"""FastAPI application — REST + WebSocket endpoints for NEXUS."""
from __future__ import annotations
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from nexus.config import settings
from nexus.tools.database import init_db, get_metrics_summary
from nexus.tools.vector_store import vector_store
from nexus.guardrails.privacy import session_store
from nexus.orchestrator.models import (
    SessionContext, ChatRequest, ChatResponse,
    HealthResponse, MetricsResponse, AgentName,
)
from nexus.orchestrator.state_machine import process_message
from nexus.llm.provider import get_mode


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB + vector store. Shutdown: cleanup."""
    print("[NEXUS] Initializing database...")
    init_db()
    print("[NEXUS] Warming up vector store...")
    vector_store.ensure_ready()
    print(f"[NEXUS] LLM mode: {get_mode()}")
    print("[NEXUS] 🚀 System ready!")
    yield
    print("[NEXUS] Shutting down...")


app = FastAPI(
    title="NEXUS — Agentic AI Customer Resolution System",
    description="Production-grade multi-agent e-commerce support system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST: Health ───────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_mode=get_mode(),
        db_connected=True,
        vector_store_ready=vector_store.ready,
    )


# ── REST: Chat ────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest):
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())

    if session_store.exists(session_id):
        session_data = session_store.get(session_id)
        session = SessionContext.model_validate(session_data)
    else:
        session = SessionContext(
            session_id=session_id,
            customer_id=request.customer_id,
        )

    # Process through state machine
    updated_session, payload = process_message(session, request.message)

    # Persist session
    session_store.set(session_id, updated_session.model_dump())

    return ChatResponse(
        session_id=session_id,
        message=payload["response"],
        agent_used=payload["agent_used"],
        confidence=payload["confidence"],
        resolution_time_ms=payload["resolution_time_ms"],
        escalated=payload["escalated"],
        turn=payload["turn"],
        citations=payload["citations"],
        data=payload["data"],
    )


# ── REST: Metrics ──────────────────────────────────────────────────────────────
@app.get("/metrics", response_model=MetricsResponse, tags=["monitoring"])
async def metrics():
    data = get_metrics_summary()
    return MetricsResponse(**data)


# ── REST: Session Delete (GDPR) ────────────────────────────────────────────────
@app.delete("/session/{session_id}", tags=["privacy"])
async def delete_session(session_id: str):
    deleted = session_store.delete(session_id)
    return {"deleted": deleted, "session_id": session_id}


# ── REST: List sample orders (for demo) ───────────────────────────────────────
@app.get("/demo/orders", tags=["demo"])
async def list_demo_orders():
    from nexus.tools.database import get_session
    from nexus.tools.database import Order
    with get_session() as s:
        orders = s.query(Order).limit(10).all()
        return [
            {
                "order_id": o.order_id,
                "status": o.status,
                "item": o.item_name,
                "amount": o.amount,
                "customer_id": o.customer_id,
            }
            for o in orders
        ]


# ── WebSocket: Chat ────────────────────────────────────────────────────────────
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    session = SessionContext(session_id=session_id)

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            session.customer_id = data.get("customer_id", "anonymous")

            updated_session, payload = process_message(session, message)
            session = updated_session
            session_store.set(session_id, session.model_dump())

            await websocket.send_json({
                "session_id": session_id,
                "message": payload["response"],
                "agent_used": payload["agent_used"].value,
                "intent": payload["intent"],
                "confidence": payload["confidence"],
                "resolution_time_ms": payload["resolution_time_ms"],
                "escalated": payload["escalated"],
                "turn": payload["turn"],
                "citations": payload["citations"],
            })
    except WebSocketDisconnect:
        session_store.delete(session_id)
