import { useEffect, useRef } from 'react';
import { useStore } from './store';
import { NexusEvent } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function useSSE(sessionId: string | null) {
  const addEvent = useStore((s) => s.addEvent);
  const setConnected = useStore((s) => s.setConnected);
  const setStreaming = useStore((s) => s.setStreaming);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // Close any prior connection
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }

    const es = new EventSource(`${API_BASE}/events/${sessionId}`);
    esRef.current = es;
    setStreaming(true);

    es.onopen = () => setConnected(true);

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'heartbeat' || data.type === 'connected') return;
        addEvent(data as NexusEvent);
        if (data.type === 'run_completed') {
          es.close();
          setConnected(false);
          setStreaming(false);
        }
      } catch (err) {
        console.error('SSE parse error', err);
      }
    };

    es.onerror = () => {
      // Only close if it's actually closed; EventSource auto-retries
      if (es.readyState === EventSource.CLOSED) {
        setConnected(false);
        setStreaming(false);
      }
    };

    return () => {
      es.close();
      setConnected(false);
      setStreaming(false);
    };
  }, [sessionId, addEvent, setConnected, setStreaming]);
}

/**
 * Open an SSE stream and resolve when the 'connected' event arrives.
 * Use this when you must guarantee the listener is registered before POSTing /chat.
 */
export function openSSEAndWait(sessionId: string, onEvent: (e: NexusEvent) => void): Promise<EventSource> {
  return new Promise((resolve, reject) => {
    const es = new EventSource(`${API_BASE}/events/${sessionId}`);
    let connected = false;

    const timeout = setTimeout(() => {
      if (!connected) {
        es.close();
        reject(new Error('SSE connect timeout'));
      }
    }, 5000);

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'connected') {
          connected = true;
          clearTimeout(timeout);
          resolve(es);
          return;
        }
        if (data.type === 'heartbeat') return;
        onEvent(data as NexusEvent);
      } catch (err) {
        console.error('SSE parse error', err);
      }
    };

    es.onerror = () => {
      if (!connected) {
        clearTimeout(timeout);
        reject(new Error('SSE failed to open'));
      }
    };
  });
}
