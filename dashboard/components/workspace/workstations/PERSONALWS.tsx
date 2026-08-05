"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { executives as execApi, learning } from "../../../lib/api";
import KnowledgeWorkspace from "../workspaces/KnowledgeWorkspace";
import IntelligenceCenter from "../workspaces/IntelligenceCenter";
import FounderConsole from "../workspaces/FounderConsole";
import CollaborationWorkspace from "../workspaces/CollaborationWorkspace";
import IntegrationsDashboard from "../workspaces/IntegrationsDashboard";
import CreatorStudio from "../workspaces/CreatorStudio";
import { ExecutiveGreetingPanel } from "../ExecutiveGreetingPanel";
import ExecutiveIntelligencePanel from "../ExecutiveIntelligencePanel";
import { InlineListeningIndicator } from "../ListeningIndicator";

type PERSONALTab = "knowledge" | "intel" | "schedule" | "habits" | "console" | "collab" | "integrations" | "creator" | "intelligence";

const WORKSTATION_VIEWS: { id: PERSONALTab; label: string; shortcut: string }[] = [
  { id: "knowledge", label: "Learn", shortcut: "⌘⇧L" },
  { id: "intel", label: "Intel", shortcut: "⌘⇧I" },
  { id: "schedule", label: "Schedule", shortcut: "⌘⇧S" },
  { id: "habits", label: "Habits", shortcut: "⌘⇧H" },
  { id: "console", label: "Console", shortcut: "⌘⇧C" },
  { id: "collab", label: "Team", shortcut: "⌘⇧T" },
  { id: "integrations", label: "Integrations", shortcut: "⌘⇧G" },
  { id: "creator", label: "Creator", shortcut: "⌘⇧R" },
  { id: "intelligence", label: "Learning", shortcut: "⌥⇧2" },
];

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

/* ── Habit Tracker mini component ──────────────────────────────────── */

function HabitTracker() {
  const [habits] = useState([
    { id: "1", label: "Morning review", done: true },
    { id: "2", label: "Read & learn", done: true },
    { id: "3", label: "Exercise", done: false },
    { id: "4", label: "Weekly planning", done: false },
  ]);

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-4">Daily Habits</h3>
      <div className="space-y-2">
        {habits.map((h) => (
          <label key={h.id} className="flex items-center gap-3 glass-panel px-4 py-3 rounded-xl cursor-pointer hover:bg-[var(--axiom-bg-elevated)] transition-colors">
            <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
              h.done
                ? "bg-emerald-500 border-emerald-500"
                : "border-[var(--axiom-border)]"
            }`}>
              {h.done && (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </div>
            <span className={`text-sm ${h.done ? "text-[var(--axiom-text-tertiary)] line-through" : "text-[var(--axiom-text-primary)]"}`}>
              {h.label}
            </span>
          </label>
        ))}
      </div>

      <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mt-8 mb-4">Weekly Goals</h3>
      <div className="glass-panel p-4 rounded-xl">
        <p className="text-xs text-[var(--axiom-text-tertiary)] mb-3">Plan your week ahead.</p>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Add a goal..."
            className="flex-1 bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] rounded-lg px-3 py-2 text-xs text-[var(--axiom-text-primary)] placeholder-[var(--axiom-text-tertiary)] outline-none focus:border-[var(--axiom-accent)] transition-colors"
          />
          <button className="px-3 py-2 text-xs font-medium text-white bg-[var(--axiom-accent)] rounded-lg hover:opacity-90 transition-opacity">
            Add
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Schedule view ─────────────────────────────────────────────────── */

function ScheduleView() {
  const hours = Array.from({ length: 12 }, (_, i) => i + 7); // 7am — 6pm
  const now = new Date();
  const currentHour = now.getHours();
  const currentMin = now.getMinutes();
  const dayName = now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-1">{dayName}</h3>
      <p className="text-[10px] text-[var(--axiom-text-tertiary)] mb-4">Daily timeline — powered by Yamako</p>
      <div className="relative space-y-0">
        {hours.map((h) => {
          const period = h >= 12 ? "PM" : "AM";
          const displayHour = h > 12 ? h - 12 : h;
          const isPast = h < currentHour || (h === currentHour && currentMin > 0);
          const isNow = h === currentHour;
          return (
            <div key={h} className="flex items-start gap-3 py-2 group">
              <div className="w-12 text-right">
                <span className={`text-[11px] font-mono tabular-nums ${
                  isNow ? "text-[var(--axiom-accent)] font-semibold" : "text-[var(--axiom-text-tertiary)]"
                }`}>
                  {displayHour}:00 {period}
                </span>
              </div>
              <div className={`flex-1 h-8 rounded-lg border ${
                isNow
                  ? "border-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                  : isPast
                    ? "border-[var(--axiom-border)] opacity-30"
                    : "border-[var(--axiom-border)] hover:bg-[var(--axiom-bg-elevated)]"
              } transition-colors cursor-pointer flex items-center px-3`}>
                {isNow && (
                  <span className="text-[10px] text-[var(--axiom-accent)] font-medium">Now</span>
                )}
                {!isNow && !isPast && (
                  <span className="text-[10px] text-[var(--axiom-text-tertiary)]">Available</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Main component ────────────────────────────────────────────────── */

export default function PERSONALWS() {
  const { setWorkstationStatus, setActiveWorkstationView } = useAxiomStore();
  const [activeTab, setActiveTab] = useState<PERSONALTab>("knowledge");
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Poll Yamako status for status dot
  useEffect(() => {
    const poll = async () => {
      try {
        const board = await execApi.boardStatus();
        const yamako = board?.yamako?.status;
        if (yamako === "running") setWorkstationStatus("personal", "healthy");
        else if (yamako === "error") setWorkstationStatus("personal", "degraded");
        else setWorkstationStatus("personal", "busy");
      } catch {
        setWorkstationStatus("personal", "idle");
      }
    };
    poll();
    pollingRef.current = setInterval(poll, 15000);
    return () => clearInterval(pollingRef.current);
  }, [setWorkstationStatus]);

  // Update store view on tab switch
  useEffect(() => {
    const viewMap: Record<PERSONALTab, "knowledge" | "intelligence" | "console" | "collaboration" | "integrations" | "creator" | "workspace"> = {
      knowledge: "knowledge",
      intel: "intelligence",
      intelligence: "intelligence",
      schedule: "knowledge",
      habits: "knowledge",
      console: "console",
      collab: "collaboration",
      integrations: "integrations",
      creator: "creator",
    };
    setActiveWorkstationView(viewMap[activeTab]);
  }, [activeTab, setActiveWorkstationView]);

  return (
    <div className="flex-1 flex">
      <div className="flex-1 flex flex-col min-w-0">
        {/* Executive Greeting Panel */}
        <ExecutiveGreetingPanel />

        {/* Workstation header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-violet-400 to-purple-600 flex items-center justify-center">
                <span className="text-[7px] font-bold text-white">P</span>
              </div>
              <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)] tracking-wide">
                PERSONAL OPS
              </h2>
              <span className="text-[10px] text-[var(--axiom-text-tertiary)] bg-[var(--axiom-bg-elevated)] px-1.5 py-0.5 rounded font-mono">
                Yamako
              </span>
            </div>
            {/* Listening indicator for Yamako */}
            <InlineListeningIndicator executive="yamako" />
          </div>

          {/* Tab navigation */}
          <div className="flex items-center gap-1">
            {WORKSTATION_VIEWS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all duration-150 ${
                  activeTab === tab.id
                    ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
                }`}
              >
                {tab.label}
                <span className="ml-1.5 text-[9px] opacity-40">{tab.shortcut}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 flex overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="flex-1 flex overflow-hidden"
            >
              {activeTab === "knowledge" && <KnowledgeWorkspace />}
              {activeTab === "intel" && <IntelligenceCenter />}
              {activeTab === "schedule" && <ScheduleView />}
              {activeTab === "habits" && <HabitTracker />}
              {activeTab === "console" && <FounderConsole />}
              {activeTab === "collab" && <CollaborationWorkspace />}
              {activeTab === "integrations" && <IntegrationsDashboard />}
              {activeTab === "creator" && <CreatorStudio />}
              {activeTab === "intelligence" && <ExecutiveIntelligencePanel />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}