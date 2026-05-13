import os

def patch_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# Refund processor
patch_file('nexus/agents/refund_processor.py', [
    ('from nexus.tools import audit_log', 'from nexus.tools import audit_log\nfrom nexus.events.emitter import emitter\nimport time'),
    ('order = get_order(order_id)', 't0 = time.time()\n    emitter.emit(session_id, "tool_call", {"agent": AgentName.REFUND_PROCESSOR.value, "tool": "get_order", "args": {"order_id": order_id}})\n    order = get_order(order_id)\n    emitter.emit(session_id, "tool_result", {"agent": AgentName.REFUND_PROCESSOR.value, "tool": "get_order", "result_summary": f"Found: {bool(order)}", "duration_ms": int((time.time() - t0) * 1000)})'),
    ('charge = stripe_get_charge(order_id)', 't0 = time.time()\n    emitter.emit(session_id, "tool_call", {"agent": AgentName.REFUND_PROCESSOR.value, "tool": "stripe_get_charge", "args": {"order_id": order_id}})\n    charge = stripe_get_charge(order_id)\n    emitter.emit(session_id, "tool_result", {"agent": AgentName.REFUND_PROCESSOR.value, "tool": "stripe_get_charge", "result_summary": "Charge retrieved", "duration_ms": int((time.time() - t0) * 1000)})'),
    ('stripe_result = stripe_refund_create(', 't0 = time.time()\n    emitter.emit(session_id, "tool_call", {"agent": AgentName.REFUND_PROCESSOR.value, "tool": "stripe_refund_create", "args": {"amount": refund_amount}})\n    stripe_result = stripe_refund_create('),
    ('        idempotency_key=idempotency_key,\n    )', '        idempotency_key=idempotency_key,\n    )\n    emitter.emit(session_id, "tool_result", {"agent": AgentName.REFUND_PROCESSOR.value, "tool": "stripe_refund_create", "result_summary": "Refund created", "duration_ms": int((time.time() - t0) * 1000)})')
])

# FAQ specialist
patch_file('nexus/agents/faq_specialist.py', [
    ('from nexus.tools import audit_log', 'from nexus.tools import audit_log\nfrom nexus.events.emitter import emitter\nimport time'),
    ('results = vector_store.search(message, top_k=3)', 't0 = time.time()\n    emitter.emit(session_id, "tool_call", {"agent": AgentName.FAQ_SPECIALIST.value, "tool": "vector_store.search", "args": {"query": message}})\n    results = vector_store.search(message, top_k=3)\n    emitter.emit(session_id, "tool_result", {"agent": AgentName.FAQ_SPECIALIST.value, "tool": "vector_store.search", "result_summary": f"Retrieved {len(results)} docs", "duration_ms": int((time.time() - t0) * 1000)})')
])

# Guardrails: Financial
patch_file('nexus/guardrails/financial.py', [
    ('from nexus.tools import audit_log', 'from nexus.tools import audit_log\nfrom nexus.events.emitter import emitter'),
    ('return result', 'emitter.emit(session_id, "guardrail_violation" if result.decision in (FinancialDecision.AUTO_REJECT, FinancialDecision.HITL_MANDATORY, FinancialDecision.FRAUD_FLAG, FinancialDecision.QUEUE_HUMAN) else "guardrail_check", {"guardrail": "financial", "passed": result.decision == FinancialDecision.AUTO_APPROVE, "severity": "high" if result.requires_escalation else "low", "action": result.decision.value, "details": result.reason})\n            return result'),
    ('        result = FinancialCheckResult(\n            decision=FinancialDecision.HITL_MANDATORY,\n            reason=f"Refund of ${amount:.2f} requires senior specialist authorization.",\n            max_auto_amount=self.auto_cap,\n            requires_escalation=True,\n        )\n        audit_log.log_guardrail_trigger(\n            session_id, "financial", f"amount_above_hard_cap_{self.human_cap}", "hitl_mandatory"\n        )\n        return result', '        result = FinancialCheckResult(\n            decision=FinancialDecision.HITL_MANDATORY,\n            reason=f"Refund of ${amount:.2f} requires senior specialist authorization.",\n            max_auto_amount=self.auto_cap,\n            requires_escalation=True,\n        )\n        audit_log.log_guardrail_trigger(\n            session_id, "financial", f"amount_above_hard_cap_{self.human_cap}", "hitl_mandatory"\n        )\n        emitter.emit(session_id, "guardrail_violation", {"guardrail": "financial", "passed": False, "severity": "high", "action": result.decision.value, "details": result.reason})\n        return result')
])

# Guardrails: Loop Detector
patch_file('nexus/guardrails/loop_detector.py', [
    ('from nexus.tools import audit_log', 'from nexus.tools import audit_log\nfrom nexus.events.emitter import emitter'),
    ('return LoopDetectorResult(is_loop=False)', 'emitter.emit(session_id, "guardrail_check", {"guardrail": "loop_detector", "passed": True, "details": "No loop detected"})\n        return LoopDetectorResult(is_loop=False)'),
    ('return LoopDetectorResult(is_loop=True, reason=reason)', 'emitter.emit(session_id, "guardrail_violation", {"guardrail": "loop_detector", "passed": False, "severity": "high", "action": "escalate", "details": reason})\n        return LoopDetectorResult(is_loop=True, reason=reason)')
])

# Guardrails: Privacy
patch_file('nexus/guardrails/privacy.py', [
    ('from nexus.tools import audit_log', 'from nexus.tools import audit_log\nfrom nexus.events.emitter import emitter'),
    ('return redacted_text, current_map', 'if found_new:\n        emitter.emit(session_id, "guardrail_violation", {"guardrail": "privacy", "passed": False, "severity": "medium", "action": "redacted_pii", "details": f"Redacted {len(found_new)} entities"})\n    else:\n        emitter.emit(session_id, "guardrail_check", {"guardrail": "privacy", "passed": True, "details": "No PII found"})\n    return redacted_text, current_map')
])
print('Patched successfully!')
