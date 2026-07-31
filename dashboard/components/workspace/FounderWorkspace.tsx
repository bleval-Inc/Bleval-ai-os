"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type WorkspaceId } from "../../lib/store/axiom-store";
import { system } from "../../lib/api";
import WorkspaceSidebar from "./navigation/WorkspaceSidebar";
import Conversation from "./Conversation";
import MemorySidebar from "./MemorySidebar";
import CommandPalette from "./CommandPalette";
import ExecutiveBoard from "./workspaces/ExecutiveBoard";
import OperationsCenter from "./workspaces/OperationsCenter";
import KnowledgeWorkspace from "./workspaces/KnowledgeWorkspace";
import ProjectsWorkspace from "./workspaces/ProjectsWorkspace";
import CreatorStudio from "./workspaces/CreatorStudio";
import TradingTerminal from "./workspaces/TradingTerminal";
import FounderConsole from "./workspaces/FounderConsole";

/* ── Page transition variants ──────────────────────────────────────── */

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

/* ── Workspace 1: Founder (main workspace) ─────────────────────────── */

function FounderWorkspace() {
  const { sidePanel, setSidePanel, runtime, setRuntime } = useAxiomStore();
  const [canvasOpen, setCanvasOpen] = useState(false);
  const [canvasItems] = useState<
    { id: string; title: string; type: string; preview: string }[]
  >([]);

  // Fetch initial status
  useEffect(() => {
    const init = async () => {
      try {
        const status = await system.status();
        setRuntime(status);
      } catch {
        // Backend not available
      }
    };
    init();
  }, [setRuntime]);

  return (
    <div className="flex-1 flex">
      {/* Main workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Workspace header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-medium text-[var(--axiom-text-primary)]">
              Founder Workspace
            </h2>
            <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono">
              {runtime?.version ? `v${runtime.version}` : ""}
            </span>
          </div>

          <div className="flex items-center gap-1">
            {/* Canvas toggle */}
            <button
              onClick={() => setCanvasOpen(!canvasOpen)}
              className={`p-1.5 rounded-md transition-colors ${
                canvasOpen
                  ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
              }`}
              title="Toggle Canvas"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="3" y1="9" x2="21" y2="9" />
                <line x1="9" y1="21" x2="9" y2="9" />
              </svg>
            </button>

            {/* Memory sidebar toggle */}
            <button
              onClick={() => setSidePanel(sidePanel === "memory" ? "none" : "memory")}
              className={`p-1.5 rounded-md transition-colors ${
                sidePanel === "memory"
                  ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
              }`}
              title="Toggle Memory Sidebar"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 flex overflow-hidden">
          <Conversation />

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
                    <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] tracking-wide uppercase">
                      Canvas
                    </h3>
                    <button
                      onClick={() => setCanvasOpen(false)}
                      className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] transition-colors"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 6 6 18" />
                        <path d="m6 6 12 12" />
                      </svg>
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="space-y-3">
                      <p className="text-xs text-[var(--axiom-text-tertiary)]">
                        Generated items will appear here. Start a conversation to create artifacts.
                      </p>
                      {canvasItems.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] mb-3">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                            <line x1="3" y1="9" x2="21" y2="9" />
                            <line x1="9" y1="21" x2="9" y2="9" />
                          </svg>
                          <p className="text-sm text-[var(--axiom-text-tertiary)]">Empty canvas</p>
                          <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">
                            Responses with code, charts, or documents will appear here.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="px-4 py-3 border-t border-[var(--axiom-border)] flex gap-2 flex-wrap">
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Chart</button>
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Document</button>
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Code</button>
                    <button className="px-3 py-1.5 text-[11px] font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">+ Diagram</button>
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

/* ── Workspace Renderer ────────────────────────────────────────────── */

const WORKSPACE_MAP: Record<WorkspaceId, React.FC> = {
  workspace: FounderWorkspace,
  executives: ExecutiveBoard,
  operations: OperationsCenter,
  knowledge: KnowledgeWorkspace,
  projects: ProjectsWorkspace,
  creator: CreatorStudio,
  trading: TradingTerminal,
  console: FounderConsole,
};

export default function WorkspaceShell() {
  const activeView = useAxiomStore((s) => s.activeView);
  const W = WORKSPACE_MAP[activeView];

  return (
    <div className="flex-1 flex pt-10 h-screen overflow-hidden">
      <CommandPalette />
      <WorkspaceSidebar />

      {/* Workspace content area */}
      <div className="flex-1 flex overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeView}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="flex-1 flex overflow-hidden"
          >
            <W />
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}