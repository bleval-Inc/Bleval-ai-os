"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type WorkstationId } from "../../../lib/store/axiom-store";
import { cn } from "../../../lib/utils";

const DOCK_WORKSTATIONS: WorkstationId[] = ["bleval", "valta", "personal"];

const WORKSTATION_CONFIG: Record<WorkstationId, { label: string; shortLabel: string; icon: React.ReactNode }> = {
  axiom: {
    label: "AXIOM",
    shortLabel: "AXIOM",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    ),
  },
  bleval: {
    label: "BLEVAL INC",
    shortLabel: "BLEVAL",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
  },
  valta: {
    label: "HOUSE OF VALTA",
    shortLabel: "VALTA",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12V7H5V2H1v5H1" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  personal: {
    label: "PERSONAL OPS",
    shortLabel: "PERSONAL",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  boardroom: {
    label: "EXECUTIVE BOARDROOM",
    shortLabel: "BOARDROOM",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  system: {
    label: "SYSTEM",
    shortLabel: "SYSTEM",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
    ),
  },
  settings: {
    label: "SETTINGS",
    shortLabel: "SETTINGS",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
};

export function Dock() {
  const { activeWorkstation, setActiveWorkstation } = useAxiomStore();
  const [visible, setVisible] = useState(false);
  const dockRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Only show dock in BLEVAL, VALTA, PERSONAL
  const showDock = DOCK_WORKSTATIONS.includes(activeWorkstation);

  if (!showDock) return null;

  // Auto-show when mouse near bottom, hide when leaving
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const distanceFromBottom = rect.bottom - e.clientY;
      // Show when within 100px of bottom
      setVisible(distanceFromBottom < 100);
    };

    const handleMouseLeave = () => {
      setVisible(false);
    };

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);
    return () => {
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-0 left-0 right-0 z-50 h-24 pointer-events-none"
      aria-label="Workstation Dock"
    >
      <AnimatePresence mode="wait">
        {visible && (
          <motion.div
            ref={dockRef}
            key="visible"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 28 }}
            className="flex justify-center pt-4 pointer-events-auto"
          >
            <div className={cn(
              "flex items-center gap-1 px-5 py-3 rounded-[50px] shadow-2xl backdrop-blur-xl border",
              "bg-[var(--axiom-bg-glass)] border-[var(--axiom-border-accent)]",
              "shadow-[0_0_40px_var(--axiom-accent-glow),0_8px_32px_-4px_rgba(0,0,0,0.4)]"
            )}>
              {DOCK_WORKSTATIONS.map((id) => {
                const config = WORKSTATION_CONFIG[id];
                const isActive = activeWorkstation === id;

                return (
                  <motion.button
                    key={id}
                    onClick={() => setActiveWorkstation(id)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className={cn(
                      "relative flex items-center justify-center w-11 h-11 rounded-xl transition-all duration-200",
                      isActive
                        ? "bg-gradient-to-br from-[var(--axiom-accent)] to-[var(--axiom-violet)] shadow-[0_0_20px_var(--axiom-accent-glow)]"
                        : "bg-transparent text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)] hover:bg-[var(--axiom-bg-elevated)]/50"
                    )}
                    aria-pressed={isActive}
                    aria-label={config.label}
                    style={{
                      boxShadow: isActive
                        ? "0 0 32px var(--axiom-accent-glow), 0 4px 16px -4px rgba(0,0,0,0.4)"
                        : "none"
                    }}
                  >
                    <div className="w-6 h-6 flex items-center justify-center overflow-hidden">
                      {config.icon}
                    </div>

                    {/* Active indicator — subtle dot */}
                    <AnimatePresence>
                      {isActive && (
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                          className="absolute -top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-white"
                        />
                      )}
                    </AnimatePresence>
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default Dock;