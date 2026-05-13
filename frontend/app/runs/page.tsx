"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import { Play } from "lucide-react";

export default function RunsPage() {
  const [runs, setRuns] = useState<any[]>([]);

  useEffect(() => {
    api.getRuns().then(setRuns);
  }, []);

  return (
    <div className="p-8 h-full overflow-y-auto bg-base">
      <h1 className="text-2xl font-semibold mb-6">Run History</h1>
      <div className="bg-panel border border-border rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-elevated/50 text-muted uppercase tracking-wider text-xs">
            <tr>
              <th className="p-4 font-medium">Session ID</th>
              <th className="p-4 font-medium">Intent</th>
              <th className="p-4 font-medium">Agent Used</th>
              <th className="p-4 font-medium">Status</th>
              <th className="p-4 font-medium">Violations</th>
              <th className="p-4 font-medium">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {runs.map((r) => (
              <tr key={r.session_id} className="hover:bg-elevated/30 transition-colors">
                <td className="p-4 font-mono text-xs">{r.session_id}</td>
                <td className="p-4">{r.intent}</td>
                <td className="p-4">{r.agent_used}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-full text-[10px] uppercase tracking-wider ${r.status === 'resolved' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                    {r.status}
                  </span>
                </td>
                <td className="p-4">
                  {r.violations > 0 ? (
                    <span className="bg-danger/20 text-danger px-2 py-1 rounded-full text-xs font-bold">{r.violations}</span>
                  ) : (
                    <span className="text-muted">-</span>
                  )}
                </td>
                <td className="p-4">
                  <Link href={`/runs/${r.session_id}`} className="text-accent hover:text-accent-2 transition-colors flex items-center gap-1">
                    <Play className="w-4 h-4" /> Replay
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
