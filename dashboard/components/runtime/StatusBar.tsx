"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type WorkstationId } from "../../lib/store/axiom-store";
import { system, executives as execApi } from "../../lib/api";
import { healthDotColor, formatTimestamp } from "../../lib/utils";
import NotificationCenter from "../workspace/NotificationCenter";
import type { FounderAvailability } from "../../lib/api-types";

// Workstation nav

const workstationNavItems: { id: WorkstationId; label: string; shortcut: string }[] = [
  { id: "axiom", label: "AXIOM", shortcut: "⌘1" },
  { id: "bleval", label: "BLEVAL INC", shortcut: "⌘2" },
  { id: "valta", label: "HOUSE OF VALTA", shortcut: "⌘3" },
  { id: "personal", label: "PERSONAL", shortcut: "⌘4" },
];

const statusDotColor: Record<string, string> = {
  healthy: "bg-emerald-400",
  degraded: "bg-amber-400",
  busy: "bg-blue-400",
  idle: "bg-[var(--axiom-text-tertiary)]",
};

// Availability display config
const AVAILABILITY_CONFIG: Record<FounderAvailability, { label: string; color: string; dot: string }> = {
  available: { label: "Available", color: "text-emerald-400", dot: "bg-emerald-400" },
  in_meeting: { label: "In Meeting", color: "text-amber-400", dot: "bg-amber-400" },
  in_trade: { label: "Trading", color: "text-blue-400", dot: "bg-blue-400" },
  sleeping: { label: "Sleeping", color: "text-violet-400", dot: "bg-violet-400" },
  training: { label: "Training", color: "text-orange-400", dot: "bg-orange-400" },
  studying: { label: "Studying", color: "text-cyan-400", dot: "bg-cyan-400" },
  do_not_disturb: { label: "DND", color: "text-red-400", dot: "bg-red-400" },
  unknown: { label: "Unknown", color: "text-gray-400", dot: "bg-gray-400" },
};

// WorkstationNavItem

function WorkstationNavItem({ id, label, shortcut }: { id: WorkstationId; label: string; shortcut: string }) {
  const activeWorkstation = useAxiomStore((s) => s.activeWorkstation);
  const setActiveWorkstation = useAxiomStore((s) => s.setActiveWorkstation);
  const workstationStatus = useAxiomStore((s) => s.workstationStatus[id]);
  const isActive = activeWorkstation === id;

  return (
    <button
      onClick={() => setActiveWorkstation(id)}
      className={`flex items-center gap-2 px-3 py-1.5 text-[11px] font-medium rounded-md transition-all duration-150 ${
        isActive
          ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
          : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${statusDotColor[workstationStatus] || "bg-[var(--axiom-text-tertiary)]"} ${
        workstationStatus === "degraded" ? "animate-pulse" : ""
      }`} />
      <span>{label}</span>
      <span className="ml-1 text-[9px] opacity-40">{shortcut}</span>
    </button>
  );
}

// AvailabilityDot

function AvailabilityDot() {
  const availability = useAxiomStore((s) => s.founderAvailability);
  const config = AVAILABILITY_CONFIG[availability] ?? AVAILABILITY_CONFIG.unknown;

  return (
    <div className="flex items-center gap-1.5" title={`Founder: ${config.label}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      <span className={`text-[10px] hidden sm:inline ${config.color}`}>{config.label}</span>
    </div>
  );
}

// DNDToggle

function DNDToggle() {
  const founderManualOverride = useAxiomStore((s) => s.founderManualOverride);
  const setFounderManualOverride = useAxiomStore((s) => s.setFounderManualOverride);
  const isDnd = founderManualOverride === "do_not_disturb";

  return (
    <button
      onClick={() => setFounderManualOverride(isDnd ? null : "do_not_disturb")}
      className={`p-1 rounded-md transition-colors ${
        isDnd
          ? "text-red-400 bg-red-400/10"
          : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
      }`}
      title={isDnd ? "Do Not Disturb — click to clear" : "Set Do Not Disturb"}
    >
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
      </svg>
    </button>
  );
}

// StatusBar

export default function StatusBar() {
  const {
    runtime,
    health,
    executiveBoard,
    setRuntime,
    setHealth,
    setExecutiveBoard,
    setActiveWorkstation,
    voiceActive,
    setVoiceActive,
    isAwake,
    notifications,
    toggleCommandPalette,
    toggleNotificationPanel,
    notificationPanelOpen,
    emergencyActive,
    emergencyLevel,
    emergencySource,
    clearEmergency,
  } = useAxiomStore();

  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Poll runtime status every 15 seconds
  useEffect(() => {
    const poll = async () => {
      try {
        const [s, h, eb] = await Promise.all([
          system.status(),
          system.health(),
          execApi.boardStatus(),
        ]);
        setRuntime(s);
        setHealth(h);
        setExecutiveBoard(eb);
      } catch {
        // Backend not available
      }
    };
    poll();
    pollingRef.current = setInterval(poll, 15000);
    return () => clearInterval(pollingRef.current);
  }, [setRuntime, setHealth, setExecutiveBoard]);

  const healthOverall = health?.overall ?? "healthy";
  const healthDot = healthDotColor(healthOverall);
  const unreadCount = notifications.filter((n) => !n.read && (!n.snoozedUntil || n.snoozedUntil <= Date.now())).length;

  // Keyboard shortcuts: ⌘1-⌘4 for workstations, ⌘K for command palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey && !e.shiftKey && !e.altKey) {
        switch (e.key) {
          case "1": e.preventDefault(); setActiveWorkstation("axiom"); break;
          case "2": e.preventDefault(); setActiveWorkstation("bleval"); break;
          case "3": e.preventDefault(); setActiveWorkstation("valta"); break;
          case "4": e.preventDefault(); setActiveWorkstation("personal"); break;
          case "k": e.preventDefault(); toggleCommandPalette(); break;
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setActiveWorkstation, toggleCommandPalette]);

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Emergency banner */}
      <AnimatePresence>
        {emergencyActive && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 32 }}
            exit={{ opacity: 0, height: 0 }}
            className="h-8 bg-red-500/90 backdrop-blur-md flex items-center justify-between px-4"
          >
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              <span className="text-[10px] font-semibold text-white uppercase tracking-wider">
                {emergencyLevel === "critical" ? "🚨 Emergency" : "⚠️ Alert"}
              </span>
              <span className="text-[10px] text-white/80 hidden sm:inline">
                {emergencySource === "valta_prime" && "Valta Prime — POI requires attention"}
                {emergencySource === "yamako" && "Yamako — Reminder"}
                {emergencySource === "system" && "System — Component unhealthy"}
                {!["valta_prime", "yamako", "system"].includes(emergencySource || "") && "Requires attention"}
              </span>
            </div>
            <button
              onClick={clearEmergency}
              className="px-2.5 py-0.5 text-[9px] font-medium text-white bg-white/20 rounded-md hover:bg-white/30 transition-colors"
            >
              Acknowledge
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main bar */}
      <div className="h-10 glass-panel rounded-none border-x-0 border-t-0 flex items-center justify-between px-2 sm:px-4">
        {/* Left: AXIOM branding + workstations */}
        <div className="flex items-center gap-2 sm:gap-6">
          <button
            onClick={() => setActiveWorkstation("axiom")}
            className="flex items-center gap-2 group"
          >
            <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center flex-shrink-0">
              <span className="text-[8px] font-bold text-white tracking-tight">A</span>
            </div>
            <span className="text-[11px] font-medium text-[var(--axiom-text-secondary)] tracking-widest uppercase group-hover:text-[var(--axiom-text-primary)] transition-colors hidden sm:block">
              Axiom
            </span>
          </button>

          {/* Workstation navigation */}
          <nav className="flex items-center gap-1 md:gap-0">
            {workstationNavItems.map((item) => (
              <div key={item.id} className="hidden sm:block">
                <WorkstationNavItem {...item} />
              </div>
            ))}
            {/* Mobile workstation dots */}
            <div className="flex sm:hidden items-center gap-1.5">
              {workstationNavItems.map((item) => {
                const isActive = useAxiomStore.getState().activeWorkstation === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveWorkstation(item.id)}
                    className={`w-1.5 h-1.5 rounded-full ${
                      isActive
                        ? "bg-indigo-400 ring-1 ring-indigo-400/50"
                        : "bg-[var(--axiom-text-tertiary)] opacity-40 hover:opacity-70"
                    }`}
                    title={item.label}
                  />
                );
              })}
            </div>
          </nav>
        </div>

        {/* Right: status indicators */}
        <div className="flex items-center gap-2 sm:gap-4">
          {/* Availability + DND */}
          <AvailabilityDot />
          <DNDToggle />

          {/* Separator */}
          <div className="w-px h-4 bg-[var(--axiom-border)] hidden sm:block" />

          {/* Health indicator */}
          <button
            onClick={() => setActiveWorkstation("bleval")}
            className="flex items-center gap-1.5 group hidden sm:flex"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${healthDot} ${
                healthOverall === "healthy" ? "" : "animate-pulse"
              }`}
            />
            <span className="text-[10px] text-[var(--axiom-text-tertiary)] group-hover:text-[var(--axiom-text-secondary)] transition-colors hidden md:inline">
              {healthOverall === "healthy"
                ? "All systems normal"
                : `${health?.unhealthy ?? 0} issue${(health?.unhealthy ?? 0) > 1 ? "s" : ""}`}
            </span>
          </button>

          {/* Executive indicators */}
          <AnimatePresence>
            {executiveBoard && (
              <div className="flex items-center gap-1.5 hidden sm:flex">
                {Object.entries(executiveBoard).map(([id, exec]) => (
                  <motion.div
                    key={id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center gap-1"
                    title={`${id}: ${exec.status}`}
                  >
                    <span
                      className={`w-1 h-1 rounded-full ${
                        exec.status === "running"
                          ? "bg-emerald-400"
                          : exec.status === "error"
                            ? "bg-red-400"
                            : "bg-amber-400"
                      }`}
                    />
                    <span className="text-[10px] text-[var(--axiom-text-tertiary)] hidden sm:inline">
                      {id}
                    </span>
                  </motion.div>
                ))}
              </div>
            )}
          </AnimatePresence>

          {/* Voice toggle */}
          {isAwake && (
            <span className="text-[9px] font-mono text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded-sm tracking-wider hidden sm:inline">
              ON
            </span>
          )}
          <button
            onClick={() => setVoiceActive(!voiceActive)}
            className={`p-1 rounded-md transition-colors ${
              voiceActive
                ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            }`}
            title={
              isAwake
                ? "AXIOM ON — listening for commands"
                : voiceActive
                  ? 'Say "AXIOM ON" to wake'
                  : "Voice inactive"
            }
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {voiceActive ? (
                <>
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </>
              ) : (
                <>
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                  <line x1="8" y1="22" x2="16" y2="22" />
                </>
              )}
            </svg>
          </button>

          {/* Notifications bell */}
          <button
            onClick={toggleNotificationPanel}
            className={`relative p-1 rounded-md transition-colors ${
              notificationPanelOpen
                ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            }`}
            title="Notifications"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            {unreadCount > 0 && (
              <motion.span
                key={unreadCount}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-red-400 rounded-full text-[7px] font-bold text-white flex items-center justify-center"
              >
                {unreadCount > 9 ? "9+" : unreadCount}
              </motion.span>
            )}
          </button>
          <NotificationCenter />

          {/* Runtime info */}
          <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono tabular-nums hidden md:block">
            v{runtime?.version ?? "—"}
          </span>
        </div>
      </div>
    </div>
  );
}