"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ThinkingIndicatorProps {
  state: string | null;
}

const THINKING_STATES = [
  "Initializing neural pathways…",
  "Consulting executive council…",
  "Synthesizing context…",
  "Evaluating constraints…",
  "Formulating response…",
  "Refining output…",
];

export default function ThinkingIndicator({ state }: ThinkingIndicatorProps) {
  const stateIndexRef = useRef(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    stateIndexRef.current = 0;
    intervalRef.current = setInterval(() => {
      stateIndexRef.current = (stateIndexRef.current + 1) % THINKING_STATES.length;
    }, 1200);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <div className="flex gap-4 max-w-4xl md:max-w-5xl lg:max-w-6xl mx-auto w-full">
      {/* AXIOM Avatar */}
      <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <div className="w-full h-full rounded-full flex items-center justify-center bg-gradient-to-br from-indigo-400 to-violet-500">
          <span className="text-[11px] font-bold text-white">A</span>
        </div>
      </div>

      <div className="flex-1">
        <div className="text-[var(--axiom-text-primary)] px-1 py-2">
          {/* Animated dots + state text */}
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  className="w-2 h-2 rounded-full bg-[var(--axiom-accent)]/60"
                  animate={{
                    y: [0, -6, 0],
                    opacity: [0.4, 1, 0.4],
                  }}
                  transition={{
                    duration: 0.6,
                    delay: i * 0.15,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
              ))}
            </div>

            {/* Current state text */}
            <motion.span
              key={state || "default"}
              className={cn(
                "text-sm md:text-base font-light text-[var(--axiom-text-secondary)]",
                "font-mono tracking-wide uppercase",
                "min-w-[200px]"
              )}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.3 }}
            >
              {state || THINKING_STATES[stateIndexRef.current]}
            </motion.span>
          </div>

          {/* Progress bar */}
          <motion.div
            className="mt-3 h-1 bg-[var(--axiom-bg-elevated)]/50 rounded-full overflow-hidden"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <motion.div
              className="h-full rounded-full"
              style={{
                background: "linear-gradient(90deg, var(--axiom-accent), var(--axiom-accent-secondary))",
              }}
              animate={{
                scaleX: [0, 1, 0],
                borderRadius: ["100% 0 0 100%", "0 100% 100% 0", "100% 0 0 100%"],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}