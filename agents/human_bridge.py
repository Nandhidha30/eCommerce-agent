"""Agent 4: Human Bridge — HITL escalation with full context transfer."""
from __future__ import annotations
import uuid
from datetime import datetime
from nexus.orchestrator.models import AgentName, AgentResult, EscalationReason, Message
from nexus.tools import audit_log
from nexus.llm import provider as llm
from nexus.llm.prompts import SUMMARIZER_SYSTEM


def _detect_sentiment(messages: list[Message]) -> tuple[str, float]:
    """Simple keyword-based sentiment. Returns (label, score -1 to 1)."""
    negative_words = [
        "angry", "furious", "terrible", "awful", "disgusting", "unacceptable",
        "horrible", "worst", "pathetic", "useless", "fraud", "scam", "sue",
        "never again", "ridiculous", "incompetent", "disgusted", "livid",
    ]
    frustrated_words = [
        "frustrated", "annoyed", "disappointed", "unhappy", "upset", "not happy",
        "waiting too long", "still waiting", "no response", "ignored", "broken",
    ]

    all_text = " ".join(
        m.content.lower() for m in messages if m.role == "user"
    )

    neg_count = sum(1 for w in negative_words if w in all_text)
    frus_count = sum(1 for w in frustrated_words if w in all_text)

    if neg_count >= 2 or any(w in all_text for w in ["sue", "fraud", "scam"]):
        return "distressed", -0.85
    if neg_count >= 1 or frus_count >= 2:
        return "frustrated", -0.55
    if frus_count >= 1:
        return "mildly_frustrated", -0.30
    return "neutral", 0.1


def _build_transcript(messages: list[Message]) -> str:
    lines = []
    for m in messages:
        role = "Customer" if m.role == "user" else f"AI ({m.agent or 'System'})"
        lines.append(f"[{role}]: {m.content}")
    return "\n".join(lines)


def _determine_priority(sentiment_label: str, escalation_reason: str) -> str:
    if sentiment_label == "distressed" or "fraud" in escalation_reason:
        return "P1 — URGENT"
    if sentiment_label == "frustrated" or "financial" in escalation_reason:
        return "P2 — HIGH"
    return "P3 — STANDARD"


def run(
    session_id: str,
    customer_id: str,
    message: str,
    messages: list[Message],
    escalation_reason: EscalationReason | None = None,
) -> AgentResult:
    """
    Human Bridge agent.
    Packages full session context for seamless HITL handoff.
    """
    audit_log.log_agent_execution(session_id, AgentName.HUMAN_BRIDGE, "start", True)

    # ── Step 1: Sentiment analysis ─────────────────────────────────────────────
    sentiment_label, sentiment_score = _detect_sentiment(messages)
    audit_log.log_agent_execution(
        session_id, AgentName.HUMAN_BRIDGE, "sentiment_flag",
        True, f"{sentiment_label}:{sentiment_score:.2f}"
    )

    # ── Step 2: Transcript summary (LLM or mock) ──────────────────────────────
    transcript_text = _build_transcript(messages)
    reason_str = escalation_reason.value if escalation_reason else "customer_request"

    summary_prompt = f"""Conversation transcript:
{transcript_text}

Escalation reason: {reason_str}
Sentiment: {sentiment_label} ({sentiment_score:.2f})"""

    audit_log.log_agent_execution(session_id, AgentName.HUMAN_BRIDGE, "transcript_summarizer", True)
    summary = llm.generate(SUMMARIZER_SYSTEM, summary_prompt, max_tokens=300)

    # ── Step 3: Ticket creation ───────────────────────────────────────────────
    ticket_id = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    priority = _determine_priority(sentiment_label, reason_str)

    audit_log.log_agent_execution(session_id, AgentName.HUMAN_BRIDGE, "crm_ticket_creator", True, ticket_id)
    audit_log.log_escalation(session_id, reason_str, AgentName.HUMAN_BRIDGE)

    # ── Step 4: Build handoff payload ─────────────────────────────────────────
    handoff_payload = {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "customer_id": customer_id,
        "priority": priority,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "escalation_reason": reason_str,
        "turn_count": len([m for m in messages if m.role == "user"]),
        "summary": summary,
        "transcript_length": len(messages),
        "created_at": datetime.utcnow().isoformat(),
    }

    # ── Step 5: Compose customer-facing message ───────────────────────────────
    empathy_map = {
        "distressed": "I'm truly sorry for the frustration this has caused.",
        "frustrated":  "I understand this hasn't been the experience you expected.",
        "mildly_frustrated": "I appreciate your patience.",
        "neutral": "Thank you for reaching out.",
    }
    empathy = empathy_map.get(sentiment_label, "Thank you for your patience.")

    response = (
        f"{empathy} I've escalated your case to a senior specialist who will have your full conversation history.\n\n"
        f"🎫 **Your Ticket:** `{ticket_id}`\n"
        f"⚡ **Priority:** {priority}\n"
        f"⏱️ **Expected Response:** {'5 minutes' if 'P1' in priority else '4 hours' if 'P2' in priority else 'Within today'}\n\n"
        f"You'll receive updates via email. Is there anything else I should include in the handoff notes?"
    )

    return AgentResult(
        agent=AgentName.HUMAN_BRIDGE,
        success=True,
        response=response,
        data=handoff_payload,
        requires_escalation=True,
        escalation_reason=escalation_reason or EscalationReason.CUSTOMER_REQUEST,
    )
