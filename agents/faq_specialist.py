"""Agent 3: FAQ Specialist — hybrid FAISS retrieval + OpenAI/mock generation."""
from __future__ import annotations
from nexus.orchestrator.models import AgentName, AgentResult
from nexus.tools.vector_store import vector_store
from nexus.tools import audit_log
from nexus.llm import provider as llm
from nexus.llm.prompts import FAQ_SYSTEM, FAQ_USER_TEMPLATE

GROUNDEDNESS_THRESHOLD = 0.35  # Minimum FAISS cosine score to trust retrieval


def _build_context(docs: list[dict]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(
            f"[Doc {i}] Source: {doc['source']}\n{doc['text']}"
        )
    return "\n\n".join(parts)


def _extract_citations(docs: list[dict]) -> list[str]:
    return [f"{doc['source']} (relevance: {doc['score']:.2f})" for doc in docs]


def _passes_groundedness(docs: list[dict]) -> bool:
    """Check if top result meets minimum relevance threshold."""
    if not docs:
        return False
    return docs[0]["score"] >= GROUNDEDNESS_THRESHOLD


def run(session_id: str, customer_id: str, message: str) -> AgentResult:
    """
    FAQ Specialist agent.
    Pipeline: QUERY → FAISS_SEARCH → GROUNDEDNESS_CHECK → LLM_GENERATE → RESPOND
    """
    audit_log.log_agent_execution(session_id, AgentName.FAQ_SPECIALIST, "start", True)

    # ── Step 1: Vector search ─────────────────────────────────────────────────
    audit_log.log_agent_execution(session_id, AgentName.FAQ_SPECIALIST, "vector_search", True, message[:80])

    try:
        results = vector_store.search(message, top_k=4)
    except Exception as e:
        audit_log.log_agent_execution(session_id, AgentName.FAQ_SPECIALIST, "vector_search", False, str(e))
        results = []

    # ── Step 2: Groundedness check ────────────────────────────────────────────
    if not _passes_groundedness(results):
        audit_log.log_agent_execution(
            session_id, AgentName.FAQ_SPECIALIST, "groundedness_check", False,
            f"top_score={results[0]['score']:.3f}" if results else "no_results"
        )
        return AgentResult(
            agent=AgentName.FAQ_SPECIALIST,
            success=True,
            response="I found partial information but want to make sure I give you an accurate answer. Let me connect you with a specialist who can give you the definitive answer.",
            data={"groundedness": "below_threshold"},
            requires_escalation=True,
            escalation_reason=None,
        )

    audit_log.log_agent_execution(
        session_id, AgentName.FAQ_SPECIALIST, "groundedness_check", True,
        f"top_score={results[0]['score']:.3f}"
    )

    # ── Step 3: Build context and generate response ───────────────────────────
    context = _build_context(results[:3])
    citations = _extract_citations(results[:3])

    user_prompt = FAQ_USER_TEMPLATE.format(context=context, question=message)

    audit_log.log_agent_execution(session_id, AgentName.FAQ_SPECIALIST, "llm_generate", True)
    answer = llm.generate(FAQ_SYSTEM, user_prompt, max_tokens=350)

    return AgentResult(
        agent=AgentName.FAQ_SPECIALIST,
        success=True,
        response=answer,
        data={
            "retrieved_docs": len(results),
            "top_score": round(results[0]["score"], 3),
            "sources": [r["source"] for r in results[:3]],
        },
        citations=citations,
    )
