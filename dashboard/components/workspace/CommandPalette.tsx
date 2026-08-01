"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { executives as execApi } from "../../lib/api";
import type { WorkspaceId } from "../../lib/store/axiom-store";

/* ── Fuzzy match (character-sequence) ────────────────────────────── */

function fuzzyMatch(query: string, text: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  let qi = 0;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) qi++;
  }
  return qi >= q.length;
}

/* ── Strip natural-language prefixes ─────────────────────────────── */

function stripPrefix(input: string): string {
  return input.replace(/^(?:go\s+to|open|run|launch|switch\s+to|navigate\s+to)\s+/i, "").trim();
}

/* ── Command type ────────────────────────────────────────────────── */

interface Command {
  id: string;
  label: string;
  description: string;
  category: string;
  keywords?: string[];
  shortcut?: string;
  action: () => void;
}

/* ── History helpers ─────────────────────────────────────────────── */

const HISTORY_KEY = "axiom-command-history";
const MAX_HISTORY = 10;

function getHistory(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function addToHistory(id: string) {
  try {
    const h = getHistory().filter((x) => x !== id);
    h.unshift(id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(0, MAX_HISTORY)));
  } catch {
    // localStorage unavailable
  }
}

/* ── Component ───────────────────────────────────────────────────── */

export default function CommandPalette() {
  const { commandPaletteOpen, setCommandPalette, setActiveView } = useAxiomStore();

  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [staticCommands, setStaticCommands] = useState<Command[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  /* Build static navigation commands */
  const navCommands: Command[] = useMemo(
    () => [
      { id: "goto-workspace", label: "Go to Founder Workspace", description: "Open conversation with AXIOM", category: "Navigation", shortcut: "⌘1", keywords: ["chat", "home"], action: () => { setActiveView("workspace"); setCommandPalette(false); } },
      { id: "goto-executives", label: "Go to Executive Board", description: "View Jenson, Valta Prime, Yamako", category: "Navigation", shortcut: "⌘2", keywords: ["exec", "board", "agents"], action: () => { setActiveView("executives"); setCommandPalette(false); } },
      { id: "goto-operations", label: "Go to Operations Center", description: "Runtime, events, health", category: "Navigation", shortcut: "⌘3", keywords: ["ops", "runtime", "health", "status"], action: () => { setActiveView("operations"); setCommandPalette(false); } },
      { id: "goto-knowledge", label: "Go to Knowledge", description: "Unified search, knowledge graph", category: "Navigation", shortcut: "⌘4", keywords: ["search", "memory", "learn"], action: () => { setActiveView("knowledge"); setCommandPalette(false); } },
      { id: "goto-projects", label: "Go to Projects", description: "Timeline, artifacts, tasks", category: "Navigation", shortcut: "⌘5", keywords: ["tasks", "artifacts"], action: () => { setActiveView("projects"); setCommandPalette(false); } },
      { id: "goto-creator", label: "Go to Creator Studio", description: "Image, video, audio, campaigns", category: "Navigation", shortcut: "⌘6", keywords: ["create", "media", "generate"], action: () => { setActiveView("creator"); setCommandPalette(false); } },
      { id: "goto-trading", label: "Go to Trading Terminal", description: "Macro, charts, positions, risk", category: "Navigation", shortcut: "⌘7", keywords: ["finance", "market"], action: () => { setActiveView("trading"); setCommandPalette(false); } },
      { id: "goto-console", label: "Go to Founder Console", description: "Settings, API keys, security", category: "Navigation", shortcut: "⌘8", keywords: ["settings", "config", "admin"], action: () => { setActiveView("console"); setCommandPalette(false); } },
      { id: "goto-communications", label: "Go to Communications Hub", description: "Universal inbox", category: "Navigation", shortcut: "⌘9", keywords: ["inbox", "messages", "notifications"], action: () => { setActiveView("communications"); setCommandPalette(false); } },
      { id: "goto-intelligence", label: "Go to Intelligence Center", description: "Live reasoning, providers, tokens", category: "Navigation", shortcut: "⌘0", keywords: ["llm", "models", "reason"], action: () => { setActiveView("intelligence"); setCommandPalette(false); } },
      { id: "goto-content-hub", label: "Go to Content Hub", description: "Assets library", category: "Navigation", shortcut: "⌥1", keywords: ["assets", "gallery", "media"], action: () => { setActiveView("content-hub"); setCommandPalette(false); } },
      { id: "goto-integrations", label: "Go to Integrations", description: "Connected services", category: "Navigation", shortcut: "⌥2", keywords: ["services", "github", "gmail"], action: () => { setActiveView("integrations"); setCommandPalette(false); } },
      { id: "goto-collaboration", label: "Go to Collaboration Workspace", description: "Team sessions and roster", category: "Navigation", shortcut: "⌥3", keywords: ["team", "sessions", "roster"], action: () => { setActiveView("collaboration"); setCommandPalette(false); } },
    ],
    [setActiveView, setCommandPalette],
  );

  const actionCommands: Command[] = useMemo(
    () => [
      { id: "new-conversation", label: "New conversation", description: "Start a fresh chat", category: "Actions", keywords: ["chat", "start"], action: () => { setActiveView("workspace"); setCommandPalette(false); } },
      { id: "toggle-command-center", label: "Toggle Command Center", description: "Switch between dashboard and chat", category: "Actions", keywords: ["dashboard", "briefing"], action: () => { setActiveView("workspace"); setCommandPalette(false); } },
    ],
    [setActiveView, setCommandPalette],
  );

  const systemCommands: Command[] = useMemo(
    () => [
      { id: "system-status", label: "System status", description: "View runtime health", category: "System", keywords: ["health", "uptime"], action: () => { setActiveView("operations"); setCommandPalette(false); } },
      { id: "close-palette", label: "Close command palette", description: "Dismiss this menu", category: "System", shortcut: "Esc", action: () => setCommandPalette(false) },
    ],
    [setActiveView, setCommandPalette],
  );

  /* Fetch dynamic commands on open */
  useEffect(() => {
    if (!commandPaletteOpen) return;
    setHistory(getHistory());

    (async () => {
      const dynamic: Command[] = [];

      try {
        const board = await execApi.boardStatus();
        if (board) {
          for (const [id, exec] of Object.entries(board)) {
            dynamic.push({
              id: `executive-${id}`,
              label: `View executive: ${id}`,
              description: `${exec.status} · ${exec.org}`,
              category: "Executives",
              action: () => { setActiveView("executives"); setCommandPalette(false); },
            });
          }
        }
      } catch {
        // Board unavailable
      }

      setStaticCommands(dynamic);
    })();
  }, [commandPaletteOpen, setActiveView, setCommandPalette]);

  /* Combine all commands */
  const allCommands = useMemo(
    () => [...navCommands, ...actionCommands, ...staticCommands, ...systemCommands],
    [navCommands, actionCommands, staticCommands, systemCommands],
  );

  /* ── Fuzzy filtering ────────────────────────────────────────────── */

  const stripQuery = stripPrefix(query.trim());

  const grouped = useMemo(() => {
    const groups = new Map<string, Command[]>();

    for (const cmd of allCommands) {
      const searchText = [cmd.label, cmd.description, cmd.category, ...(cmd.keywords || [])].join(" ");
      if (!fuzzyMatch(stripQuery, searchText)) continue;
      if (!groups.has(cmd.category)) groups.set(cmd.category, []);
      groups.get(cmd.category)!.push(cmd);
    }

    // Build ordered result with Recent section if history exists
    const sections: { title: string; items: Command[] }[] = [];

    // If query is empty, show Recent section from history
    if (!stripQuery && history.length > 0) {
      const recentCmds: Command[] = [];
      for (const hId of history) {
        const found = allCommands.find((c) => c.id === hId);
        if (found) recentCmds.push(found);
        if (recentCmds.length >= 5) break;
      }
      if (recentCmds.length > 0) sections.push({ title: "Recent", items: recentCmds });
    }

    for (const cat of ["Navigation", "Executives", "Actions", "System"]) {
      const items = groups.get(cat);
      if (items) sections.push({ title: cat, items });
    }

    return sections;
  }, [allCommands, stripQuery, history]);

  const flatItems = useMemo(() => grouped.flatMap((g) => g.items), [grouped]);

  /* ── Keyboard & selection ────────────────────────────────────────── */

  useEffect(() => { setSelectedIndex(0); }, [query]);

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandPaletteOpen]);

  useEffect(() => {
    if (!listRef.current) return;
    const children = listRef.current.querySelectorAll<HTMLElement>("[data-cmd-index]");
    const sel = children[selectedIndex];
    sel?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedIndex]);

  const executeSelected = useCallback(() => {
    const cmd = flatItems[selectedIndex];
    if (cmd) {
      addToHistory(cmd.id);
      cmd.action();
    }
  }, [flatItems, selectedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % Math.max(flatItems.length, 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + flatItems.length) % Math.max(flatItems.length, 1));
        break;
      case "Enter":
        e.preventDefault();
        executeSelected();
        break;
      case "Escape":
        e.preventDefault();
        setCommandPalette(false);
        break;
    }
  };

  /* ── Render ──────────────────────────────────────────────────────── */

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.08, ease: "easeIn" }}
          className="fixed inset-0 z-[9998] flex items-start justify-center pt-[15vh]"
          onClick={(e) => {
            if (e.target === e.currentTarget) setCommandPalette(false);
          }}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className="relative w-full max-w-lg glass-panel shadow-xl overflow-hidden"
          >
            {/* Search input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--axiom-border)]">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] flex-shrink-0">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search commands..."
                className="flex-1 bg-transparent text-sm text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] outline-none font-sans"
              />
              <kbd className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono border border-[var(--axiom-border)] rounded px-1.5 py-0.5">ESC</kbd>
            </div>

            {/* Results */}
            <div ref={listRef} className="max-h-[360px] overflow-y-auto p-2">
              {flatItems.length === 0 ? (
                <div className="py-8 text-center text-sm text-[var(--axiom-text-tertiary)]">
                  No results for &ldquo;{query}&rdquo;
                </div>
              ) : (
                (() => {
                  let globalIndex = 0;
                  return grouped.map((section) => (
                    <div key={section.title}>
                      <p className="text-[10px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] px-3 py-1.5 font-semibold">
                        {section.title}
                      </p>
                      {section.items.map((cmd) => {
                        const idx = globalIndex++;
                        const selected = idx === selectedIndex;
                        return (
                          <button
                            key={cmd.id}
                            data-cmd-index={idx}
                            onClick={() => {
                              addToHistory(cmd.id);
                              cmd.action();
                            }}
                            onMouseEnter={() => setSelectedIndex(idx)}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-left transition-colors duration-75 ${
                              selected
                                ? "bg-[var(--axiom-accent-subtle)]"
                                : "hover:bg-[var(--axiom-bg-elevated)]"
                            }`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-[var(--axiom-text-primary)] leading-tight">
                                {cmd.label}
                              </div>
                              <div className="text-[11px] text-[var(--axiom-text-tertiary)] truncate mt-0.5">
                                {cmd.description}
                              </div>
                            </div>
                            {cmd.shortcut && (
                              <kbd className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono border border-[var(--axiom-border)] rounded px-1.5 py-0.5 flex-shrink-0 ml-2">
                                {cmd.shortcut}
                              </kbd>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  ));
                })()
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-[var(--axiom-border)] flex items-center gap-4 text-[10px] text-[var(--axiom-text-tertiary)]">
              <span><kbd className="font-mono border border-[var(--axiom-border)] rounded px-1">↑↓</kbd> Navigate</span>
              <span><kbd className="font-mono border border-[var(--axiom-border)] rounded px-1">↵</kbd> Select</span>
              <span><kbd className="font-mono border border-[var(--axiom-border)] rounded px-1">Esc</kbd> Close</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}