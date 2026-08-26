"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import type { WorkspaceId, WorkstationId } from "../../lib/store/axiom-store";

/* Fuzzy match (character-sequence) */

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

/* Strip natural-language prefixes */

function stripPrefix(input: string): string {
  return input.replace(/^(?:go\s+to|open|run|launch|switch\s+to|navigate\s+to)\s+/i, "").trim();
}

/* Command type */

interface Command {
  id: string;
  label: string;
  description: string;
  category: string;
  keywords?: string[];
  shortcut?: string;
  action: () => void;
}

/* History helpers */

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

/* Component */

export default function CommandPalette() {
  const { commandPaletteOpen, setCommandPalette, setActiveView, setActiveWorkstation } = useAxiomStore();

  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [staticCommands, setStaticCommands] = useState<Command[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  /* Build static navigation commands - only valid workspace IDs */
  const navCommands: Command[] = useMemo(
    () => [
      { id: "goto-workspace", label: "Go to Home", description: "Open AXIOM home workspace", category: "Navigation", shortcut: "⌘1", keywords: ["home", "chat"], action: () => { setActiveView("workspace"); setCommandPalette(false); } },
      { id: "goto-boardroom", label: "Go to Boardroom", description: "Executive governance", category: "Navigation", shortcut: "⌘B", keywords: ["board", "governance"], action: () => { setActiveView("boardroom"); setActiveWorkstation("boardroom"); setCommandPalette(false); } },
      { id: "goto-system", label: "Go to System", description: "System monitoring & health", category: "Navigation", shortcut: "⌘5", keywords: ["system", "health", "monitor"], action: () => { setActiveView("system"); setActiveWorkstation("system"); setCommandPalette(false); } },
      { id: "goto-settings", label: "Go to Settings", description: "Configuration & preferences", category: "Navigation", shortcut: "⌘,", keywords: ["settings", "config"], action: () => { setActiveView("settings"); setActiveWorkstation("settings"); setCommandPalette(false); } },
      { id: "goto-bleval", label: "Go to Bleval Inc", description: "Company operations workstation", category: "Navigation", shortcut: "⌘2", keywords: ["bleval", "operations", "jenson"], action: () => { setActiveWorkstation("bleval"); setActiveView("workspace"); setCommandPalette(false); } },
      { id: "goto-valta", label: "Go to House of Valta", description: "Markets & strategy workstation", category: "Navigation", shortcut: "⌘3", keywords: ["valta", "markets", "strategy"], action: () => { setActiveWorkstation("valta"); setActiveView("workspace"); setCommandPalette(false); } },
      { id: "goto-personal", label: "Go to Personal", description: "Personal operations workstation", category: "Navigation", shortcut: "⌘4", keywords: ["personal", "ops", "yamako"], action: () => { setActiveWorkstation("personal"); setActiveView("workspace"); setCommandPalette(false); } },
    ],
    [setActiveView, setActiveWorkstation, setCommandPalette],
  );

  const systemCommands: Command[] = useMemo(
    () => [
      { id: "close-palette", label: "Close command palette", description: "Dismiss this menu", category: "System", shortcut: "Esc", action: () => setCommandPalette(false) },
    ],
    [setCommandPalette],
  );

  /* Combine all commands */
  const allCommands = useMemo(
    () => [...navCommands, ...staticCommands, ...systemCommands],
    [navCommands, staticCommands, systemCommands],
  );

  /* Fuzzy filtering */

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

    for (const cat of ["Navigation", "System"]) {
      const items = groups.get(cat);
      if (items) sections.push({ title: cat, items });
    }

    return sections;
  }, [allCommands, stripQuery, history]);

  const flatItems = useMemo(() => grouped.flatMap((g) => g.items), [grouped]);

  /* Keyboard & selection */

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

  /* Render */

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