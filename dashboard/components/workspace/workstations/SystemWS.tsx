"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Segmented } from "./settings/settings-ui";
import SystemOverview from "./system/SystemOverview";
import SystemTelemetryView from "./system/SystemTelemetryView";
import SettingsWS from "./SettingsWS";

// SYSTEM — the unified AXIOM OS control centre. Consolidates the System
// Overview (OS health / runtime visibility), Telemetry, and the Settings
// configuration surface into one workstation. All destinations stay inside
// SYSTEM; there is no separate Settings workstation any more.

type SystemTab = "Overview" | "Telemetry" | "Settings";
const TABS: readonly SystemTab[] = ["Overview", "Telemetry", "Settings"];

export default function SystemWS() {
  const [tab, setTab] = useState<SystemTab>("Overview");

  return (
    <div
      className="relative flex-1 min-h-0 overflow-hidden flex flex-col bg-[var(--axiom-bg-base)]"
      style={{
        background:
          "radial-gradient(ellipse 60% 45% at 0% 0%, rgba(109,124,255,0.05), transparent 60%), radial-gradient(ellipse 45% 40% at 100% 100%, rgba(168,140,255,0.05), transparent 60%), var(--axiom-bg-base)",
      }}
    >
      {/* Header — identity + tab switcher */}
      <header className="flex items-center justify-between gap-4 px-5 h-14 border-b flex-shrink-0" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
        <div className="flex items-center gap-3 min-w-0">
          <div className="text-[11px] font-semibold tracking-[0.14em] text-[var(--axiom-text-primary)] uppercase flex-shrink-0">SYSTEM</div>
          <span className="hidden sm:block text-[10px] text-[var(--axiom-text-tertiary)] truncate">AXIOM control centre</span>
        </div>
        <div className="flex-shrink-0">
          <Segmented options={TABS} value={tab} onValue={setTab} />
        </div>
      </header>

      {/* Content — switches between the three control-centre areas */}
      <div className="relative flex-1 min-h-0 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className={cn("absolute inset-0", tab === "Settings" ? "flex flex-col overflow-hidden" : "overflow-y-auto hide-scrollbar p-5 md:p-7 pb-24")}
          >
            {tab === "Overview" && <SystemOverview />}
            {tab === "Telemetry" && <SystemTelemetryView />}
            {tab === "Settings" && <SettingsWS />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}