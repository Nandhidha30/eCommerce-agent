# Product Requirements Document (PRD)
## Project: NEXUS — Agentic AI Customer Resolution System
### Version: 1.0.0 | Classification: Internal — Engineering & Product
### Date: May 2026 | Status: APPROVED FOR DEVELOPMENT


## 7.1 Live Observability
The system includes a real-time event bus and a Next.js 14 Cockpit UI.
- **Event Emitter**: Emits events (node_enter, node_exit, intent_classified, tool_call, tool_result, guardrail_check, guardrail_violation) directly from the LangGraph execution context via asyncio.Queue.
- **Cockpit UI**: Provides live reasoning traces, agent flow canvas topology visualization, and SSE streaming.

---

## 1. Introduction

### 1.1 Executive Summary

NEXUS is a production-grade, multi-agent AI orchestration system designed to resolve the **Response Time Crisis** afflicting a global e-commerce platform processing **10,000+ customer queries daily**. The system replaces a legacy ticket-triage model — averaging 6-hour resolution windows — with a deterministic, state-machine-driven agentic pipeline targeting **sub-3-minute Automated Resolution Time (ART)** for 85%+ of queries.

NEXUS is **not a chatbot**. It is a distributed agentic workflow system with:
- A semantic routing orchestrator
- Four specialized sub-agents (Order Tracker, Refund Processor, FAQ Specialist, Human Bridge)
- PII-redaction middleware
- Financial guardrails with policy enforcement
- Human-in-the-Loop (HITL) escalation pathways
- Real-time session isolation and memory management

### 1.2 Problem Context

| Metric | Current State | Target State |
|---|---|---|
| Average Resolution Time (ART) | 6 hours | < 3 minutes (automated) |
| Daily Query Volume | 10,000+ | 10,000+ (elastic scale) |
| Automation Rate | ~12% (basic IVR) | ≥ 85% |
| Human Agent Escalation | 88% of tickets | ≤ 15% of tickets |
| CSAT Score | 2.8 / 5 | ≥ 4.2 / 5 |
| Agent Burnout Index | High (repetitive triaging) | Low (complex cases only) |

### 1.3 Scope

**In Scope:**
- Order status queries (real-time API integration)
- Refund and return processing (policy-engine enforcement)
- FAQ and policy resolution (RAG-based knowledge retrieval)
- Escalation to human agents with full context transfer

**Out of Scope:**
- New product recommendations
- Loyalty program management
- B2B/enterprise account billing
- Vendor-side dispute resolution

---

## 2. Business Case & Human Cost Analysis

### 2.1 Customer Impact (LTV & Churn Analysis)

A 6-hour delay in resolution is not just an inconvenience — it is a **revenue destruction event**:

- **Churn multiplier:** Customers who experience a resolution delay > 4 hours are **3.2× more likely to churn** within 90 days (industry benchmark, Zendesk 2024).
- **LTV erosion:** Average e-commerce LTV = $480. A 10% churn increase on 10,000 daily contacts = **$4.8M annual LTV loss**.
- **Negative word-of-mouth:** NPS detractors (score 0–6) generate an average of **2.3 negative referrals**, amplifying brand damage geometrically.
- **Cart abandonment correlation:** 34% of users who contact support mid-session and receive no immediate response abandon their cart permanently.

### 2.2 Human Agent Impact (Burnout & Efficiency)

The hidden cost of the current model is **agent cognitive load**:

- **Repetitive triaging:** ~73% of tickets are Tier-1 (order status, simple FAQ) — tasks that require zero judgment. Agents spend 4.5 hours/day on these.
- **Context switching:** Agents handle 45+ tickets per shift across 6 categories. Frequent switching reduces decision accuracy by 28% (APA Cognitive Load Study).
- **Escalation fatigue:** When everything escalates, agents lose prioritization ability. Critical cases (fraud, safety) get delayed alongside trivial ones.
- **Attrition cost:** Support agent attrition runs 35–45% annually at high-volume centers. Replacing one agent costs ~$4,200 in recruitment and retraining.

> **NEXUS Outcome:** By automating 85% of Tier-1 queries, agents are redeployed exclusively to Tier-2/3 cases (fraud, complex disputes, emotional support). This reduces cognitive load, increases job satisfaction, and cuts attrition.

---

## 3. User Stories

### 3.1 End Customer Stories

| ID | Role | Goal | Acceptance Criteria |
|---|---|---|---|
| US-001 | Customer | Know where my order is in real-time | System returns order status + ETA within 8 seconds, no human needed |
| US-002 | Customer | Initiate a refund without calling support | Refund processed or queued within 2 minutes if within policy |
| US-003 | Customer | Get answers to return/shipping policy | Accurate answer with source citation from knowledge base |
| US-004 | Customer | Reach a human when I'm frustrated | Seamless handoff with full conversation context pre-loaded for agent |
| US-005 | Customer | My personal data stays private | No PII echoed back in responses; session data purged on close |

### 3.2 Human Agent Stories

| ID | Role | Goal | Acceptance Criteria |
|---|---|---|---|
| US-006 | Support Agent | Receive escalations with full context | HITL handoff includes transcript, intent classification, PII-redacted summary |
| US-007 | Support Agent | Only handle cases that require judgment | ≤ 15% of total tickets reach human queue |
| US-008 | Support Manager | Monitor automation performance | Real-time dashboard with KPI visibility |

### 3.3 Engineering/DevOps Stories

| ID | Role | Goal | Acceptance Criteria |
|---|---|---|---|
| US-009 | DevOps Engineer | System scales to 10,000+ daily queries | Horizontal scaling via Kubernetes; no degradation at peak |
| US-010 | ML Engineer | Detect and prevent infinite agent loops | Max-turn circuit breaker triggers at turn 8; auto-escalates |
| US-011 | Security Engineer | Audit all agent decisions | Immutable audit log for every tool call and state transition |

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER INTERFACE LAYER                     │
│         (Web Chat / Mobile SDK / WhatsApp / Email API)         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PII REDACTION MIDDLEWARE                      │
│   (Presidio / Custom NER — strips emails, phones, card #s)     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              SESSION MANAGER (Redis — Isolated TTL)             │
│        Session ID → Encrypted Context → Auto-Purge 30min       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               ORCHESTRATOR — SEMANTIC ROUTER                    │
│    (Embedding-based Intent Classification + Confidence Gate)   │
│                                                                 │
│   Intent → OrderTracker | RefundProcessor | FAQSpecialist |    │
│            HumanBridge | AmbiguousHandler                      │
└──────┬──────────┬──────────────┬──────────────┬────────────────┘
       │          │              │              │
       ▼          ▼              ▼              ▼
  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────────┐
  │  Order  │ │ Refund  │ │   FAQ    │ │ Human Bridge  │
  │ Tracker │ │Processor│ │Specialist│ │   (HITL)      │
  └────┬────┘ └────┬────┘ └────┬─────┘ └───────┬───────┘
       │           │           │               │
       ▼           ▼           ▼               ▼
  [OMS API]  [Stripe API] [Vector DB]   [Agent Console]
  [SQL DB]   [Policy     [Reranker]    [CRM Push]
             Engine]     [LLM Gen]     [Slack Alert]
                         
└─────────────────────────────────────────────────────────────────┘
│              GUARDRAIL LAYER (Cross-cutting)                    │
│   Financial Cap | PII Isolation | Loop Detector | Audit Log    │
└─────────────────────────────────────────────────────────────────┘
│                MONITORING & OBSERVABILITY                       │
│         (Langfuse / Prometheus / Grafana / PagerDuty)          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 State Machine Design (Orchestrator)

The orchestrator operates as a **deterministic finite-state machine** (not a free-form LLM chat loop):

```
States:
  INTAKE → CLASSIFY → ROUTE → EXECUTE → VALIDATE → RESPOND → CLOSE
                         ↓ (if confidence < 0.72)
                    CLARIFY → RECLASSIFY
                         ↓ (if max_turns exceeded OR loop detected)
                    ESCALATE → HITL_HANDOFF
```

**State Transitions:**

| From | To | Condition |
|---|---|---|
| INTAKE | CLASSIFY | Message received and PII-redacted |
| CLASSIFY | ROUTE | Confidence ≥ 0.72 |
| CLASSIFY | CLARIFY | Confidence < 0.72 |
| ROUTE | EXECUTE | Agent selected |
| EXECUTE | VALIDATE | Tool call returned result |
| VALIDATE | RESPOND | Result passes guardrail checks |
| VALIDATE | ESCALATE | Guardrail violation detected |
| EXECUTE | ESCALATE | Tool error after 3 retries |
| RESPOND | CLOSE | Customer confirms resolution |
| RESPOND | RECLASSIFY | Customer signals unsatisfied |
| Any | ESCALATE | Turn count > 8 OR loop signature detected |

### 4.3 Agent Specifications

#### Agent 1: Order Tracker (API-Heavy)

**Responsibility:** Retrieve real-time order status, delivery ETAs, carrier tracking

**Tools:**
- `sql_order_lookup(order_id, customer_id)` — PostgreSQL: orders, shipments tables
- `carrier_api_call(tracking_number, carrier_code)` — FedEx/UPS/USPS REST APIs
- `oms_status_resolver(order_id)` — Internal OMS microservice
- `geo_eta_calculator(warehouse_zip, delivery_zip)` — Routing service

**State Logic:**
```
RECEIVE(order_id) → VALIDATE_OWNERSHIP → FETCH_OMS → 
  IF tracking_exists → FETCH_CARRIER → FORMAT_RESPONSE
  IF no_tracking    → CHECK_FULFILLMENT_ETA → FORMAT_RESPONSE
  IF order_not_found → ESCALATE(fraud_check=True)
```

**Output:** Structured JSON → formatted natural language response

---

#### Agent 2: Refund Processor (Policy-Heavy)

**Responsibility:** Evaluate refund eligibility, initiate approved refunds, reject and explain denied requests

**Tools:**
- `policy_engine_check(order_id, reason_code, days_since_purchase)` — Rule-based engine (not LLM)
- `stripe_refund_initiate(charge_id, amount, idempotency_key)` — Stripe API
- `refund_cap_validator(customer_id, refund_amount, rolling_window_days=30)` — Fraud guardrail
- `crm_case_logger(session_id, outcome, amount)` — Salesforce/Zendesk API
- `email_confirmation_dispatch(customer_id, refund_id)` — Transactional email service

**Policy Engine Rules (Deterministic — Not LLM):**
```yaml
refund_policy:
  standard_window_days: 30
  extended_window_days: 60  # Premium members
  max_auto_approve_amount: 150.00
  require_human_approval_above: 500.00
  auto_reject_conditions:
    - days_since_purchase > 90
    - item_category: "digital_downloads"
    - fraud_score > 0.75
  require_evidence_conditions:
    - days_since_purchase > 30 AND days_since_purchase <= 60
    - refund_count_30d > 3
```

**Idempotency:** Every Stripe call uses a `UUID + session_id` idempotency key to prevent duplicate refunds.

---

#### Agent 3: FAQ Specialist (RAG-Heavy)

**Responsibility:** Answer policy questions, shipping information, product specifications using knowledge base

**Tools:**
- `vector_search(query_embedding, top_k=5, filters={"doc_type": "policy"})` — Pinecone/Weaviate
- `bm25_keyword_search(query_text)` — Elasticsearch fallback for sparse retrieval
- `reranker(query, candidate_chunks)` — Cross-encoder reranking (Cohere Rerank / BGE)
- `llm_answer_generator(context_chunks, query, system_prompt)` — Gemini Pro / GPT-4o
- `citation_extractor(source_docs)` — Returns source document + page number for transparency

**RAG Pipeline:**
```
QUERY → EMBED → HYBRID_SEARCH(vector + BM25) → RERANK → 
CONTEXT_WINDOW_PACK → LLM_GENERATE(with_citations) → 
HALLUCINATION_CHECK(groundedness_score ≥ 0.85) → RESPOND
```

**Hallucination Guard:** If groundedness score < 0.85, answer is suppressed and system responds: *"I found partial information but want to be certain — let me connect you with a specialist."*

---

#### Agent 4: Human Bridge (Context-Transfer Heavy)

**Responsibility:** Graceful escalation to human agents with zero context loss

**Tools:**
- `transcript_summarizer(session_id)` — Condenses conversation to structured summary
- `pii_safe_export(session_id)` — Exports transcript with PII re-introduced from vault (for agent eyes only)
- `crm_ticket_creator(customer_id, priority, summary, transcript)` — Creates prioritized ticket
- `agent_routing_engine(ticket_priority, agent_skills, queue_depth)` — Skills-based routing
- `slack_alert(agent_channel, ticket_id, urgency)` — Real-time agent notification
- `sentiment_flag(session_transcript)` — Flags emotionally distressed customers for priority routing

**HITL Handoff Payload:**
```json
{
  "ticket_id": "TKT-20260513-9821",
  "customer_id": "CUST-[REDACTED]",
  "session_duration_seconds": 187,
  "intent_detected": "refund_denied_dispute",
  "ai_resolution_attempted": true,
  "failure_reason": "refund_policy_boundary_case",
  "sentiment_score": -0.72,
  "priority": "HIGH",
  "conversation_summary": "Customer purchased item on 04/15, received damaged, photo evidence provided. Refund denied by auto-policy due to 31-day window. Customer disputes the date calculation.",
  "recommended_action": "Review photos, authorize exception refund up to $89.99",
  "full_transcript_url": "https://vault.nexus.internal/sessions/[SESSION_ID]"
}
```

---

## 5. Functional Requirements

### 5.1 Orchestrator Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Semantic router must classify intent with ≥ 95% accuracy on test set | P0 |
| FR-002 | Classification latency must be < 200ms (embedding inference) | P0 |
| FR-003 | State machine must log every transition with timestamp and payload | P0 |
| FR-004 | Ambiguous intents (confidence < 0.72) must trigger clarification flow | P1 |
| FR-005 | System must support multi-intent detection (e.g., "where's my order AND I want a refund") | P1 |

### 5.2 Safety Guardrails (Non-Negotiable P0)

#### Guardrail 1 — Financial: Refund Caps

| Rule | Implementation |
|---|---|
| Auto-approve cap | Refunds ≤ $150 auto-processed without human review |
| Human-approval gate | Refunds $150–$500 require async agent approval within 4 hours |
| Hard block | Refunds > $500 blocked from AI; immediate HITL |
| Rolling window fraud | If customer_id has > 3 refunds in 30 days, flag and escalate |
| Idempotency | Every Stripe call uses unique idempotency key; logged to DB |
| Audit trail | Every refund decision (approved/denied) logged with policy rule ID |

#### Guardrail 2 — Privacy: Session-Based Memory Isolation

| Rule | Implementation |
|---|---|
| PII redaction at ingress | Microsoft Presidio + custom NER strips emails, phones, card numbers, SSNs before any LLM call |
| Session-scoped memory | Each session has isolated Redis namespace; no cross-session leakage |
| PII vault | Original PII stored encrypted (AES-256) in separate vault; referenced by token |
| No PII in LLM context | LLM never receives raw PII; only tokenized references |
| Session TTL | Memory auto-purges after 30 minutes of inactivity |
| Agent-only PII access | Full PII only decrypted and shown to human agents in secure console |
| GDPR compliance | Customer can request session deletion via API endpoint |

#### Guardrail 3 — Logic: Infinite Loop Detection & Max-Turn Limits

| Rule | Implementation |
|---|---|
| Max-turn hard limit | Conversations exceeding 8 agent turns auto-escalate to HITL |
| Loop signature detection | If same intent is re-classified 3× in a row, loop is flagged |
| Tool retry cap | Each tool call retried max 3× with exponential backoff; fail → escalate |
| State transition validation | Invalid state transitions raise exception; logged + escalated |
| Circular reference guard | Graph traversal tracks visited nodes; re-entry blocked |
| Watchdog timer | If agent execution exceeds 45 seconds, async timeout and escalate |

### 5.3 Performance Requirements

| Requirement | Target | Measurement |
|---|---|---|
| End-to-end response time (P50) | < 3 seconds | Latency percentiles, Prometheus |
| End-to-end response time (P95) | < 8 seconds | Latency percentiles, Prometheus |
| System availability | 99.9% uptime | Uptime monitoring, PagerDuty |
| Concurrent session handling | 500 simultaneous sessions | Load testing, k6 |
| Daily throughput | 10,000+ queries | Horizontal scaling, Kubernetes HPA |

---

## 6. Security Requirements

### 6.1 Authentication & Authorization

- All external API calls use OAuth 2.0 / API key rotation (90-day cycle)
- Agent-to-agent communication via mTLS within Kubernetes cluster
- Human agent console requires MFA + role-based access control (RBAC)
- Audit logs are **immutable** (write-once S3 / append-only DB table)

### 6.2 Data Security

- All data at rest: AES-256 encryption
- All data in transit: TLS 1.3
- LLM API calls: requests routed through private VPC endpoints (no public internet for PII-adjacent data)
- PII vault: HSM-backed key management (AWS KMS / HashiCorp Vault)

### 6.3 Compliance

| Standard | Compliance Action |
|---|---|
| GDPR | Session purge API, right-to-erasure workflow |
| CCPA | Data inventory tagging for California residents |
| PCI-DSS | No card data stored; Stripe handles payment tokenization |
| SOC 2 Type II | Audit log pipeline, access controls, incident response plan |

---

## 7. Monitoring & KPIs

### KPI 1 — Automation Accuracy Rate (AAR)
**Definition:** % of AI-resolved sessions where resolution was confirmed correct by customer
**Target:** ≥ 85% Routing Accuracy

### KPI 2 — Average Resolution Time (ART)
**Definition:** Time from first customer message to confirmed resolution
**Target:** ≤ 3s P95

### KPI 3 — Escalation Rate
**Definition:** % of sessions requiring human intervention
**Target:** ≤ 15%

### KPI 4 — Guardrail Trigger Rate (GTR)
**Definition:** % of sessions where a safety guardrail fired
**Target:** < 2%

### KPI 5 — First-Contact Resolution Rate
**Definition:** % of sessions resolved without a follow-up required
**Target:** ≥ 70%

### KPI 6 — Cost per Resolution
**Definition:** Average LLM inference cost per session
**Target:** < $0.02


### KPI 5 — First-Contact Resolution Rate
**Definition:** % of sessions resolved without a follow-up required
**Target:** >= 70%

### KPI 6 — Cost per Resolution
**Definition:** Average LLM inference cost per session
**Target:** < .02

### Supporting Metrics (Dashboard)

| Metric | Description |
|---|---|
| Intent Classification Confidence Distribution | Histogram of confidence scores; monitors model drift |
| Tool Call Error Rate | % of tool calls failing; per-tool breakdown |
| LLM Groundedness Score (FAQ) | Average RAG answer groundedness; detects hallucination trends |
| Agent Queue Depth (HITL) | Human agent backlog; triggers auto-scaling alerts |
| Session Memory Purge Compliance | Confirms TTL enforcement rate |

## 7.1 Live Observability
The system includes a real-time event bus and a Next.js 14 Cockpit UI. 
- **Event Emitter**: Emits events (`node_enter`, `node_exit`, `intent_classified`, `tool_call`, `tool_result`, `guardrail_check`, `guardrail_violation`, etc.) directly from the LangGraph execution context via `asyncio.Queue` without blocking inference.
- **Cockpit UI**: Provides live reasoning traces, agent flow canvas topology visualization, and Server-Sent Events (SSE) streaming for real-time human oversight.

---

## 8. Deployment Requirements

- **Container:** Docker + Kubernetes (EKS/GKE)
- **Orchestration Framework:** LangGraph (stateful multi-agent graphs)
- **LLM Provider:** Gemini Pro 1.5 (primary) + GPT-4o (fallback)
- **Vector DB:** Pinecone (production) + FAISS (local dev)
- **Session Store:** Redis Cluster (ElastiCache)
- **Message Queue:** Apache Kafka (event streaming between agents)
- **CI/CD:** GitHub Actions → ArgoCD → Kubernetes
- **Observability:** Langfuse (LLM tracing) + Prometheus + Grafana + PagerDuty

---

## 9. Open Questions & Risks

| ID | Question/Risk | Owner | Status |
|---|---|---|---|
| OQ-001 | OMS API rate limits under 10K daily load? | Engineering | Pending |
| OQ-002 | Stripe sandbox → production promotion timeline? | Finance + Eng | Pending |
| OQ-003 | GDPR legal review of session vault architecture | Legal | In Review |
| RISK-001 | LLM provider outage — fallback to deterministic responses? | Arch | Mitigated (dual-provider) |
| RISK-002 | Semantic router accuracy degradation over time (model drift) | ML Eng | Mitigated (weekly eval pipeline) |

---

*Document Owner: AI Platform Team | Review Cycle: Monthly | Next Review: June 2026*
