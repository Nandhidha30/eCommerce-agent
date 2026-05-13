"use client";

import { useState, useEffect, useCallback } from "react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import { openSSEAndWait } from "@/lib/sse";
import { NexusEvent } from "@/lib/types";
import ChatPanel from "@/components/cockpit/ChatPanel";
import AgentFlowCanvas from "@/components/cockpit/AgentFlowCanvas";
import ReasoningTrace from "@/components/cockpit/ReasoningTrace";
import ActivityFeed from "@/components/cockpit/ActivityFeed";
import MetricsStrip from "@/components/cockpit/MetricsStrip";
import GuardrailBanner from "@/components/cockpit/GuardrailBanner";

export default function CockpitPage() {
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const addEvent = useStore((s) => s.addEvent);
  const addMessage = useStore((s) => s.addMessage);
  const clearEvents = useStore((s) => s.clearEvents);
  const setStreaming = useStore((s) => s.setStreaming);
  const setConnected = useStore((s) => s.setConnected);
  const setCurrentRunId = useStore((s) => s.setCurrentRunId);
  const isStreaming = useStore((s) => s.isStreaming);

  useEffect(() => {
    api.checkHealth().then(setHealthStatus);
    const i = setInterval(() => api.checkHealth().then(setHealthStatus), 10000);
    return () => clearInterval(i);
  }, []);

  /**
   * Send flow (FIXES THE RACE):
   * 1. Generate sid
   * 2. Push user message immediately to chat
   * 3. Open SSE and AWAIT 'connected' confirmation
   * 4. THEN POST /chat
   */
  const handleSend = useCallback(async (msg: string, customerId: string) => {
    if (isStreaming) return;
    const sid = crypto.randomUUID();

    clearEvents();
    setCurrentRunId(sid);
    addMessage({ role: "user", content: msg, ts: new Date().toISOString() });
    setStreaming(true);

    try {
      const es = await openSSEAndWait(sid, (ev: NexusEvent) => {
        addEvent(ev);
        if (ev.type === "run_completed") {
          es.close();
          setConnected(false);
          setStreaming(false);
        }
      });
      setConnected(true);

      // Fire chat now that listener is guaranteed alive
      await api.chat(msg, customerId, sid);
    } catch (err) {
      console.error("send failed", err);
      setStreaming(false);
      setConnected(false);
    }
  }, [isStreaming, clearEvents, setCurrentRunId, addMessage, setStreaming, addEvent, setConnected]);

  return (
    <div className="h-full flex relative bg-base">
      <GuardrailBanner />

      {/* Left Column: Chat */}
      <div className="w-[28%] min-w-[340px] border-r border-border bg-gradient-to-b from-panel to-base flex flex-col relative z-10">
        <div className="h-14 border-b border-border flex items-center justify-between px-5 bg-panel/80 backdrop-blur">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <div className={`w-2.5 h-2.5 rounded-full ${healthStatus?.status === 'healthy' ? 'bg-success' : 'bg-danger'}`} />
              {healthStatus?.status === 'healthy' && (
                <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-success animate-ping opacity-60" />
              )}
            </div>
            <h2 className="font-semibold text-sm text-primary tracking-tight">Customer Chat</h2>
          </div>
          <span className="text-[10px] text-muted font-mono uppercase tracking-wider px-2 py-1 rounded bg-elevated border border-border">
            {healthStatus?.llm_mode || "offline"}
          </span>
        </div>
        <ChatPanel onSendMessage={handleSend} isStreaming={isStreaming} />
      </div>

      {/* Center Column: Topology + Trace */}
      <div className="flex-1 border-r border-border bg-panel flex flex-col relative">
        <div className="h-[45%] min-h-[340px] border-b border-border relative overflow-hidden bg-gradient-to-br from-elevated/40 via-panel to-base">
          <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-semibold">Agent Topology</span>
            {isStreaming && (
              <span className="flex items-center gap-1.5 text-[10px] text-accent font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                LIVE
              </span>
            )}
          </div>
          <AgentFlowCanvas />
        </div>
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="h-11 border-b border-border flex items-center px-5 bg-elevated/30">
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-semibold">Reasoning Trace</span>
          </div>
          <ReasoningTrace />
        </div>
      </div>

      {/* Right Column: Feed + Metrics */}
      <div className="w-[26%] min-w-[300px] bg-gradient-to-b from-panel to-base flex flex-col relative z-10">
        <div className="p-4 border-b border-border bg-panel/80 backdrop-blur">
          <MetricsStrip />
        </div>
        <div className="h-11 border-b border-border flex items-center px-5 bg-elevated/30">
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-semibold">Live Event Stream</span>
        </div>
        <ActivityFeed />
      </div>
    </div>
  );
}
