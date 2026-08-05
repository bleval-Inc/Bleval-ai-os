"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system, axiom as axiomApi } from "../../../lib/api";
import Conversation from "../Conversation";
import ResearchWorkspaceView from "../workspaces/ResearchWorkspaceView";
import ContentHub from "../workspaces/ContentHub";
import CommunicationsHub from "../workspaces/CommunicationsHub";
import MemorySidebar from "../MemorySidebar";
import AXIOMWorkspace from "../workspaces/AXIOMWorkspace";
import BoardRoomPanel from "../BoardRoomPanel";
import { ExecutiveGreetingPanel } from "../ExecutiveGreetingPanel";
import { InlineListeningIndicator } from "../ListeningIndicator";

type AXIOMTab = "chat" | "research" | "axiom" | "board" | "canvas" | "system" | "content" | "comms";

const WORKSTATION_VIEWS: { id: AXIOMTab; label: string; shortcut: string }[] = [
  { id: "chat", label: "Chat", shortcut: "⌘⇧C" },
  { id: "research", label: "Research", shortcut: "⌘⇧R" },
  { id: "axiom", label: "AXIOM", shortcut: "⌘⇧A" },
  { id: "board", label: "Board", shortcut: "⌘⇧B" },
  { id: "canvas", label: "Canvas", shortcut: "⌘⇧V" },
  { id: "system", label: "System", shortcut: "⌘⇧S" },
  { id: "content", label: "Content", shortcut: "⌘⇧O" },
  { id: "comms", label: "Comms", shortcut: "⌘⇧M" },
];

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

export default function AXIOMWS() {
  const { setWorkstationStatus, setActiveWorkstationView, sidePanel, setSidePanel } =
    useAxiomStore();
  const [activeTab, setActiveTab] = useState<AXIOMTab>("chat");
  const [canvasOpen, setCanvasOpen] = useState(false);
  const [canvasItems] = useState<{ id: string; title: string; type: string; preview: string }[]>([]);
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Poll AXIOM awareness for status dot
  useEffect(() => {
    const poll = async () => {
      try {
        const awareness = await axiomApi.awareness();
        setWorkstationStatus("axiom", awareness?.state === "running" ? "healthy" : "busy");
      } catch {
        setWorkstationStatus("axiom", "idle");
      }
    };
    poll();
    pollingRef.current = setInterval(poll, 15000);
    return () => clearInterval(pollingRef.current);
  }, [setWorkstationStatus]);

  // Update store view on tab switch
  useEffect(() => {
    const viewMap: Record<AXIOMTab, "workspace" | "research" | "axiom-workspace" | "content-hub" | "communications"> = {
      chat: "workspace",
      research: "research",
      axiom: "axiom-workspace",
      board: "workspace",
      canvas: "workspace",
      system: "workspace",
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
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center">
                <span className="text-[8px] font-bold text-white">A</span>
              </div>
              <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)] tracking-wide">
                AXIOM
              </h2>
              <span className="text-[10px] text-[var(--axiom-text-tertiary)] bg-[var(--axiom-bg-elevated)] px-1.5 py-0.5 rounded font-mono">
                Primary
              </span>
            </div>
            {/* Listening indicator for AXIOM */}
            <InlineListeningIndicator executive="axiom" />
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
            {/* Canvas toggle */}
            <div className="w-px h-4 mx-1 bg-[var(--axiom-border)]" />
            <button
              onClick={() => setCanvasOpen(!canvasOpen)}
              className={`p-1.5 rounded-md transition-colors ${
                canvasOpen
                  ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
              }`}
              title="Toggle Canvas"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="3" y1="9" x2="21" y2="9" />
                <line x1="9" y1="21" x2="9" y2="9" />
              </svg>
            </button>
            <button
              onClick={() => setSidePanel(sidePanel === "memory" ? "none" : "memory")}
              className={`p-1.5 rounded-md transition-colors ${
                sidePanel === "memory"
                  ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
              }`}
              title="Toggle Memory Sidebar"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </button>
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
              {activeTab === "chat" && <Conversation />}
              {activeTab === "research" && <ResearchWorkspaceView />}
              {activeTab === "axiom" && <AXIOMWorkspace />}
              {activeTab === "board" && <BoardRoomPanel />}
              {activeTab === "content" && <ContentHub />}
              {activeTab === "comms" && <CommunicationsHub />}
              {activeTab === "canvas" && (
                <div className="flex-1 p-8 flex flex-col items-center justify-center">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] mb-4">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                    <line x1="3" y1="9" x2="21" y2="9" />
                    <line x1="9" y1="21" x2="9" y2="9" />
                  </svg>
                  <p className="text-sm text-[var(--axiom-text-tertiary)]">Canvas workspace</p>
                  <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">
                    Code, charts, and documents will appear here.
                  </p>
                </div>
              )}
              {activeTab === "system" && (
                <div className="flex-1 p-6 overflow-y-auto">
                  <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-4">System Status</h3>
                  <div className="glass-panel p-4 rounded-xl">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="text-sm text-[var(--axiom-text-primary)]">All systems operational</span>
                    </div>
                    <p className="text-xs text-[var(--axiom-text-tertiary)]">Polling runtime, health, and executive status every 15s.</p>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="glass-panel p-4 rounded-xl">
                      <span className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">Memory</span>
                      <p className="text-lg font-semibold text-[var(--axiom-text-primary)] mt-1">Online</p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl">
                      <span className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">Workflows</span>
                      <p className="text-lg font-semibold text-[var(--axiom-text-primary)] mt-1">Active</p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl">
                      <span className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">QC Manager</span>
                      <p className="text-lg font-semibold text-[var(--axiom-text-primary)] mt-1">Ready</p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl">
                      <span className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">Founder Gateway</span>
                      <p className="text-lg font-semibold text-[var(--axiom-text-primary)] mt-1">Active</p>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Canvas (right side panel) */}
          <AnimatePresence>
            {canvasOpen && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 400, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeOut" as const }}
                className="border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-hidden flex-shrink-0"
              >
                <div className="w-[400px] h-full flex flex-col">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--axiom-border)]">
                    <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] tracking-wide uppercase">Canvas</h3>
                    <button
                      onClick={() => setCanvasOpen(false)}
                      className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] transition-colors"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 6 6 18" /><path d="m6 6 12 12" />
                      </svg>
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="space-y-3">
                      <p className="text-xs text-[var(--axiom-text-tertiary)]">Generated items will appear here.</p>
                      {canvasItems.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] mb-3">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" />
                          </svg>
                          <p className="text-sm text-[var(--axiom-text-tertiary)]">Empty canvas</p>
                          <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">Responses with code, charts, or documents will appear here.</p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="px-4 py-3 border-t border-[var(--axiom-border)] flex gap-2 flex-wrap">
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Chart</button>
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Document</button>
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Code</button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      <MemorySidebar />
    </div>
  );
}