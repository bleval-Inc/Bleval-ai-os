"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { system, executives as execApi } from "../../lib/api";
import { healthDotColor, formatTimestamp } from "../../lib/utils";

export default function StatusBar() {
  const {
    runtime,
    health,
    executiveBoard,
    setRuntime,
    setHealth,
    setExecutiveBoard,
    setActiveView,
    activeView,
    voiceActive,
    setVoiceActive,
    isListening,
    isAwake,
    notifications,
    toggleCommandPalette,
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

  const navItems = [
    { id: "workspace" as const, label: "Founder", shortcut: "⌘1" },
    { id: "executives" as const, label: "Exec Board", shortcut: "⌘2" },
    { id: "operations" as const, label: "Operations", shortcut: "⌘3" },
    { id: "knowledge" as const, label: "Knowledge", shortcut: "⌘4" },
    { id: "projects" as const, label: "Projects", shortcut: "⌘5" },
    { id: "creator" as const, label: "Creator", shortcut: "⌘6" },
    { id: "trading" as const, label: "Trading", shortcut: "⌘7" },
    { id: "console" as const, label: "Console", shortcut: "⌘8" },
  ];

  // Keyboard shortcuts for navigation — ⌘1 through ⌘8 for workspaces, ⌘K for command palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey && !e.shiftKey) {
        switch (e.key) {
          case "1":
            e.preventDefault();
            setActiveView("workspace");
            break;
          case "2":
            e.preventDefault();
            setActiveView("executives");
            break;
          case "3":
            e.preventDefault();
            setActiveView("operations");
            break;
          case "4":
            e.preventDefault();
            setActiveView("knowledge");
            break;
          case "5":
            e.preventDefault();
            setActiveView("projects");
            break;
          case "6":
            e.preventDefault();
            setActiveView("creator");
            break;
          case "7":
            e.preventDefault();
            setActiveView("trading");
            break;
          case "8":
            e.preventDefault();
            setActiveView("console");
            break;
          case "k":
            e.preventDefault();
            toggleCommandPalette();
            break;
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setActiveView, toggleCommandPalette]);

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Main bar */}
      <div className="h-10 glass-panel rounded-none border-x-0 border-t-0 flex items-center justify-between px-4">
        {/* Left: AXIOM branding + nav */}
        <div className="flex items-center gap-6">
          {/* AXIOM logo */}
          <button
            onClick={() => setActiveView("workspace")}
            className="flex items-center gap-2 group"
          >
            <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center">
              <span className="text-[8px] font-bold text-white tracking-tight">
                A
              </span>
            </div>
            <span className="text-[11px] font-medium text-[var(--axiom-text-secondary)] tracking-widest uppercase group-hover:text-[var(--axiom-text-primary)] transition-colors">
              Axiom
            </span>
          </button>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all duration-150 ${
                  activeView === item.id
                    ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
                }`}
              >
                {item.label}
                <span className="ml-1.5 text-[9px] opacity-40">{item.shortcut}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Right: status indicators */}
        <div className="flex items-center gap-4">
          {/* Health indicator — links to operations */}
          <button
            onClick={() => setActiveView("operations")}
            className="flex items-center gap-1.5 group"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${healthDot} ${
                healthOverall === "healthy" ? "" : "animate-pulse"
              }`}
            />
            <span className="text-[10px] text-[var(--axiom-text-tertiary)] group-hover:text-[var(--axiom-text-secondary)] transition-colors">
              {healthOverall === "healthy"
                ? "All systems normal"
                : `${health?.unhealthy ?? 0} issue${(health?.unhealthy ?? 0) > 1 ? "s" : ""}`}
            </span>
          </button>

          {/* Executive indicators */}
          <AnimatePresence>
            {executiveBoard && (
              <div className="flex items-center gap-1.5">
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
            <span className="text-[9px] font-mono text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded-sm tracking-wider">
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
            className="relative p-1 text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] transition-colors"
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
            {notifications.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-red-400 rounded-full text-[7px] font-bold text-white flex items-center justify-center">
                {notifications.length > 9 ? "9+" : notifications.length}
              </span>
            )}
          </button>

          {/* Runtime info */}
          <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono tabular-nums hidden md:block">
            v{runtime?.version ?? "—"}
          </span>
        </div>
      </div>
    </div>
  );
}