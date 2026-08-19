"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PersonalViewId } from "./personal/personal-data";
import { PersonalDock } from "./personal/PersonalDock";
import PersonalDashboard from "./personal/PersonalDashboard";
import YamakoAI from "./personal/YamakoAI";
import Schedule from "./personal/Schedule";
import Learning from "./personal/Learning";
import Rnd from "./personal/Rnd";
import Progress from "./personal/Progress";

// PERSONAL — the Founder's private operating environment, coordinated by Yamako.
// All internal destinations stay inside the Personal workstation.
export default function PERSONALWS() {
  const [view, setView] = useState<PersonalViewId>("dashboard");
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={containerRef}
      className="relative flex-1 min-h-0 overflow-hidden bg-[var(--axiom-bg-base)]"
      style={{
        background:
          "radial-gradient(ellipse 70% 50% at 10% 0%, rgba(45,212,191,0.05), transparent 60%), radial-gradient(ellipse 50% 40% at 100% 100%, rgba(109,124,255,0.05), transparent 60%), var(--axiom-bg-base)",
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
            {view === "dashboard" && <PersonalDashboard />}
            {view === "yamako" && <YamakoAI />}
            {view === "schedule" && <Schedule />}
            {view === "learning" && <Learning />}
            {view === "rnd" && <Rnd />}
            {view === "progress" && <Progress />}
          </div>
        </motion.div>
      </AnimatePresence>

      <PersonalDock active={view} onSelect={setView} containerRef={containerRef} />
    </div>
  );
}