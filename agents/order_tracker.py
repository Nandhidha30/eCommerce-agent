"""Agent 1: Order Tracker — real-time order status via SQLite + mock carrier API."""
from __future__ import annotations
import re
from nexus.orchestrator.models import AgentName, AgentResult, EscalationReason
from nexus.tools.database import get_order, get_customer
from nexus.tools.mock_carrier import get_carrier_tracking
from nexus.tools import audit_log
from nexus.llm import provider as llm
from nexus.llm.prompts import ORDER_RESPONSE_TEMPLATE


def _extract_order_id(message: str) -> str | None:
    """Extract order ID from message. Supports formats: ORD-001, #ORD-001, order 123."""
    patterns = [
        r'\b(ORD-\d+)\b',
        r'#(ORD-\d+)',
        r'\border[:\s#]+(\w+-?\d+)\b',
        r'\b(\d{3,})\b',  # bare number fallback
    ]
    for pat in patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            grp = m.group(1)
            if not grp.upper().startswith("ORD-"):
                grp = f"ORD-{grp}"
            return grp.upper()
    return None


def run(session_id: str, customer_id: str, message: str) -> AgentResult:
    """
    Order Tracker agent execution.
    State: RECEIVE → VALIDATE → FETCH_OMS → [FETCH_CARRIER] → FORMAT
    """
    audit_log.log_agent_execution(session_id, AgentName.ORDER_TRACKER, "start", True)

    # ── Step 1: Extract order ID ───────────────────────────────────────────────
    order_id = _extract_order_id(message)

    if not order_id:
        # No order ID found — ask for it
        return AgentResult(
            agent=AgentName.ORDER_TRACKER,
            success=True,
            response="I'd be happy to check your order status! Could you please provide your order number? It starts with **ORD-** (e.g., ORD-001).",
            data={"awaiting": "order_id"},
        )

    # ── Step 2: Database lookup ────────────────────────────────────────────────
    audit_log.log_agent_execution(session_id, AgentName.ORDER_TRACKER, "sql_order_lookup", True, order_id)
    order = get_order(order_id, customer_id if customer_id != "anonymous" else None)

    if not order:
        audit_log.log_agent_execution(session_id, AgentName.ORDER_TRACKER, "sql_order_lookup", False, f"not_found:{order_id}")
        return AgentResult(
            agent=AgentName.ORDER_TRACKER,
            success=False,
            response=f"I couldn't find order **{order_id}** associated with your account. Please double-check the order number. If you think this is an error, I can connect you with a specialist.",
            data={"order_id": order_id, "found": False},
            requires_escalation=False,
        )

    # ── Step 3: Carrier tracking (if shipped) ─────────────────────────────────
    tracking_data = None
    if order.tracking_number and order.status in ("shipped", "out_for_delivery", "delivered"):
        audit_log.log_agent_execution(session_id, AgentName.ORDER_TRACKER, "carrier_api_call", True, order.tracking_number)
        tracking_data = get_carrier_tracking(
            order.tracking_number, order.carrier or "fedex", order.status
        )

    # ── Step 4: Format response ───────────────────────────────────────────────
    data = {
        "order_id": order.order_id,
        "status": order.status,
        "item": order.item_name,
        "amount": f"${order.amount:.2f}",
        "placed_at": order.placed_at.strftime("%B %d, %Y") if order.placed_at else "N/A",
        "tracking": tracking_data,
    }

    # Build a structured response without LLM overhead for simple statuses
    status_map = {
        "processing": f"Your order **{order_id}** for *{order.item_name}* (${order.amount:.2f}) is currently being processed and will ship soon.",
        "shipped": f"Your order **{order_id}** has shipped! " + (
            f"Tracking: **{order.tracking_number}** via {(order.carrier or 'carrier').upper()}. "
            f"Expected delivery: **{tracking_data['estimated_delivery_display']}**. "
            f"Currently in: {tracking_data['current_location']}." if tracking_data else ""
        ),
        "out_for_delivery": f"Great news! Your order **{order_id}** is **out for delivery today**. "
                            + (f"It's on the delivery vehicle in {tracking_data['current_location']}." if tracking_data else ""),
        "delivered": f"Your order **{order_id}** for *{order.item_name}* was **delivered** on "
                     + (f"{tracking_data['events'][-1]['timestamp'][:10] if tracking_data else 'recently'}. "
                        "If you haven't received it, please check with neighbors or your building's front desk."),
        "cancelled": f"Your order **{order_id}** has been **cancelled**. If you didn't request this, please contact us immediately.",
    }

    response = status_map.get(
        order.status,
        f"Your order **{order_id}** status is: **{order.status.upper()}**."
    )

    audit_log.log_agent_execution(session_id, AgentName.ORDER_TRACKER, "format_response", True)

    return AgentResult(
        agent=AgentName.ORDER_TRACKER,
        success=True,
        response=response,
        data=data,
    )
