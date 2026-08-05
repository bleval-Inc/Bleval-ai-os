"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system, executives as execApi } from "../../../lib/api";
import CommandCenter from "../workspaces/CommandCenter";
import ExecutiveBoard from "../workspaces/ExecutiveBoard";
import OperationsCenter from "../workspaces/OperationsCenter";
import ProjectsWorkspace from "../workspaces/ProjectsWorkspace";
import CreatorStudio from "../workspaces/CreatorStudio";
import FounderConsole from "../workspaces/FounderConsole";
import CommunicationsHub from "../workspaces/CommunicationsHub";
import ContentHub from "../workspaces/ContentHub";
import CollaborationWorkspace from "../workspaces/CollaborationWorkspace";
import IntegrationsDashboard from "../workspaces/IntegrationsDashboard";
import IntelligenceCenter from "../workspaces/IntelligenceCenter";
import { ExecutiveGreetingPanel } from "../ExecutiveGreetingPanel";
import ExecutiveIntelligencePanel from "../ExecutiveIntelligencePanel";
import { InlineListeningIndicator } from "../ListeningIndicator";

type BLEVALTab = "overview" | "executives" | "operations" | "projects" | "creator" | "console" | "comms" | "content" | "collab" | "integrations" | "intel" | "intelligence";

const WORKSTATION_VIEWS: { id: BLEVALTab; label: string; shortcut: string }[] = [
  { id: "overview", label: "Overview", shortcut: "⌘⇧1" },
  { id: "executives", label: "Execs", shortcut: "⌘⇧2" },
  { id: "operations", label: "Ops", shortcut: "⌘⇧3" },
  { id: "projects", label: "Projects", shortcut: "⌘⇧4" },
  { id: "creator", label: "Creator", shortcut: "⌘⇧5" },
  { id: "console", label: "Console", shortcut: "⌘⇧6" },
  { id: "intel", label: "Intel", shortcut: "⌘⇧7" },
  { id: "comms", label: "Comms", shortcut: "⌘⇧8" },
  { id: "content", label: "Content", shortcut: "⌘⇧9" },
  { id: "collab", label: "Team", shortcut: "⌘⇧0" },
  { id: "integrations", label: "Integrations", shortcut: "⌥⇧1" },
  { id: "intelligence", label: "Learning", shortcut: "⌥⇧2" },
];

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

export default function BLEVALWS() {
  const { setWorkstationStatus, setActiveWorkstationView } = useAxiomStore();
  const [activeTab, setActiveTab] = useState<BLEVALTab>("overview");
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Poll executive board for Jenson status
  useEffect(() => {
    const poll = async () => {
      try {
        const board = await execApi.boardStatus();
        const jenson = board?.jenson?.status;
        if (jenson === "running") setWorkstationStatus("bleval", "healthy");
        else if (jenson === "error") setWorkstationStatus("bleval", "degraded");
        else setWorkstationStatus("bleval", "busy");
      } catch {
        setWorkstationStatus("bleval", "idle");
      }
    };
    poll();
    pollingRef.current = setInterval(poll, 15000);
    return () => clearInterval(pollingRef.current);
  }, [setWorkstationStatus]);

  // Update store view on tab switch
  useEffect(() => {
    const viewMap: Record<BLEVALTab, "executives" | "operations" | "projects" | "creator" | "console" | "communications" | "content-hub" | "collaboration" | "integrations" | "intelligence" | "workspace"> = {
      overview: "workspace",
      executives: "executives",
      operations: "operations",
      projects: "projects",
      creator: "creator",
      console: "console",
      intel: "intelligence",
      intelligence: "intelligence",
      comms: "communications",
      content: "content-hub",
      collab: "collaboration",
      integrations: "integrations",
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
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center">
                <span className="text-[7px] font-bold text-white">B</span>
              </div>
              <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)] tracking-wide">
                BLEVAL INC
              </h2>
              <span className="text-[10px] text-[var(--axiom-text-tertiary)] bg-[var(--axiom-bg-elevated)] px-1.5 py-0.5 rounded font-mono">
                Jenson
              </span>
            </div>
            {/* Listening indicator for Jenson */}
            <InlineListeningIndicator executive="jenson" />
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
              {activeTab === "overview" && <CommandCenter />}
              {activeTab === "executives" && <ExecutiveBoard />}
              {activeTab === "operations" && <OperationsCenter />}
              {activeTab === "projects" && <ProjectsWorkspace />}
              {activeTab === "creator" && <CreatorStudio />}
              {activeTab === "console" && <FounderConsole />}
              {activeTab === "intel" && <IntelligenceCenter />}
              {activeTab === "comms" && <CommunicationsHub />}
              {activeTab === "content" && <ContentHub />}
              {activeTab === "collab" && <CollaborationWorkspace />}
              {activeTab === "integrations" && <IntegrationsDashboard />}
              {activeTab === "intelligence" && <ExecutiveIntelligencePanel />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}