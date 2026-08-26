"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { TRADING_VIEWS, type TradingViewId } from "./valta-data";

interface VALTADockProps {
  active: TradingViewId;
  onSelect: (view: TradingViewId) => void;
  containerRef: RefObject<HTMLDivElement | null>;
}

// Internal House of Valta dock. Selecting a destination keeps the user inside
// House of Valta — these are internal workstations, not global AXIOM ones.
export function VALTADock({ active, onSelect, containerRef }: VALTADockProps) {
  const [visible, setVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const shownRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const distanceFromBottom = rect.bottom - e.clientY;
      shownRef.current = distanceFromBottom < 220;
      setVisible(distanceFromBottom < 220);
    };
    const onLeave = () => {
      shownRef.current = false;
      setVisible(false);
      setExpanded(false);
    };

    container.addEventListener("mousemove", onMove);
    container.addEventListener("mouseleave", onLeave);
    return () => {
      container.removeEventListener("mousemove", onMove);
      container.removeEventListener("mouseleave", onLeave);
    };
  }, [containerRef]);

  return (
    <div className="absolute left-0 right-0 bottom-0 z-30 flex justify-center pointer-events-none">
      <AnimatePresence>
        {visible && (
          <motion.div
            onMouseEnter={() => setExpanded(true)}
            onMouseLeave={() => setExpanded(false)}
            initial={{ opacity: 0, y: 24, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.92 }}
            transition={{ type: "spring", stiffness: 380, damping: 26 }}
            className="pointer-events-auto mb-6"
            aria-label="House of Valta internal navigation"
          >
            <div
              className={cn(
                "flex items-center gap-1 px-2.5 py-2 rounded-full backdrop-blur-xl border",
                "bg-[var(--axiom-bg-glass)] border-[var(--axiom-border-accent)]",
                "shadow-[0_8px_40px_-6px_rgba(0,0,0,0.5),0_0_40px_-8px_var(--axiom-accent-glow)]",
              )}
            >
              {TRADING_VIEWS.map((view) => {
                const isActive = view.id === active;
                return (
                  <motion.button
                    key={view.id}
                    onClick={() => onSelect(view.id)}
                    whileHover={{ scale: 1.08 }}
                    whileTap={{ scale: 0.94 }}
                    className={cn(
                      "relative flex items-center gap-2 rounded-full h-10 transition-all duration-200",
                      expanded ? "px-2.5 w-auto" : "px-2.5 w-10 justify-center",
                      isActive ? "text-white" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)]",
                    )}
                    style={
                      isActive
                        ? { background: "linear-gradient(135deg,#6d7cff,#a88cff)", boxShadow: "0 0 18px var(--axiom-accent-glow)" }
                        : { background: "transparent" }
                    }
                    aria-pressed={isActive}
                    aria-label={view.label}
                    title={view.label}
                  >
                    <span className="flex-shrink-0 flex items-center justify-center">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        {view.id === "dashboard" && <path d="M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z" />}
                        {view.id === "calendar" && <><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18M8 15h3M8 18h2M14 15h3M14 18h2" /></>}
                        {view.id === "journal" && <><path d="M6 3h9a4 4 0 0 1 4 4v14l-2-1.33L15 21l-2-1.33L11 21l-2-1.33L7 21l-2-1.33L4 21V7a4 4 0 0 1 4-4z" /><path d="M7 7h6M7 11h9M7 15h9" /></>}
                        {view.id === "reports" && <><path d="M3 3v18h18" /><path d="M7 15l3.5-3 2.5 2 5-6" /><path d="M7 9h2M7 12h1" /></>}
                      </svg>
                    </span>
                    {isActive && <span className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]" />}
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}