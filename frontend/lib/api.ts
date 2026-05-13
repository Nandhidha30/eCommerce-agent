const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const api = {
  chat: async (message: string, customerId: string, sessionId?: string) => {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, customer_id: customerId, session_id: sessionId })
    });
    return res.json();
  },
  getMetrics: async () => {
    const res = await fetch(`${API_BASE}/metrics`);
    return res.json();
  },
  getGuardrailBreakdown: async () => {
    const res = await fetch(`${API_BASE}/metrics/guardrail-breakdown`);
    return res.json();
  },
  getRuns: async () => {
    const res = await fetch(`${API_BASE}/runs`);
    return res.json();
  },
  getRunEvents: async (id: string) => {
    const res = await fetch(`${API_BASE}/runs/${id}`);
    return res.json();
  },
  getDemoOrders: async () => {
    const res = await fetch(`${API_BASE}/demo/orders`);
    return res.json();
  },
  checkHealth: async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  }
};
