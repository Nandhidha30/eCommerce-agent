"use client";
import { useStore } from "@/lib/store";
import { motion } from "framer-motion";
import { useMemo } from "react";

// Map backend agent identifiers → canvas agent IDs
const AGENT_KEY: Record<string, string> = {
  "order_status": "order",
  "Order Tracker": "order",
  "refund_request": "refund",
  "Refund Processor": "refund",
  "faq_policy": "faq",
  "FAQ Specialist": "faq",
  "human_escalation": "human",
  "Human Bridge": "human",
  "customer_request": "human",
};

const GUARDRAIL_KEY: Record<string, string> = {
  "financial": "financial",
  "privacy": "privacy",
  "loop_detector": "loop",
  "loop": "loop",
};

type AgentState = "idle" | "active" | "done";
type GuardrailState = "idle" | "pass" | "fail";

export default function AgentFlowCanvas() {
  const events = useStore((s) => s.events);

  // Derive sticky agent states (active until next handoff or run end)
  const { agentStates, guardrailStates, activeAgent } = useMemo(() => {
    const agents: Record<string, AgentState> = {
      orchestrator: "idle", order: "idle", refund: "idle", faq: "idle", human: "idle",
    };
    const guardrails: Record<string, GuardrailState> = {
      financial: "idle", privacy: "idle", loop: "idle",
    };
    let active: string | null = null;

    for (const e of events) {
      if (e.type === "run_started") {
        // Reset
        Object.keys(agents).forEach((k) => (agents[k] = "idle"));
        Object.keys(guardrails).forEach((k) => (guardrails[k] = "idle"));
        active = "orchestrator";
        agents.orchestrator = "active";
      }
      if (e.type === "node_enter") {
        const node = (e.payload as any)?.node || e.node;
        if (["intake", "classify", "clarify", "route", "respond"].includes(node)) {
          if (active !== "orchestrator") {
            // Returning to orchestrator (e.g., respond after specialist)
            if (active) agents[active] = "done";
          }
          agents.orchestrator = "active";
          active = "orchestrator";
        }
      }
      if (e.type === "agent_invoked") {
        const key = (e.payload as any)?.agent;
        const id = AGENT_KEY[key];
        if (id) {
          agents.orchestrator = "done";
          if (active && active !== id) agents[active] = "done";
          agents[id] = "active";
          active = id;
        }
      }
      if (e.type === "escalation_triggered") {
        if (active && active !== "human") agents[active] = "done";
        agents.human = "active";
        active = "human";
      }
      if (e.type === "guardrail_check") {
        const g = GUARDRAIL_KEY[(e.payload as any)?.guardrail] || (e.payload as any)?.guardrail;
        if (g && g in guardrails) guardrails[g] = "pass";
      }
      if (e.type === "guardrail_violation") {
        const g = GUARDRAIL_KEY[(e.payload as any)?.guardrail] || (e.payload as any)?.guardrail;
        if (g && g in guardrails) guardrails[g] = "fail";
      }
      if (e.type === "run_completed") {
        if (active) agents[active] = "done";
        active = null;
      }
    }

    return { agentStates: agents, guardrailStates: guardrails, activeAgent: active };
  }, [events]);

  return (
    <div className="w-full h-full relative">
      <svg viewBox="0 0 800 380" preserveAspectRatio="xMidYMid meet" className="w-full h-full">
        <defs>
          {/* Glow filters per agent */}
          {[
            ["orchestrator", "#a78bfa"],
            ["order", "#60a5fa"],
            ["refund", "#10b981"],
            ["faq", "#f59e0b"],
            ["human", "#ef4444"],
          ].map(([id, color]) => (
            <filter key={id} id={`glow-${id}`} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feFlood floodColor={color} floodOpacity="0.6" />
              <feComposite in2="blur" operator="in" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          ))}

          {/* Edge gradient */}
          <linearGradient id="edge-grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.1" />
          </linearGradient>

          <linearGradient id="edge-active" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#a78bfa" stopOpacity="1" />
            <stop offset="100%" stopColor="#60a5fa" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        {/* Edges — from Orchestrator to each specialist */}
        {[
          { x: 130, agent: "order" },
          { x: 320, agent: "refund" },
          { x: 510, agent: "faq" },
          { x: 690, agent: "human" },
        ].map(({ x, agent }) => {
          const isActive = activeAgent === agent || agentStates[agent] !== "idle";
          return (
            <g key={agent}>
              <path
                d={`M 400 100 Q 400 140 ${x + 65} 175`}
                stroke={isActive ? "url(#edge-active)" : "#2a2a35"}
                strokeWidth={isActive ? 2.5 : 1.5}
                fill="none"
                strokeDasharray={isActive ? "0" : "4 4"}
                opacity={isActive ? 1 : 0.4}
              />
              {activeAgent === agent && (
                <motion.circle
                  r="4"
                  fill="#a78bfa"
                  initial={{ offsetDistance: "0%" }}
                  animate={{ offsetDistance: "100%" }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
                  style={{
                    offsetPath: `path('M 400 100 Q 400 140 ${x + 65} 175')`,
                  } as any}
                />
              )}
            </g>
          );
        })}

        {/* Orchestrator (top center) */}
        <AgentNode
          x={335} y={45} w={130} h={56}
          id="orchestrator" name="Orchestrator" subtitle="Router & Supervisor"
          color="#a78bfa" state={agentStates.orchestrator}
        />

        {/* Specialists (row) */}
        <AgentNode x={65} y={175} w={130} h={56} id="order" name="Order Tracker" subtitle="Tracking & ETA" color="#60a5fa" state={agentStates.order} />
        <AgentNode x={255} y={175} w={130} h={56} id="refund" name="Refund Processor" subtitle="Returns & Stripe" color="#10b981" state={agentStates.refund} />
        <AgentNode x={445} y={175} w={130} h={56} id="faq" name="FAQ Specialist" subtitle="Policy & RAG" color="#f59e0b" state={agentStates.faq} />
        <AgentNode x={625} y={175} w={130} h={56} id="human" name="Human Bridge" subtitle="Escalation" color="#ef4444" state={agentStates.human} />

        {/* Guardrails strip */}
        <g transform="translate(0, 290)">
          <text x="400" y="0" fill="#8b8b9b" fontSize="10" textAnchor="middle"
                style={{ letterSpacing: "2px", fontWeight: 600 }}>
            GUARDRAILS
          </text>
          <Guardrail x={210} name="Financial" state={guardrailStates.financial} />
          <Guardrail x={345} name="Privacy" state={guardrailStates.privacy} />
          <Guardrail x={480} name="Loop Detector" state={guardrailStates.loop} />
        </g>
      </svg>
    </div>
  );
}

function AgentNode({
  x, y, w, h, id, name, subtitle, color, state,
}: {
  x: number; y: number; w: number; h: number;
  id: string; name: string; subtitle: string; color: string;
  state: AgentState;
}) {
  const isActive = state === "active";
  const isDone = state === "done";

  return (
    <motion.g
      initial={false}
      animate={{
        scale: isActive ? 1.04 : 1,
        opacity: state === "idle" ? 0.55 : 1,
      }}
      transition={{ type: "spring", stiffness: 280, damping: 22 }}
    >
      {/* Glow background when active */}
      {isActive && (
        <motion.rect
          x={x - 6} y={y - 6} width={w + 12} height={h + 12} rx={16}
          fill={color} opacity={0.15}
          animate={{ opacity: [0.1, 0.25, 0.1] }}
          transition={{ duration: 1.8, repeat: Infinity }}
        />
      )}

      <rect
        x={x} y={y} width={w} height={h} rx={12}
        fill="#161622"
        stroke={isActive ? color : isDone ? color : "#2a2a35"}
        strokeWidth={isActive ? 2 : 1.5}
        strokeOpacity={isDone && !isActive ? 0.55 : 1}
        filter={isActive ? `url(#glow-${id})` : undefined}
      />

      {/* Status indicator */}
      <circle
        cx={x + 12} cy={y + h / 2} r={4}
        fill={state === "idle" ? "#5a5a6b" : color}
      />
      {isActive && (
        <motion.circle
          cx={x + 12} cy={y + h / 2} r={4}
          fill={color}
          animate={{ r: [4, 8, 4], opacity: [0.8, 0, 0.8] }}
          transition={{ duration: 1.4, repeat: Infinity }}
        />
      )}

      <text
        x={x + 24} y={y + h / 2 - 4}
        fill="#e8e8ef" fontSize="12.5"
        style={{ fontWeight: 600 }}
      >
        {name}
      </text>
      <text
        x={x + 24} y={y + h / 2 + 12}
        fill="#8b8b9b" fontSize="9.5"
        style={{ letterSpacing: "0.5px" }}
      >
        {subtitle}
      </text>
    </motion.g>
  );
}

function Guardrail({ x, name, state }: { x: number; name: string; state: GuardrailState }) {
  const stroke = state === "fail" ? "#ef4444" : state === "pass" ? "#10b981" : "#2a2a35";
  const fill = state === "fail" ? "rgba(239,68,68,0.15)" : state === "pass" ? "rgba(16,185,129,0.1)" : "#161622";
  const textColor = state === "fail" ? "#ef4444" : state === "pass" ? "#10b981" : "#8b8b9b";

  return (
    <motion.g
      animate={state === "fail" ? { x: [0, -3, 3, -2, 2, 0] } : { x: 0 }}
      transition={{ duration: 0.4 }}
    >
      <rect x={x} y={15} width={130} height={32} rx={8}
            fill={fill} stroke={stroke} strokeWidth={1.5} />
      <circle cx={x + 14} cy={31} r={3.5}
              fill={state === "idle" ? "#5a5a6b" : stroke} />
      <text x={x + 26} y={35} fill={textColor} fontSize="11"
            style={{ fontWeight: 600 }}>
        {name}
      </text>
    </motion.g>
  );
}
