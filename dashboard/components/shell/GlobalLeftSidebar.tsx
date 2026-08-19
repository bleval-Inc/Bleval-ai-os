"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAxiomStore, type WorkspaceId, type WorkstationId } from "../../lib/store/axiom-store";
import { cn } from "../../lib/utils";

// Only the primary navigation items per spec
const GLOBAL_NAV_ITEMS: { id: WorkspaceId | WorkstationId; label: string; shortLabel: string; shortcut: string; icon: React.ReactNode }[] = [
  {
    id: "workspace",
    label: "HOME",
    shortLabel: "HOME",
    shortcut: "⌘1",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    id: "bleval",
    label: "BLEVAL",
    shortLabel: "BLEVAL",
    shortcut: "⌘2",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
  },
  {
    id: "valta",
    label: "HOUSE OF VALTA",
    shortLabel: "VALTA",
    shortcut: "⌘3",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12V7H5V2H1v5H1" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    id: "personal",
    label: "PERSONAL",
    shortLabel: "PERSONAL",
    shortcut: "⌘4",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    id: "boardroom",
    label: "BOARDROOM",
    shortLabel: "BOARDROOM",
    shortcut: "⌘B",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    id: "system",
    label: "SYSTEM",
    shortLabel: "SYSTEM",
    shortcut: "⌘5",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
    ),
  },
] as const;

export function GlobalLeftSidebar() {
  const router = useRouter();
  const { activeView, setActiveView, activeWorkstation, setActiveWorkstation, sidebarCollapsed, setSidebarCollapsed } = useAxiomStore();

  // Determine if current view matches a global nav item
  const isItemActive = (itemId: string) => {
    return activeView === itemId || activeWorkstation === itemId;
  };

  return (
    <div
      className={cn(
        "relative z-30 flex flex-col flex-shrink-0",
        "bg-[var(--axiom-bg-surface)]/70 backdrop-blur-xl border-r border-[var(--axiom-border)]/50",
        "transition-all duration-300 ease-out",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
      aria-label="Global navigation"
    >
      {/* Navigation Items */}
      <nav className="flex-1 flex flex-col items-center pt-4 pb-6 gap-0.5 overflow-y-auto" role="navigation" aria-label="Main navigation">
        {GLOBAL_NAV_ITEMS.map((item) => {
          const isActive = isItemActive(item.id);

          return (
            <div key={item.id} className="relative group w-full px-2">
              <button
                onClick={() => {
                  // Handle workstation switches vs view switches
                  if (item.id === "workspace") {
                    // HOME is the dashboard route, not a workstation. Navigate back to it
                    // and reset the store to a valid workstation id (this also avoids the
                    // invalid "workspace" key that used to trigger React error #130).
                    router.push("/");
                    setActiveView("workspace");
                    setActiveWorkstation("axiom");
                  } else if (item.id === "boardroom" || item.id === "system") {
                    setActiveWorkstation(item.id as WorkstationId);
                    setActiveView(item.id);
                  } else {
                    setActiveWorkstation(item.id as WorkstationId);
                    setActiveView("workspace");
                  }
                }}
                className={cn(
                  "relative w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--axiom-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--axiom-bg-surface)]",
                  isActive
                    ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]/50"
                )}
                title={sidebarCollapsed ? item.label : ""}
                aria-label={item.label}
                aria-current={isActive ? "page" : undefined}
              >
                {/* Icon */}
                <div className={cn("flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg", isActive && "bg-[var(--axiom-accent)]/10")}>
                  {item.icon}
                </div>

                {/* Label + Shortcut (hidden when collapsed) */}
                <div className={cn("flex-1 min-w-0 text-left overflow-hidden", sidebarCollapsed ? "opacity-0 w-0 pointer-events-none" : "opacity-100")}>
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-medium truncate">{item.label}</span>
                    <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] opacity-60 whitespace-nowrap">{item.shortcut}</span>
                  </div>
                </div>
              </button>

              {/* Active Indicator (animated bar on left) */}
              <AnimatePresence>
                {isActive && (
                  <motion.div
                    layoutId="global-nav-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-[var(--axiom-accent)]"
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    aria-hidden="true"
                  />
                )}
              </AnimatePresence>

              {/* Tooltip when collapsed */}
              {sidebarCollapsed && (
                <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-50">
                  <motion.div
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-panel px-3 py-2 whitespace-nowrap shadow-lg rounded-lg"
                  >
                    <span className="text-sm font-medium text-[var(--axiom-text-primary)]">{item.label}</span>
                    <span className="ml-2 text-[10px] font-mono text-[var(--axiom-text-tertiary)]">{item.shortcut}</span>
                  </motion.div>
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Bottom: Collapse Toggle */}
      <div className="flex flex-col items-center gap-3 pb-4 px-2 border-t border-[var(--axiom-border)]/50">
        {/* Collapse/Expand Toggle */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className={cn(
            "relative flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200",
            "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]/50",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--axiom-accent)]"
          )}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!sidebarCollapsed}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("transition-transform duration-200", sidebarCollapsed && "rotate-180")}
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default GlobalLeftSidebar;