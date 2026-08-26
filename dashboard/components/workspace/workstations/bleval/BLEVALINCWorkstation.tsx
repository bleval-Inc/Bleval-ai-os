"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { type BlevalViewId } from "./bleval-ws-data";
import { BLEVALDock } from "./BLEVALDock";
import BlevalDashboard from "./BlevalDashboard";
import JensonWorkstation from "./JensonWorkstation";
import TruthEngine from "./TruthEngine";
import Acquisition from "./Acquisition";
import ContentStudio from "./ContentStudio";
import Clients from "./Clients";
import Operations from "./Operations";

export default function BLEVALINCWorkstation() {
  const [view, setView] = useState<BlevalViewId>("dashboard");
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div ref={containerRef} className="relative flex-1 min-h-0 overflow-hidden bg-[var(--axiom-bg-base)]">
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
            {view === "dashboard" && <BlevalDashboard onOpenJenson={() => setView("jenson")} />}
            {view === "jenson" && <JensonWorkstation />}
            {view === "truth" && <TruthEngine />}
            {view === "acquisition" && <Acquisition />}
            {view === "content" && <ContentStudio />}
            {view === "clients" && <Clients />}
            {view === "operations" && <Operations />}
          </div>
        </motion.div>
      </AnimatePresence>

      <BLEVALDock active={view} onSelect={setView} containerRef={containerRef} />
    </div>
  );
}