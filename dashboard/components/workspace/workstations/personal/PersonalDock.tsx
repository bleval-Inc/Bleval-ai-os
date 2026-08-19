"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { PERSONAL_VIEWS, type PersonalViewId } from "./personal-data";

interface PersonalDockProps {
  active: PersonalViewId;
  onSelect: (view: PersonalViewId) => void;
  containerRef: RefObject<HTMLDivElement | null>;
}

const DOCK_GLYPHS: Record<PersonalViewId, React.ReactNode> = {
  dashboard: <path d="M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z" />,
  yamako: <><circle cx="12" cy="12" r="3.2" /><circle cx="12" cy="12" r="7" opacity="0.5" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2" /></>,
  schedule: <><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18M8 15h3M8 18h2M14 15h3M14 18h2" /></>,
  learning: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /><path d="M9 7h6" /></>,
  rnd: <><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /><path d="M14.5 8.5l-2.6 3.8-1.4-1-2 2.4" /></>,
  progress: <><path d="M20 6L9 17l-5-5" /><circle cx="6" cy="18" r="2.4" /><circle cx="18" cy="6" r="2" /></>,
};

// Internal Personal dock. Destinations keep the Founder inside the Personal
// workstation — they are not global AXIOM workstations.
export function PersonalDock({ active, onSelect, containerRef }: PersonalDockProps) {
  const [visible, setVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const shownRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      shownRef.current = rect.bottom - e.clientY < 220;
      setVisible(rect.bottom - e.clientY < 220);
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
            aria-label="Personal internal navigation"
          >
            <div
              className={cn(
                "flex items-center gap-1 px-2.5 py-2 rounded-full backdrop-blur-xl border",
                "bg-[var(--axiom-bg-glass)] border-[var(--axiom-border-accent)]",
                "shadow-[0_8px_40px_-6px_rgba(0,0,0,0.5),0_0_40px_-8px_var(--axiom-accent-glow)]",
              )}
            >
              {PERSONAL_VIEWS.map((view) => {
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
                    style={isActive ? { background: "linear-gradient(135deg,#6d7cff,#a88cff)", boxShadow: "0 0 18px var(--axiom-accent-glow)" } : { background: "transparent" }}
                    aria-pressed={isActive}
                    aria-label={view.label}
                    title={view.label}
                  >
                    <span className="flex-shrink-0 flex items-center justify-center">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        {DOCK_GLYPHS[view.id]}
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