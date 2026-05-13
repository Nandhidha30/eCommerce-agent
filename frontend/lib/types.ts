export interface NexusEvent {
  type: string;
  session_id: string;
  ts: string;
  step: number;
  node: string | null;
  payload: any;
}

export interface RunSummary {
  session_id: string;
  customer_id: string;
  intent: string;
  agent_used: string;
  status: string;
  duration_ms: number;
  violations: number;
  query_preview: string;
}

export interface MetricsData {
  total_sessions: number;
  resolution_rate: number;
  avg_resolution_time_ms: number;
  escalation_rate: number;
  intent_distribution: Record<string, number>;
  guardrails_triggered: number;
}
