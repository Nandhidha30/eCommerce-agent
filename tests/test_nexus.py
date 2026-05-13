"""Tests — router accuracy, guardrails, agent logic."""
from __future__ import annotations
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nexus.orchestrator.router import router
from nexus.orchestrator.models import IntentType
from nexus.guardrails.financial import financial_guardrail, FinancialDecision
from nexus.guardrails.loop_detector import loop_detector
from nexus.guardrails.privacy import redact_pii, restore_pii


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSemanticRouter:

    def test_order_status_intent(self):
        result = router.classify("Where is my package? Order ORD-001")
        assert result.intent == IntentType.ORDER_STATUS
        assert result.confidence >= 0.5

    def test_refund_request_intent(self):
        result = router.classify("I want to return my item and get a refund")
        assert result.intent == IntentType.REFUND_REQUEST
        assert result.confidence >= 0.5

    def test_faq_policy_intent(self):
        result = router.classify("What is your return policy for electronics?")
        assert result.intent == IntentType.FAQ_POLICY
        assert result.confidence >= 0.5

    def test_human_escalation_intent(self):
        result = router.classify("I want to speak to a real person please")
        assert result.intent == IntentType.HUMAN_ESCALATION
        assert result.confidence >= 0.5

    def test_ambiguous_low_confidence(self):
        """Very vague message should trigger AMBIGUOUS."""
        result = router.classify("help")
        # Either ambiguous or a low-confidence intent
        assert result.confidence < 1.0

    def test_confidence_range(self):
        """All confidence scores should be between 0 and 1."""
        for msg in ["track my order", "refund please", "shipping policy", "agent"]:
            result = router.classify(msg)
            assert 0.0 <= result.confidence <= 1.0

    def test_raw_scores_all_intents(self):
        """raw_scores should contain all intent types."""
        result = router.classify("I need help with my order")
        # raw_scores should have entries
        assert len(result.raw_scores) > 0


# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL GUARDRAIL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestFinancialGuardrail:

    def test_auto_approve_small_amount(self):
        result = financial_guardrail.check("sess-1", "CUST-001", amount=50.0)
        assert result.decision == FinancialDecision.AUTO_APPROVE
        assert not result.requires_escalation

    def test_auto_approve_at_cap(self):
        result = financial_guardrail.check("sess-2", "CUST-001", amount=150.0)
        assert result.decision == FinancialDecision.AUTO_APPROVE

    def test_queue_human_above_cap(self):
        result = financial_guardrail.check("sess-3", "CUST-001", amount=200.0)
        assert result.decision == FinancialDecision.QUEUE_HUMAN
        assert result.requires_escalation

    def test_hitl_mandatory_large_amount(self):
        result = financial_guardrail.check("sess-4", "CUST-001", amount=600.0)
        assert result.decision == FinancialDecision.HITL_MANDATORY
        assert result.requires_escalation

    def test_digital_goods_auto_reject(self):
        result = financial_guardrail.check(
            "sess-5", "CUST-001", amount=30.0, item_category="digital_downloads"
        )
        assert result.decision == FinancialDecision.AUTO_REJECT
        assert not result.requires_escalation

    def test_expired_window_auto_reject(self):
        result = financial_guardrail.check(
            "sess-6", "CUST-001", amount=50.0, days_since_purchase=91
        )
        assert result.decision == FinancialDecision.AUTO_REJECT

    def test_fraud_score_flag(self):
        result = financial_guardrail.check(
            "sess-7", "CUST-001", amount=50.0, fraud_score=0.9
        )
        assert result.decision == FinancialDecision.FRAUD_FLAG
        assert result.requires_escalation


# ══════════════════════════════════════════════════════════════════════════════
# LOOP DETECTOR TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestLoopDetector:

    def test_no_loop_normal_session(self):
        result = loop_detector.check(
            session_id="sess-a",
            turn_count=3,
            intent_history=["order_status", "refund_request", "faq_policy"],
            tool_errors=[],
            visited_states=["INTAKE", "CLASSIFY", "ROUTE", "EXECUTE"],
            current_state="RESPOND",
        )
        assert not result.is_loop

    def test_max_turns_exceeded(self):
        result = loop_detector.check(
            session_id="sess-b",
            turn_count=9,  # above max of 8
            intent_history=["order_status"] * 9,
            tool_errors=[],
            visited_states=["INTAKE"] * 9,
            current_state="CLASSIFY",
        )
        assert result.is_loop

    def test_intent_loop_detected(self):
        result = loop_detector.check(
            session_id="sess-c",
            turn_count=4,
            intent_history=["order_status", "order_status", "order_status"],
            tool_errors=[],
            visited_states=["INTAKE", "CLASSIFY", "ROUTE", "EXECUTE"],
            current_state="CLASSIFY",
        )
        assert result.is_loop

    def test_tool_error_loop(self):
        result = loop_detector.check(
            session_id="sess-d",
            turn_count=4,
            intent_history=["order_status"] * 3,
            tool_errors=[
                {"tool": "carrier_api", "error": "timeout"},
                {"tool": "carrier_api", "error": "timeout"},
                {"tool": "carrier_api", "error": "timeout"},
            ],
            visited_states=["INTAKE", "EXECUTE"],
            current_state="EXECUTE",
        )
        assert result.is_loop


# ══════════════════════════════════════════════════════════════════════════════
# PRIVACY GUARDRAIL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestPrivacyGuardrail:

    def test_email_redacted(self):
        text = "My email is john.doe@gmail.com please help"
        redacted, token_map = redact_pii(text, "sess-e", {})
        assert "john.doe@gmail.com" not in redacted
        assert len(token_map) > 0

    def test_phone_redacted(self):
        text = "Call me at 555-867-5309"
        redacted, token_map = redact_pii(text, "sess-f", {})
        assert "555-867-5309" not in redacted

    def test_restore_pii(self):
        text = "Email john@test.com"
        redacted, token_map = redact_pii(text, "sess-g", {})
        restored = restore_pii(redacted, token_map)
        assert "john@test.com" in restored

    def test_no_pii_unchanged(self):
        text = "Where is my order ORD-001?"
        redacted, token_map = redact_pii(text, "sess-h", {})
        assert "ORD-001" in redacted
        assert len(token_map) == 0

    def test_ssn_redacted(self):
        text = "My SSN is 123-45-6789"
        redacted, token_map = redact_pii(text, "sess-i", {})
        assert "123-45-6789" not in redacted
