"""NEXUS Streamlit frontend — premium dark glassmorphism chat UI + KPI dashboard."""
import streamlit as st
import httpx
import time
import json
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS — AI Customer Resolution",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000"

# ── Custom CSS — dark glassmorphism ──────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  /* Global */
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 50%, #0a0a1a 100%); }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03);
    border-right: 1px solid rgba(255,255,255,0.08);
  }

  /* Chat container */
  .chat-container {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
    min-height: 420px;
    max-height: 520px;
    overflow-y: auto;
  }

  /* Message bubbles */
  .msg-user {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0 8px 20%;
    font-size: 0.95rem;
    line-height: 1.5;
    box-shadow: 0 4px 20px rgba(99,102,241,0.25);
  }
  .msg-agent {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 8px 20% 8px 0;
    font-size: 0.95rem;
    line-height: 1.5;
  }
  .msg-system {
    text-align: center;
    color: rgba(255,255,255,0.35);
    font-size: 0.78rem;
    margin: 4px 0;
    font-style: italic;
  }

  /* Agent badge */
  .agent-badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 99px;
    margin-bottom: 5px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .badge-order    { background: rgba(59,130,246,0.2);  color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }
  .badge-refund   { background: rgba(16,185,129,0.2);  color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
  .badge-faq      { background: rgba(245,158,11,0.2);  color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
  .badge-human    { background: rgba(239,68,68,0.2);   color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
  .badge-system   { background: rgba(139,92,246,0.2);  color: #a78bfa; border: 1px solid rgba(139,92,246,0.3); }

  /* KPI cards */
  .kpi-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 18px 20px;
    text-align: center;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
  }
  .kpi-card:hover { border-color: rgba(99,102,241,0.4); }
  .kpi-value { font-size: 2rem; font-weight: 700; color: #a78bfa; margin: 4px 0; }
  .kpi-label { font-size: 0.78rem; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-target { font-size: 0.7rem; color: rgba(255,255,255,0.3); margin-top: 4px; }

  /* Ticket card */
  .ticket-card {
    background: rgba(239,68,68,0.07);
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 14px;
    padding: 16px;
    margin-top: 12px;
  }

  /* Citations */
  .citation {
    font-size: 0.72rem;
    color: rgba(167,139,250,0.7);
    margin-top: 6px;
    font-style: italic;
  }

  /* Input area */
  .stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 16px !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
  }

  /* Buttons */
  .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 28px !important;
    transition: opacity 0.2s !important;
  }
  .stButton > button:hover { opacity: 0.85 !important; }

  /* Divider */
  hr { border-color: rgba(255,255,255,0.06) !important; }

  /* Section headers */
  h1, h2, h3 { color: #e2e8f0 !important; font-family: 'Inter', sans-serif !important; }

  /* Metrics */
  [data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 12px;
  }

  /* Hide Streamlit branding */
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],          # list of {role, content, agent, meta}
        "session_id": None,
        "customer_id": "CUST-DEMO-001",
        "turn_count": 0,
        "last_agent": None,
        "last_ticket": None,
        "api_available": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── API helpers ───────────────────────────────────────────────────────────────
def check_api() -> bool:
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def send_message(message: str) -> dict | None:
    try:
        payload = {
            "message": message,
            "customer_id": st.session_state.customer_id,
        }
        if st.session_state.session_id:
            payload["session_id"] = st.session_state.session_id

        r = httpx.post(f"{API_BASE}/chat", json=payload, timeout=90)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        return {"error": str(e)}
    return None


def get_metrics() -> dict | None:
    try:
        r = httpx.get(f"{API_BASE}/metrics", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def get_demo_orders() -> list:
    try:
        r = httpx.get(f"{API_BASE}/demo/orders", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


# ── Agent badge helper ────────────────────────────────────────────────────────
AGENT_BADGE_MAP = {
    "Order Tracker":    ("badge-order",  "📦 Order Tracker"),
    "Refund Processor": ("badge-refund", "💳 Refund Processor"),
    "FAQ Specialist":   ("badge-faq",    "📚 FAQ Specialist"),
    "Human Bridge":     ("badge-human",  "🧑‍💼 Human Bridge"),
    "Orchestrator":     ("badge-system", "⚙️ Orchestrator"),
}

def agent_badge_html(agent_name: str) -> str:
    css_class, label = AGENT_BADGE_MAP.get(agent_name, ("badge-system", agent_name))
    return f'<span class="agent-badge {css_class}">{label}</span>'


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 NEXUS")
    st.markdown("<p style='color:rgba(255,255,255,0.4);font-size:0.8rem;margin-top:-10px;'>Agentic AI Resolution System</p>", unsafe_allow_html=True)
    st.divider()

    # API status
    api_ok = check_api()
    st.session_state.api_available = api_ok

    # Customer config
    st.markdown("**Customer Session**")
    st.session_state.customer_id = st.text_input(
        "Customer ID", value=st.session_state.customer_id, key="cid_input"
    )

    if st.session_state.session_id:
        st.caption(f"Session: `{st.session_state.session_id[:16]}...`")
        st.caption(f"Turns: {st.session_state.turn_count}")

    if st.button("🔄 New Session"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.turn_count = 0
        st.session_state.last_agent = None
        st.session_state.last_ticket = None
        st.rerun()

    st.divider()

    # Quick demo prompts
    st.markdown("**💡 Try These**")
    demo_prompts = [
        ("📦", "Track order ORD-001"),
        ("💳", "Refund my order ORD-002"),
        ("💳", "I need a $600 refund for ORD-003"),
        ("📚", "What is your return policy?"),
        ("📚", "How long does shipping take?"),
        ("🧑‍💼", "I want to speak to a human"),
        ("📚", "Are digital downloads refundable?"),
        ("📦", "Where is order ORD-004?"),
    ]
    for icon, prompt in demo_prompts:
        if st.button(f"{icon} {prompt}", key=f"demo_{prompt[:20]}"):
            st.session_state["_pending_prompt"] = prompt
            st.rerun()

    st.divider()

# ── Main layout ───────────────────────────────────────────────────────────────
tab_chat, tab_metrics = st.tabs(["💬 Chat", "📊 Live Metrics"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    col_chat, col_info = st.columns([3, 1])

    with col_chat:
        st.markdown("### 💬 Customer Support Chat")
        st.markdown("<p style='color:rgba(255,255,255,0.4);font-size:0.85rem;margin-top:-10px;'>Powered by NEXUS Agentic AI</p>", unsafe_allow_html=True)

        # ── Chat window ───────────────────────────────────────────────────────
        chat_html = '<div class="chat-container" id="chat-window">'

        if not st.session_state.messages:
            chat_html += '<div class="msg-system">👋 Hello! I\'m NEXUS, your AI support assistant. Ask me about your order, refunds, or policies.</div>'
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    chat_html += f'<div class="msg-user">{msg["content"]}</div>'
                elif msg["role"] == "agent":
                    badge = agent_badge_html(msg.get("agent", "Orchestrator"))
                    citations_html = ""
                    if msg.get("citations"):
                        cit_text = " · ".join(msg["citations"][:2])
                        citations_html = f'<div class="citation">📎 {cit_text}</div>'
                    rt = msg.get("resolution_time_ms", 0)
                    rt_html = f'<div style="font-size:0.68rem;color:rgba(255,255,255,0.2);margin-top:6px;">⚡ {rt}ms</div>'
                    chat_html += f'<div>{badge}<div class="msg-agent">{msg["content"]}{citations_html}{rt_html}</div></div>'
                elif msg["role"] == "system":
                    chat_html += f'<div class="msg-system">{msg["content"]}</div>'

        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        # ── Input + send ──────────────────────────────────────────────────────
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Message",
                placeholder="Ask about your order, refund, or policy...",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Send →", use_container_width=True)

        # Handle demo prompt
        pending = st.session_state.pop("_pending_prompt", None)
        if pending:
            user_input = pending
            submitted = True

        if submitted and user_input.strip():
            if not st.session_state.api_available:
                st.error("API is offline. Please start the backend first.")
            else:
                # Add user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input,
                })

                with st.spinner("🤔 Thinking..."):
                    result = send_message(user_input)

                if result and "error" not in result:
                    st.session_state.session_id = result.get("session_id")
                    st.session_state.turn_count = result.get("turn", 0)
                    st.session_state.last_agent = result.get("agent_used")

                    # Add agent response
                    st.session_state.messages.append({
                        "role": "agent",
                        "content": result.get("message", ""),
                        "agent": result.get("agent_used", "Orchestrator"),
                        "citations": result.get("citations", []),
                        "resolution_time_ms": result.get("resolution_time_ms", 0),
                    })

                    # Escalation notice
                    if result.get("escalated"):
                        data = result.get("data", {})
                        st.session_state.last_ticket = data
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"🎫 Escalated to human agent — Ticket: {data.get('ticket_id', 'N/A')} | Priority: {data.get('priority', 'N/A')}",
                        })

                    st.rerun()
                elif result and "error" in result:
                    st.error(f"Error: {result['error']}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: LIVE METRICS
# ══════════════════════════════════════════════════════════════════════════════
with tab_metrics:
    st.markdown("### 📊 Live KPI Dashboard")
    st.markdown("<p style='color:rgba(255,255,255,0.4);font-size:0.85rem;margin-top:-10px;'>Updates on each chat interaction</p>", unsafe_allow_html=True)

    if not st.session_state.api_available:
        st.warning("Start the backend API to see live metrics.")
    else:
        metrics = get_metrics()
        if metrics:
            # KPI Row 1
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                aar = metrics.get("automation_accuracy_rate", 0)
                color = "#34d399" if aar >= 87 else "#fbbf24" if aar >= 70 else "#f87171"
                st.markdown(f"""<div class='kpi-card'>
<div class='kpi-label'>Automation Accuracy</div>
<div class='kpi-value' style='color:{color};'>{aar}%</div>
<div class='kpi-target'>Target: ≥ 87%</div>
</div>""", unsafe_allow_html=True)

            with c2:
                art = metrics.get("avg_resolution_time_ms", 0)
                art_sec = round(art / 1000, 1)
                color = "#34d399" if art < 180000 else "#fbbf24" if art < 360000 else "#f87171"
                st.markdown(f"""<div class='kpi-card'>
<div class='kpi-label'>Avg Resolution Time</div>
<div class='kpi-value' style='color:{color};'>{art_sec}s</div>
<div class='kpi-target'>Target: &lt; 180s</div>
</div>""", unsafe_allow_html=True)

            with c3:
                esc = metrics.get("escalation_rate", 0)
                color = "#34d399" if esc <= 15 else "#fbbf24" if esc <= 25 else "#f87171"
                st.markdown(f"""<div class='kpi-card'>
<div class='kpi-label'>Escalation Rate</div>
<div class='kpi-value' style='color:{color};'>{esc}%</div>
<div class='kpi-target'>Target: ≤ 15%</div>
</div>""", unsafe_allow_html=True)

            with c4:
                gtr = metrics.get("guardrail_trigger_rate", 0)
                color = "#34d399" if gtr < 2 else "#fbbf24" if gtr < 5 else "#f87171"
                st.markdown(f"""<div class='kpi-card'>
<div class='kpi-label'>Guardrail Trigger Rate</div>
<div class='kpi-value' style='color:{color};'>{gtr}%</div>
<div class='kpi-target'>Target: &lt; 2%</div>
</div>""", unsafe_allow_html=True)

            st.divider()

            # Session summary
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Sessions", metrics.get("total_sessions", 0))
                st.metric("Resolved by AI", metrics.get("resolved_sessions", 0))
                st.metric("Escalated to Human", metrics.get("escalated_sessions", 0))

            with col_b:
                # Intent distribution chart
                import plotly.graph_objects as go
                intent_data = metrics.get("intent_distribution", {})
                if intent_data:
                    labels = list(intent_data.keys())
                    values = list(intent_data.values())
                    colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
                    fig = go.Figure(data=[go.Pie(
                        labels=labels, values=values,
                        hole=0.55,
                        marker=dict(colors=colors[:len(labels)]),
                        textfont=dict(color="white", size=11),
                    )])
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=True,
                        legend=dict(font=dict(color="rgba(255,255,255,0.6)", size=11)),
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=250,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Send some messages to see intent distribution.")
        else:
            st.info("No sessions yet. Start chatting to generate metrics!")


