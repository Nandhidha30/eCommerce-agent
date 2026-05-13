"use client";
import { useStore } from "@/lib/store";

export default function MetricsStrip() {
  const events = useStore((state) => state.events);
  const stepCount = events.length > 0 ? events[events.length - 1].step : 0;
  
  const toolsCount = events.filter(e => e.type === "tool_call").length;
  const guardrailHits = events.filter(e => e.type === "guardrail_violation").length;
  
  const startEvent = events.find(e => e.type === "run_started");
  const endEvent = events.find(e => e.type === "run_completed");
  
  let duration = 0;
  if (endEvent) {
    duration = endEvent.payload.total_duration_ms;
  } else if (startEvent && events.length > 0) {
    const last = events[events.length - 1];
    duration = new Date(last.ts).getTime() - new Date(startEvent.ts).getTime();
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      <MetricCard label="Step Count" value={stepCount.toString()} />
      <MetricCard label="Elapsed Time" value={`${(duration / 1000).toFixed(2)}s`} />
      <MetricCard label="Tools Called" value={toolsCount.toString()} />
      <MetricCard label="Guardrail Hits" value={guardrailHits.toString()} alert={guardrailHits > 0} />
    </div>
  );
}

function MetricCard({ label, value, alert }: { label: string, value: string, alert?: boolean }) {
  return (
    <div className={`p-2.5 rounded-lg border ${alert ? 'bg-danger/10 border-danger/30' : 'bg-elevated border-border'}`}>
      <div className="text-[10px] text-muted uppercase font-bold tracking-wider mb-1">{label}</div>
      <div className={`text-xl font-mono ${alert ? 'text-danger' : 'text-primary'}`}>{value}</div>
    </div>
  );
}
