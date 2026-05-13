"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useStore } from "@/lib/store";
import ChatPanel from "@/components/cockpit/ChatPanel";
import AgentFlowCanvas from "@/components/cockpit/AgentFlowCanvas";
import ReasoningTrace from "@/components/cockpit/ReasoningTrace";
import ActivityFeed from "@/components/cockpit/ActivityFeed";
import MetricsStrip from "@/components/cockpit/MetricsStrip";
import GuardrailBanner from "@/components/cockpit/GuardrailBanner";
import { Play, FastForward } from "lucide-react";

export default function ReplayPage() {
  const { id } = useParams();
  const [recordedEvents, setRecordedEvents] = useState<any[]>([]);
  const { clearEvents, addEvent } = useStore();
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (id) {
      api.getRunEvents(id as string).then(setRecordedEvents);
    }
  }, [id]);

  const handleReplay = async (speed: number) => {
    if (recordedEvents.length === 0) return;
    setIsPlaying(true);
    clearEvents();

    let lastTs = new Date(recordedEvents[0].ts).getTime();
    
    for (const e of recordedEvents) {
      const currentTs = new Date(e.ts).getTime();
      const delay = Math.max(0, currentTs - lastTs) / speed;
      if (delay > 0) {
        await new Promise(r => setTimeout(r, delay));
      }
      addEvent(e);
      lastTs = currentTs;
    }
    setIsPlaying(false);
  };

  return (
    <div className="h-full flex flex-col bg-base relative overflow-hidden">
      {/* Top Replay Bar */}
      <div className="h-14 border-b border-border bg-elevated/50 flex items-center px-6 justify-between z-20 shadow-md">
        <div className="flex items-center gap-3 font-mono text-sm">
          <span className="text-muted uppercase tracking-widest text-xs font-semibold">Replay Session</span>
          <span className="text-accent">{id}</span>
        </div>
        <div className="flex items-center gap-3">
          <button 
            disabled={isPlaying} 
            onClick={() => handleReplay(1)}
            className="flex items-center gap-2 bg-panel border border-border hover:bg-elevated px-4 py-1.5 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4 text-success" /> Replay 1x
          </button>
          <button 
            disabled={isPlaying} 
            onClick={() => handleReplay(4)}
            className="flex items-center gap-2 bg-panel border border-border hover:bg-elevated px-4 py-1.5 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            <FastForward className="w-4 h-4 text-warning" /> Replay 4x
          </button>
        </div>
      </div>

      <GuardrailBanner />
      
      <div className="flex-1 flex relative">
        <div className="w-[28%] border-r border-border bg-base flex flex-col relative z-10">
          <div className="h-12 border-b border-border flex items-center justify-between px-4 bg-panel">
            <h2 className="font-medium text-sm text-primary flex items-center gap-2">Customer Chat</h2>
          </div>
          {/* Readonly chat panel simulation */}
          <div className="flex-1 overflow-hidden pointer-events-none opacity-90">
             <ChatPanel onSendMessage={() => {}} isStreaming={false} />
          </div>
        </div>

        <div className="w-[44%] border-r border-border bg-panel flex flex-col relative z-0">
          <div className="h-[40%] min-h-[300px] border-b border-border relative overflow-hidden bg-gradient-to-b from-elevated/50 to-transparent">
            <AgentFlowCanvas />
          </div>
          <div className="flex-1 overflow-hidden flex flex-col">
            <ReasoningTrace />
          </div>
        </div>

        <div className="w-[28%] bg-base flex flex-col relative z-10">
          <div className="p-4 border-b border-border bg-elevated/20">
            <MetricsStrip />
          </div>
          <ActivityFeed />
        </div>
      </div>
    </div>
  );
}
