"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system, executives as execApi } from "../../../lib/api";
import TradingTerminal from "../workspaces/TradingTerminal";
import OperationsCenter from "../workspaces/OperationsCenter";
import IntelligenceCenter from "../workspaces/IntelligenceCenter";
import KnowledgeWorkspace from "../workspaces/KnowledgeWorkspace";
import ContentHub from "../workspaces/ContentHub";
import CommunicationsHub from "../workspaces/CommunicationsHub";
import { ExecutiveGreetingPanel } from "../ExecutiveGreetingPanel";
import ExecutiveIntelligencePanel from "../ExecutiveIntelligencePanel";
import { InlineListeningIndicator } from "../ListeningIndicator";

type VALTATab = "markets" | "analysis" | "operations" | "intel" | "knowledge" | "content" | "comms" | "intelligence";

const WORKSTATION_VIEWS: { id: VALTATab; label: string; shortcut: string }[] = [
  { id: "markets", label: "Markets", shortcut: "⌘⇧M" },
  { id: "analysis", label: "Analysis", shortcut: "⌘⇧A" },
  { id: "operations", label: "Ops", shortcut: "⌘⇧O" },
  { id: "intel", label: "Intel", shortcut: "⌘⇧I" },
  { id: "knowledge", label: "Knowledge", shortcut: "⌘⇧K" },
  { id: "content", label: "Content", shortcut: "⌘⇧C" },
  { id: "comms", label: "Comms", shortcut: "⌘⇧S" },
  { id: "intelligence", label: "Learning", shortcut: "⌥⇧2" },
];

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

export default function VALTAWS() {
  const { setWorkstationStatus, setActiveWorkstationView } = useAxiomStore();
  const [activeTab, setActiveTab] = useState<VALTATab>("markets");
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Poll for Valta Prime status
  useEffect(() => {
    const poll = async () => {
      try {
        const board = await execApi.boardStatus();
        const valta = board?.valta_prime?.status;
        if (valta === "running") setWorkstationStatus("valta", "healthy");
        else if (valta === "error") setWorkstationStatus("valta", "degraded");
        else setWorkstationStatus("valta", "busy");
      } catch {
        setWorkstationStatus("valta", "idle");
      }
    };
    poll();
    pollingRef.current = setInterval(poll, 15000);
    return () => clearInterval(pollingRef.current);
  }, [setWorkstationStatus]);

  // Update store view on tab switch
  useEffect(() => {
    const viewMap: Record<VALTATab, "trading" | "operations" | "intelligence" | "knowledge" | "content-hub" | "communications"> = {
      markets: "trading",
      analysis: "trading",
      operations: "operations",
      intel: "intelligence",
      intelligence: "intelligence",
      knowledge: "knowledge",
      content: "content-hub",
      comms: "communications",
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
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
                <span className="text-[7px] font-bold text-white">V</span>
              </div>
              <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)] tracking-wide">
                HOUSE OF VALTA
              </h2>
              <span className="text-[10px] text-[var(--axiom-text-tertiary)] bg-[var(--axiom-bg-elevated)] px-1.5 py-0.5 rounded font-mono">
                Valta Prime
              </span>
            </div>
            {/* Listening indicator for Valta Prime */}
            <InlineListeningIndicator executive="valta_prime" />
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

        {/* ⚠️ Read-only alert banner */}
        <div className="px-6 py-1.5 text-[10px] text-amber-400/80 bg-amber-400/5 border-b border-amber-400/10 flex items-center gap-2">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span>Read-only market analysis. No trade execution available.</span>
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
              {activeTab === "markets" && <TradingTerminal />}
              {activeTab === "analysis" && (
                <div className="flex-1 p-6 overflow-y-auto">
                  <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-4">Trade Analysis</h3>
                  <div className="glass-panel p-6 rounded-xl text-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 text-[var(--axiom-text-tertiary)]">
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                    <p className="text-sm text-[var(--axiom-text-tertiary)]">Deep trade analysis loaded from Valta Prime's strategy engine.</p>
                  </div>
                </div>
              )}
              {activeTab === "operations" && <OperationsCenter />}
              {activeTab === "intel" && <IntelligenceCenter />}
              {activeTab === "knowledge" && <KnowledgeWorkspace />}
              {activeTab === "content" && <ContentHub />}
              {activeTab === "comms" && <CommunicationsHub />}
              {activeTab === "intelligence" && <ExecutiveIntelligencePanel />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}