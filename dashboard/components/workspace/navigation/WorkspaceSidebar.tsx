"use client";

import { motion } from "framer-motion";
import { useAxiomStore, type WorkspaceId } from "../../../lib/store/axiom-store";

/* ── Icon components (inline SVG, no lucide dependency in this file) ── */

const ICONS: Record<string, React.ReactNode> = {
  workspace: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
    </svg>
  ),
  executives: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  operations: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
  knowledge: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4Z" />
      <path d="M2 22v-2a6 6 0 0 1 6-6h8a6 6 0 0 1 6 6v2" />
    </svg>
  ),
  projects: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
    </svg>
  ),
  creator: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="13.5" cy="6.5" r="0.5" />
      <path d="M17 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h8" />
      <path d="M18 17V3l4 2.5-4 2.5" />
    </svg>
  ),
  trading: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="12" x2="2" y2="12" />
      <polyline points="12 2 2 12 12 22" />
    </svg>
  ),
  console: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  communications: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="8" y1="9" x2="16" y2="9" />
      <line x1="8" y1="13" x2="14" y2="13" />
    </svg>
  ),
  intelligence: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  "content-hub": (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  ),
  integrations: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  collaboration: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  "axiom-workspace": (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
  research: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
};

const WORKSPACE_LABELS: Record<string, { label: string; shortcut: string }> = {
  workspace: { label: "Founder", shortcut: "⌘1" },
  executives: { label: "Exec Board", shortcut: "⌘2" },
  operations: { label: "Operations", shortcut: "⌘3" },
  knowledge: { label: "Knowledge", shortcut: "⌘4" },
  projects: { label: "Projects", shortcut: "⌘5" },
  creator: { label: "Creator", shortcut: "⌘6" },
  trading: { label: "Trading", shortcut: "⌘7" },
  console: { label: "Console", shortcut: "⌘8" },
  communications: { label: "Inbox", shortcut: "⌘9" },
  intelligence: { label: "Intel", shortcut: "⌘0" },
  "content-hub": { label: "Content", shortcut: "⌥1" },
  integrations: { label: "Integrations", shortcut: "⌥2" },
  collaboration: { label: "Team", shortcut: "⌥3" },
  "axiom-workspace": { label: "AXIOM", shortcut: "⌥4" },
  research: { label: "Research", shortcut: "⌥5" },
};

const ORDER: WorkspaceId[] = [
  "workspace",
  "executives",
  "operations",
  "knowledge",
  "projects",
  "creator",
  "trading",
  "console",
  "communications",
  "intelligence",
  "content-hub",
  "integrations",
  "collaboration",
  "axiom-workspace",
  "research",
];

export default function WorkspaceSidebar() {
  const { activeView, setActiveView, sidebarCollapsed, setSidebarCollapsed } =
    useAxiomStore();

  return (
    <div
      className={`flex flex-col items-center bg-[var(--axiom-bg-surface)] border-r border-[var(--axiom-border)] transition-all duration-200 ${
        sidebarCollapsed ? "w-12" : "w-12"
      }`}
      style={{ paddingTop: 0 }}
    >
      {/* Workspace icons */}
      <div className="flex flex-col items-center gap-1 pt-3">
        {ORDER.map((id, index) => {
          const isActive = activeView === id;
          const { label, shortcut } = WORKSPACE_LABELS[id];

          return (
            <div key={id} className="relative group">
              <button
                onClick={() => setActiveView(id)}
                className={`flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-150 ${
                  isActive
                    ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
                }`}
              >
                {ICONS[id]}
              </button>

              {/* Active indicator dot */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute -left-[6px] top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full bg-[var(--axiom-accent)]"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}

              {/* Tooltip — appears on hover to the right */}
              <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-50">
                <div className="glass-panel px-2.5 py-1.5 whitespace-nowrap">
                  <span className="text-xs font-medium text-[var(--axiom-text-primary)]">
                    {label}
                  </span>
                  <span className="ml-2 text-[10px] text-[var(--axiom-text-tertiary)] font-mono">
                    {shortcut}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Bottom: settings icon */}
      <div className="relative group pb-3">
        <button
          onClick={() => setActiveView("console")}
          className={`flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-150 ${
            activeView === "console"
              ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
              : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
          }`}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
          </svg>
        </button>
        <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-50">
          <div className="glass-panel px-2.5 py-1.5 whitespace-nowrap">
            <span className="text-xs font-medium text-[var(--axiom-text-primary)]">
              Console
            </span>
            <span className="ml-2 text-[10px] text-[var(--axiom-text-tertiary)] font-mono">
              ⌘8
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}