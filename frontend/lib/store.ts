import { create } from 'zustand';
import { NexusEvent } from './types';

export type ChatMessage = {
  role: 'user' | 'agent';
  content: string;
  agent?: string;
  ts: string;
};

interface AppState {
  events: NexusEvent[];
  messages: ChatMessage[];
  currentRunId: string | null;
  isConnected: boolean;
  isStreaming: boolean;

  addEvent: (event: NexusEvent) => void;
  clearEvents: () => void;
  addMessage: (m: ChatMessage) => void;
  setConnected: (status: boolean) => void;
  setStreaming: (v: boolean) => void;
  setCurrentRunId: (id: string | null) => void;
  resetRun: () => void;
}

export const useStore = create<AppState>((set) => ({
  events: [],
  messages: [],
  currentRunId: null,
  isConnected: false,
  isStreaming: false,

  addEvent: (event) => set((state) => {
    // Auto-add final response to chat history
    if (event.type === 'final_response') {
      const text = (event.payload as any)?.text;
      const agent = (event.payload as any)?.agent;
      if (text) {
        return {
          events: [...state.events, event],
          messages: [...state.messages, {
            role: 'agent',
            content: text,
            agent: agent || 'Agent',
            ts: event.ts,
          }],
        };
      }
    }
    return { events: [...state.events, event] };
  }),

  clearEvents: () => set({ events: [] }),
  addMessage: (m) => set((state) => ({ messages: [...state.messages, m] })),
  setConnected: (status) => set({ isConnected: status }),
  setStreaming: (v) => set({ isStreaming: v }),
  setCurrentRunId: (id) => set({ currentRunId: id }),

  resetRun: () => set({ events: [], currentRunId: null, isConnected: false, isStreaming: false }),
}));
