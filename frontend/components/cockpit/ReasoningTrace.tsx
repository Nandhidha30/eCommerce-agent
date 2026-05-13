"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useStore } from "@/lib/store";

export default function ReasoningTrace() {
  const events = useStore((state) => state.events);
  const traceEvents = events.filter((e) =>
    ["node_enter", "agent_invoked", "tool_call", "tool_result", "intent_classified", "guardrail_check"].includes(e.type)
  );

  return (
    <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
      <AnimatePresence>
        {traceEvents.map((e, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-elevated border border-border rounded-lg p-3 text-sm flex gap-3 shadow-sm relative overflow-hidden"
          >
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${getColor(e.type)}`} />
            <div className="flex-1 min-w-0 pl-1">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-xs font-semibold text-primary/80 uppercase">{e.node || "System"}</span>
                <span className="text-[10px] text-muted font-mono">{e.ts.split('T')[1]?.substring(0, 8)}</span>
              </div>
              <div className="text-dim text-xs whitespace-pre-wrap">
                {formatPayload(e)}
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

function getColor(type: string) {
  if (type.includes("guardrail")) return "bg-success";
  if (type.includes("tool")) return "bg-info";
  if (type === "intent_classified") return "bg-accent-2";
  return "bg-accent";
}

function formatPayload(e: any) {
  if (e.type === "intent_classified") return `Classified as ${e.payload.intent} (${(e.payload.confidence * 100).toFixed(1)}%)`;
  if (e.type === "tool_call") return `Calling ${e.payload.tool}(${Object.keys(e.payload.args).join(', ')})`;
  if (e.type === "tool_result") return `Result: ${e.payload.result_summary} (+${e.payload.duration_ms}ms)`;
  if (e.type === "guardrail_check") return `Passed check: ${e.payload.guardrail}`;
  return JSON.stringify(e.payload);
}
