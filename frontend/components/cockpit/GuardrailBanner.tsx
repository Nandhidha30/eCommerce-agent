"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useStore } from "@/lib/store";
import { useState, useEffect } from "react";
import { AlertTriangle } from "lucide-react";

export default function GuardrailBanner() {
  const events = useStore(state => state.events);
  const [violation, setViolation] = useState<any>(null);

  useEffect(() => {
    const lastEvent = events[events.length - 1];
    if (lastEvent?.type === "guardrail_violation") {
      setViolation(lastEvent);
      const t = setTimeout(() => setViolation(null), 4000);
      return () => clearTimeout(t);
    }
  }, [events]);

  return (
    <AnimatePresence>
      {violation && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          className="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-danger text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 font-semibold text-sm border-2 border-danger/50"
        >
          <AlertTriangle className="w-5 h-5 animate-pulse" />
          GUARDRAIL TRIGGERED · {violation.payload.guardrail.toUpperCase()} · {violation.payload.action.toUpperCase()}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
