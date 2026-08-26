"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { TradingViewId } from "./valta/valta-data";
import { VALTADock } from "./valta/VALTADock";
import ValtaDashboard from "./valta/ValtaDashboard";
import TradingCalendar from "./valta/TradingCalendar";
import TradingJournal from "./valta/TradingJournal";
import Reports from "./valta/Reports";

// HOUSE OF VALTA — trading workstation managed by Valta Prime.
// Internal destinations (calendar, journal, reports) keep the user inside
// House of Valta; they are not global AXIOM workstations.
export default function VALTAWS() {
  const [view, setView] = useState<TradingViewId>("dashboard");
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={containerRef}
      className="relative flex-1 min-h-0 overflow-hidden bg-[var(--axiom-bg-base)]"
      style={{
        background:
          "radial-gradient(ellipse 70% 50% at 20% 0%, rgba(109,124,255,0.05), transparent 60%), radial-gradient(ellipse 50% 40% at 100% 100%, rgba(168,140,255,0.04), transparent 60%), var(--axiom-bg-base)",
      }}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={view}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
          className="absolute inset-0 overflow-y-auto hide-scrollbar"
        >
          <div className="min-h-full flex flex-col">
            {view === "dashboard" && <ValtaDashboard />}
            {view === "calendar" && <TradingCalendar />}
            {view === "journal" && <TradingJournal />}
            {view === "reports" && <Reports />}
          </div>
        </motion.div>
      </AnimatePresence>

      <VALTADock active={view} onSelect={setView} containerRef={containerRef} />
    </div>
  );
}