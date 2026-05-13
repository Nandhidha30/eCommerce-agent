"use client";
import { useStore } from "@/lib/store";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight } from "lucide-react";

const TYPE_META: Record<string, { color: string; bg: string; border: string; label: string }> = {
  run_started:           { color: "#a78bfa", bg: "rgba(167,139,250,0.08)", border: "#a78bfa", label: "RUN" },
  run_completed:         { color: "#06b6d4", bg: "rgba(6,182,212,0.08)",   border: "#06b6d4", label: "END" },
  node_enter:            { color: "#a78bfa", bg: "rgba(167,139,250,0.05)", border: "#a78bfa", label: "NODE→" },
  node_exit:             { color: "#5a5a6b", bg: "rgba(90,90,107,0.05)",   border: "#5a5a6b", label: "←NODE" },
  intent_classified:     { color: "#60a5fa", bg: "rgba(96,165,250,0.08)",  border: "#60a5fa", label: "INTENT" },
  agent_invoked:         { color: "#06b6d4", bg: "rgba(6,182,212,0.08)",   border: "#06b6d4", label: "AGENT" },
  tool_call:             { color: "#c084fc", bg: "rgba(192,132,252,0.08)", border: "#c084fc", label: "TOOL→" },
  tool_result:           { color: "#c084fc", bg: "rgba(192,132,252,0.05)", border: "#c084fc", label: "←TOOL" },
  guardrail_check:       { color: "#10b981", bg: "rgba(16,185,129,0.08)",  border: "#10b981", label: "✓ GUARD" },
  guardrail_violation:   { color: "#ef4444", bg: "rgba(239,68,68,0.12)",   border: "#ef4444", label: "⚠ GUARD" },
  escalation_triggered:  { color: "#f59e0b", bg: "rgba(245,158,11,0.1)",   border: "#f59e0b", label: "ESCALATE" },
  final_response:        { color: "#10b981", bg: "rgba(16,185,129,0.08)",  border: "#10b981", label: "RESPONSE" },
};

const DEFAULT_META = { color: "#8b8b9b", bg: "transparent", border: "#2a2a35", label: "EVENT" };

function summarize(type: string, payload: any): string {
  if (!payload) return "";
  switch (type) {
    case "run_started": return `"${payload.message || ''}"`;
    case "run_completed": return `${payload.status} · ${payload.total_duration_ms}ms`;
    case "node_enter": return `→ ${payload.node || ''}`;
    case "node_exit": return `${payload.duration_ms ?? 0}ms`;
    case "intent_classified": return `${payload.intent} (${((payload.confidence||0)*100).toFixed(0)}%)`;
    case "agent_invoked": return `→ ${payload.agent}`;
    case "tool_call": return `${payload.tool}(${Object.keys(payload.args || {}).join(',')})`;
    case "tool_result": return `${payload.duration_ms ?? 0}ms · ${(payload.result_summary || '').slice(0, 40)}`;
    case "guardrail_check": return `${payload.guardrail} ✓`;
    case "guardrail_violation": return `${payload.guardrail} · ${payload.action}`;
    case "escalation_triggered": return `${payload.reason || ''}`;
    case "final_response": return `${payload.agent}: "${(payload.text || '').slice(0, 50)}..."`;
    default: return JSON.stringify(payload).slice(0, 60);
  }
}

export default function ActivityFeed() {
  const events = useStore((state) => state.events);
  const endRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [events.length]);

  return (
    <div className="flex-1 overflow-y-auto px-3 py-3 flex flex-col gap-1.5">
      {events.length === 0 && (
        <div className="m-auto text-center text-xs text-dim py-8">
          Waiting for events...
          <div className="text-[10px] text-dim/60 mt-2">Trigger a query to see live activity</div>
        </div>
      )}
      <AnimatePresence initial={false}>
        {events.map((e, idx) => {
          const m = TYPE_META[e.type] || DEFAULT_META;
          const isOpen = expanded === idx;
          const time = e.ts?.split('T')[1]?.substring(0, 12) || '';

          return (
            <motion.div
              key={`${e.step}-${idx}`}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="rounded-lg border overflow-hidden cursor-pointer"
              style={{ borderColor: m.border + "55", background: m.bg }}
              onClick={() => setExpanded(isOpen ? null : idx)}
            >
              <div className="flex items-center gap-2 px-2.5 py-1.5">
                <ChevronRight
                  className="w-3 h-3 shrink-0 transition-transform"
                  style={{ color: m.color, transform: isOpen ? "rotate(90deg)" : "" }}
                />
                <span className="font-mono text-[9.5px] text-dim shrink-0 w-[68px]">{time}</span>
                <span
                  className="text-[9px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded shrink-0"
                  style={{ color: m.color, background: m.color + "1a" }}
                >
                  {m.label}
                </span>
                <span className="text-[11px] text-primary/85 truncate flex-1 font-mono">
                  {summarize(e.type, e.payload)}
                </span>
              </div>
              {isOpen && (
                <div className="border-t border-border/40 bg-base/40 px-3 py-2 font-mono text-[10px] text-muted whitespace-pre-wrap break-all max-h-[200px] overflow-y-auto">
                  {JSON.stringify(e.payload, null, 2)}
                </div>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
      <div ref={endRef} />
    </div>
  );
}
