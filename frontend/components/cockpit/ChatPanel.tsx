"use client";
import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";
import { useStore } from "@/lib/store";

interface Props {
  onSendMessage: (msg: string, customerId: string) => void;
  isStreaming: boolean;
}

export default function ChatPanel({ onSendMessage, isStreaming }: Props) {
  const [input, setInput] = useState("");
  const [customerId, setCustomerId] = useState("CUST-DEMO-001");
  const [scenarios, setScenarios] = useState<any[]>([]);
  const messages = useStore((s) => s.messages);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/demo-scenarios.json").then((r) => r.json()).then(setScenarios).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isStreaming]);

  const submit = () => {
    if (!input.trim() || isStreaming) return;
    onSendMessage(input.trim(), customerId);
    setInput("");
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Demo Scenario Pills */}
      <div className="p-3 border-b border-border/60 bg-base/30">
        <div className="text-[9px] uppercase tracking-[0.18em] text-dim mb-2 font-semibold">Quick Demos</div>
        <div className="flex flex-wrap gap-1.5">
          {scenarios.map((s) => (
            <button
              key={s.id}
              disabled={isStreaming}
              onClick={() => onSendMessage(s.message, customerId)}
              className="text-[11px] px-2.5 py-1 rounded-md border border-border bg-elevated/60 text-muted hover:text-primary hover:border-accent/60 hover:bg-elevated transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-5 flex flex-col gap-4">
        {messages.length === 0 && (
          <div className="m-auto text-center max-w-[260px]">
            <div className="w-12 h-12 rounded-full bg-elevated border border-border mx-auto mb-3 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-accent" />
            </div>
            <div className="text-sm font-medium text-primary mb-1">Welcome to NEXUS</div>
            <div className="text-xs text-muted leading-relaxed">
              Click a quick demo or type a message. Watch the agents work in real time on the right.
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${
              m.role === "user"
                ? "bg-gradient-to-br from-accent to-accent-2 shadow-lg shadow-accent/20"
                : "bg-elevated border border-border"
            }`}>
              {m.role === "user" ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-accent" />}
            </div>
            <div className={`max-w-[78%] ${m.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
              {m.role === "agent" && m.agent && (
                <div className="text-[9px] uppercase tracking-[0.15em] font-semibold text-accent/90 ml-1">
                  {m.agent}
                </div>
              )}
              <div className={`rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
                m.role === "user"
                  ? "bg-gradient-to-br from-accent/15 to-accent-2/10 border border-accent/25 text-primary rounded-tr-sm"
                  : "bg-elevated border border-border text-primary/95 rounded-tl-sm"
              }`}>
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            </div>
          </div>
        ))}

        {isStreaming && (
          <div className="flex gap-2.5">
            <div className="w-8 h-8 rounded-full bg-elevated border border-border flex items-center justify-center">
              <Bot className="w-4 h-4 text-accent animate-pulse" />
            </div>
            <div className="rounded-2xl px-3.5 py-2.5 bg-elevated border border-border flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce [animation-delay:-0.2s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce [animation-delay:-0.1s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-border bg-panel/50 backdrop-blur">
        <form
          onSubmit={(e) => { e.preventDefault(); submit(); }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
            placeholder={isStreaming ? "Processing..." : "Ask about your order, refund, or policy..."}
            className="flex-1 bg-elevated border border-border rounded-xl px-3.5 py-2.5 text-sm text-primary placeholder:text-dim focus:outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/15 transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="bg-gradient-to-br from-accent to-accent-2 text-white rounded-xl px-4 py-2.5 transition-all hover:shadow-lg hover:shadow-accent/30 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
