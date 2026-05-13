"""Agent 2: Refund Processor — deterministic policy engine + mock Stripe."""
from __future__ import annotations
import re
import uuid
from datetime import datetime
from nexus.orchestrator.models import AgentName, AgentResult, EscalationReason
from nexus.tools.database import get_order, create_refund_record
from nexus.tools.mock_stripe import stripe_refund_create, stripe_get_charge
from nexus.guardrails.financial import financial_guardrail, FinancialDecision
from nexus.tools import audit_log


def _extract_order_id(message: str) -> str | None:
    patterns = [r'\b(ORD-\d+)\b', r'#(ORD-\d+)', r'\border[:\s#]+(\w+-?\d+)\b']
    for pat in patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            grp = m.group(1)
            return grp.upper() if grp.upper().startswith("ORD-") else f"ORD-{grp.upper()}"
    return None


def _extract_amount(message: str, fallback: float = 0.0) -> float:
    """Try to extract a dollar amount from the message."""
    m = re.search(r'\$\s*(\d+(?:\.\d{2})?)', message)
    if m:
        return float(m.group(1))
    return fallback


def _days_since(dt: datetime) -> int:
    if not dt:
        return 0
    return (datetime.utcnow() - dt).days


def run(session_id: str, customer_id: str, message: str) -> AgentResult:
    """
    Refund Processor agent.
    State: EXTRACT → POLICY_CHECK → [STRIPE_CALL | QUEUE | ESCALATE] → RESPOND
    """
    audit_log.log_agent_execution(session_id, AgentName.REFUND_PROCESSOR, "start", True)

    # ── Step 1: Extract order ID ───────────────────────────────────────────────
    order_id = _extract_order_id(message)

    if not order_id:
        return AgentResult(
            agent=AgentName.REFUND_PROCESSOR,
            success=True,
            response="I can help you with a refund! To get started, could you share your **order number** (e.g., ORD-001)? Also, what's the reason for your return?",
            data={"awaiting": "order_id"},
        )

    # ── Step 2: Order lookup ───────────────────────────────────────────────────
    audit_log.log_agent_execution(session_id, AgentName.REFUND_PROCESSOR, "sql_order_lookup", True, order_id)
    order = get_order(order_id)

    if not order:
        return AgentResult(
            agent=AgentName.REFUND_PROCESSOR,
            success=False,
            response=f"I couldn't find order **{order_id}**. Please verify the order number. If you need further help, I can escalate to a specialist.",
            data={"order_id": order_id, "found": False},
        )

    # ── Step 3: Financial guardrail check ─────────────────────────────────────
    days_since = _days_since(order.placed_at)
    requested_amount = _extract_amount(message, fallback=order.amount)
    # Cap requested amount at order amount
    refund_amount = min(requested_amount, order.amount)

    guardrail_result = financial_guardrail.check(
        session_id=session_id,
        customer_id=customer_id,
        amount=refund_amount,
        item_category=order.item_category or "general",
        days_since_purchase=days_since,
        fraud_score=0.0,  # Plug in real fraud service here
    )

    audit_log.log_agent_execution(
        session_id, AgentName.REFUND_PROCESSOR, "policy_engine_check",
        True, f"decision={guardrail_result.decision.value}"
    )

    # ── Step 4: Route by policy decision ──────────────────────────────────────

    if guardrail_result.decision == FinancialDecision.AUTO_REJECT:
        return AgentResult(
            agent=AgentName.REFUND_PROCESSOR,
            success=True,
            response=f"I'm sorry, but I'm unable to process a refund for this order. **Reason:** {guardrail_result.reason}\n\nIf you believe this is an error or have special circumstances, I can escalate your case to a senior specialist.",
            data={"order_id": order_id, "decision": "rejected", "reason": guardrail_result.reason},
            requires_escalation=False,
        )

    if guardrail_result.decision in (FinancialDecision.HITL_MANDATORY, FinancialDecision.FRAUD_FLAG, FinancialDecision.QUEUE_HUMAN):
        refund_id = f"RFD-{uuid.uuid4().hex[:8].upper()}"
        create_refund_record(
            refund_id=refund_id,
            customer_id=customer_id,
            order_id=order_id,
            amount=refund_amount,
            reason=message[:200],
            status="escalated",
        )
        audit_log.log_escalation(session_id, guardrail_result.decision.value, AgentName.REFUND_PROCESSOR)

        return AgentResult(
            agent=AgentName.REFUND_PROCESSOR,
            success=True,
            response=f"I've created a priority refund case **#{refund_id}** for **${refund_amount:.2f}** on order {order_id}. {guardrail_result.reason}\n\nA specialist will review and contact you within 4 hours. You'll receive a confirmation email shortly.",
            data={"order_id": order_id, "refund_id": refund_id, "amount": refund_amount, "decision": "escalated"},
            requires_escalation=True,
            escalation_reason=EscalationReason.FINANCIAL_LIMIT,
        )

    # ── Step 5: AUTO_APPROVE — call mock Stripe ────────────────────────────────
    charge = stripe_get_charge(order_id)
    idempotency_key = f"{session_id}-{order_id}-refund"

    audit_log.log_agent_execution(session_id, AgentName.REFUND_PROCESSOR, "stripe_refund_initiate", True, f"amount={refund_amount}")
    stripe_result = stripe_refund_create(
        charge_id=charge["id"],
        amount=refund_amount,
        reason="customer_request",
        idempotency_key=idempotency_key,
    )

    refund_id = stripe_result["refund"]["id"]
    create_refund_record(
        refund_id=refund_id,
        customer_id=customer_id,
        order_id=order_id,
        amount=refund_amount,
        reason=message[:200],
        status="approved",
        stripe_id=refund_id,
    )

    return AgentResult(
        agent=AgentName.REFUND_PROCESSOR,
        success=True,
        response=f"✅ **Refund Approved!** Your refund of **${refund_amount:.2f}** for order **{order_id}** has been processed.\n\n"
                 f"- **Refund ID:** `{refund_id}`\n"
                 f"- **Timeline:** 3–5 business days to your original payment method\n"
                 f"- **Confirmation:** A receipt will be sent to your email\n\n"
                 f"Is there anything else I can help you with?",
        data={"order_id": order_id, "refund_id": refund_id, "amount": refund_amount, "stripe_result": stripe_result},
    )
