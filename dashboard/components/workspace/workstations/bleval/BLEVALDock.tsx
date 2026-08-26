"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { BLEVAL_VIEWS, type BlevalViewId } from "./bleval-ws-data";
import { type BaseIcon } from "./types";

function DockIcon({ name }: { name: BaseIcon }) {
  const common = { width: 16, height: 16, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "dashboard":
      return <svg {...common}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>;
    case "jenson":
      return <svg {...common}><path d="M12 8V4l8 8-8 8v-4" /><path d="M4 14h8" /><path d="M4 18h8" /></svg>;
    case "truth":
      return <svg {...common}><path d="M9 3h6v3h3v3h3v9h-3v3h-3v3H9v-3H6v-3H3V9h3V6h3z" /><circle cx="12" cy="12" r="2.5" /><path d="M12 7v3M12 14v3" /><path d="M7 12h3M14 12h3" /></svg>;
    case "acquisition":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /><path d="M14.5 8.5l-2.6 3.8-1.4-1-2 2.4" /></svg>;
    case "content":
      return <svg {...common}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="M8 13h8M8 17h5" /></svg>;
    case "clients":
      return <svg {...common}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>;
    case "operations":
      return <svg {...common}><circle cx="5" cy="12" r="2" /><circle cx="19" cy="12" r="2" /><path d="M7 12h10" /><path d="M12 7v10" /></svg>;
  }
}

interface BLEVALDockProps {
  active: BlevalViewId;
  onSelect: (view: BlevalViewId) => void;
  containerRef: RefObject<HTMLDivElement | null>;
}

export function BLEVALDock({ active, onSelect, containerRef }: BLEVALDockProps) {
  const [visible, setVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const shownRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const distanceFromBottom = rect.bottom - e.clientY;
      const nearBottom = distanceFromBottom < 200;
      shownRef.current = nearBottom;
      setVisible(nearBottom);
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

  const handleSelect = (view: BlevalViewId) => {
    onSelect(view);
  };

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
            aria-label="BLEVAL internal navigation"
          >
            <div
              className={cn(
                "flex items-center gap-1 px-2.5 py-2 rounded-full backdrop-blur-xl border",
                "bg-[var(--axiom-bg-glass)] border-[var(--axiom-border-accent)]",
                "shadow-[0_8px_40px_-6px_rgba(0,0,0,0.5),0_0_40px_-8px_var(--axiom-accent-glow)]",
              )}
            >
              {BLEVAL_VIEWS.map((view) => {
                const isActive = view.id === active;
                return (
                  <motion.button
                    key={view.id}
                    onClick={() => handleSelect(view.id)}
                    whileHover={{ scale: 1.08 }}
                    whileTap={{ scale: 0.94 }}
                    className={cn(
                      "relative flex items-center gap-2 rounded-full h-10 transition-all duration-200",
                      expanded ? "px-2.5 w-auto" : "px-2.5 w-10 justify-center",
                      isActive
                        ? "text-white"
                        : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)]",
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
                      <DockIcon name={view.icon} />
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