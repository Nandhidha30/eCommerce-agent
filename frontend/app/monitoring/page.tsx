"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [guardrails, setGuardrails] = useState<any>(null);

  useEffect(() => {
    const fetchAll = () => {
      api.getMetrics().then(setMetrics);
      api.getGuardrailBreakdown().then(setGuardrails);
    };
    fetchAll();
    const t = setInterval(fetchAll, 5000);
    return () => clearInterval(t);
  }, []);

  if (!metrics) return <div className="p-8">Loading monitoring data...</div>;

  return (
    <div className="p-8 h-full overflow-y-auto bg-base">
      <h1 className="text-2xl font-semibold mb-6">Live Monitoring Dashboard</h1>
      
      {/* Top KPIs */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <KpiCard title="Total Sessions" value={metrics.total_sessions} />
        <KpiCard title="Avg Resolution Time" value={`${(metrics.avg_resolution_time_ms / 1000).toFixed(2)}s`} />
        <KpiCard title="Resolution Rate" value={`${(metrics.resolution_rate * 100).toFixed(1)}%`} />
        <KpiCard title="Guardrails Triggered" value={metrics.guardrails_triggered} />
      </div>

      {/* Charts / Details */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-panel border border-border rounded-xl p-6">
          <h2 className="text-sm text-muted mb-4 uppercase tracking-widest">Intent Distribution</h2>
          <div className="space-y-3">
            {Object.entries(metrics.intent_distribution).map(([intent, count]: any) => (
              <div key={intent} className="flex items-center justify-between">
                <span className="capitalize">{intent.replace('_', ' ')}</span>
                <span className="font-mono">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-panel border border-border rounded-xl p-6">
          <h2 className="text-sm text-muted mb-4 uppercase tracking-widest">Guardrail Violations (24h)</h2>
          <div className="space-y-3">
            {guardrails && Object.entries(guardrails).map(([name, count]: any) => (
              <div key={name} className="flex items-center justify-between">
                <span className="capitalize">{name}</span>
                <span className="font-mono text-danger">{count}</span>
              </div>
            ))}
            {(!guardrails || Object.keys(guardrails).length === 0) && (
              <span className="text-muted">No violations</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ title, value }: { title: string, value: string | number }) {
  return (
    <div className="bg-panel border border-border rounded-xl p-6 flex flex-col">
      <span className="text-muted text-xs uppercase tracking-widest font-semibold mb-2">{title}</span>
      <span className="text-3xl font-light text-primary">{value}</span>
    </div>
  );
}
