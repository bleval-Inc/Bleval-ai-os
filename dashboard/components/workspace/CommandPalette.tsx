"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import type { WorkspaceId } from "../../lib/store/axiom-store";

interface Command {
  id: string;
  label: string;
  description: string;
  category: string;
  shortcut?: string;
  action: () => void;
}

export default function CommandPalette() {
  const {
    commandPaletteOpen,
    setCommandPalette,
    setActiveView,
    activeView,
  } = useAxiomStore();

  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const commands: Command[] = [
    // ── Navigation ──────────────────────────────────────────
    {
      id: "goto-workspace",
      label: "Go to Founder Workspace",
      description: "Open conversation with AXIOM",
      category: "Navigation",
      shortcut: "⌘1",
      action: () => {
        setActiveView("workspace");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-executives",
      label: "Go to Executive Board",
      description: "View Jenson, Valta Prime, Yamako",
      category: "Navigation",
      shortcut: "⌘2",
      action: () => {
        setActiveView("executives");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-operations",
      label: "Go to Operations Center",
      description: "NASA Mission Control — runtime, events, health",
      category: "Navigation",
      shortcut: "⌘3",
      action: () => {
        setActiveView("operations");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-knowledge",
      label: "Go to Knowledge",
      description: "Unified search, knowledge graph, semantic memory",
      category: "Navigation",
      shortcut: "⌘4",
      action: () => {
        setActiveView("knowledge");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-projects",
      label: "Go to Projects",
      description: "Timeline, artifacts, tasks, approvals",
      category: "Navigation",
      shortcut: "⌘5",
      action: () => {
        setActiveView("projects");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-creator",
      label: "Go to Creator Studio",
      description: "Image, video, audio, design, campaigns",
      category: "Navigation",
      shortcut: "⌘6",
      action: () => {
        setActiveView("creator");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-trading",
      label: "Go to Trading Terminal",
      description: "Macro, charts, positions, risk, journals",
      category: "Navigation",
      shortcut: "⌘7",
      action: () => {
        setActiveView("trading");
        setCommandPalette(false);
      },
    },
    {
      id: "goto-console",
      label: "Go to Founder Console",
      description: "Goals, settings, API keys, security",
      category: "Navigation",
      shortcut: "⌘8",
      action: () => {
        setActiveView("console");
        setCommandPalette(false);
      },
    },
    // ── Actions ──────────────────────────────────────────────
    {
      id: "new-conversation",
      label: "New conversation",
      description: "Start a fresh conversation with AXIOM",
      category: "Actions",
      action: () => {
        setActiveView("workspace");
        setCommandPalette(false);
      },
    },
    {
      id: "toggle-voice",
      label: "Toggle voice",
      description: "Enable or disable voice interaction",
      category: "Actions",
      shortcut: "⌘⇧V",
      action: () => {
        setCommandPalette(false);
      },
    },
    // ── System ───────────────────────────────────────────────
    {
      id: "system-status",
      label: "System status",
      description: "View runtime health and component status",
      category: "System",
      action: () => {
        setActiveView("operations");
        setCommandPalette(false);
      },
    },
    {
      id: "close-palette",
      label: "Close command palette",
      description: "Dismiss this menu",
      category: "System",
      shortcut: "Esc",
      action: () => setCommandPalette(false),
    },
  ];

  // Filter commands based on query
  const filtered = query.trim()
    ? commands.filter(
        (cmd) =>
          cmd.label.toLowerCase().includes(query.toLowerCase()) ||
          cmd.description.toLowerCase().includes(query.toLowerCase()) ||
          cmd.category.toLowerCase().includes(query.toLowerCase()),
      )
    : commands;

  // Reset selection when results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Focus input when opened
  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandPaletteOpen]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const selected = listRef.current.children[selectedIndex] as HTMLElement;
    selected?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedIndex]);

  const executeSelected = useCallback(() => {
    if (filtered[selectedIndex]) {
      filtered[selectedIndex].action();
    }
  }, [filtered, selectedIndex]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % filtered.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + filtered.length) % filtered.length);
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

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
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
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="relative w-full max-w-lg glass-panel shadow-xl overflow-hidden"
          >
            {/* Search input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--axiom-border)]">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-[var(--axiom-text-tertiary)] flex-shrink-0"
              >
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
              <kbd className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono border border-[var(--axiom-border)] rounded px-1.5 py-0.5">
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div
              ref={listRef}
              className="max-h-[320px] overflow-y-auto p-2"
            >
              {filtered.length === 0 ? (
                <div className="py-8 text-center text-sm text-[var(--axiom-text-tertiary)]">
                  No results for &ldquo;{query}&rdquo;
                </div>
              ) : (
                filtered.map((cmd, i) => {
                  const selected = i === selectedIndex;
                  return (
                    <button
                      key={cmd.id}
                      onClick={() => {
                        cmd.action();
                      }}
                      onMouseEnter={() => setSelectedIndex(i)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-left transition-colors duration-100 ${
                        selected
                          ? "bg-[var(--axiom-accent-subtle)]"
                          : "hover:bg-[var(--axiom-bg-elevated)]"
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-[var(--axiom-text-primary)]">
                          {cmd.label}
                        </div>
                        <div className="text-[11px] text-[var(--axiom-text-tertiary)] truncate">
                          {cmd.description}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono">
                          {cmd.category}
                        </span>
                        {cmd.shortcut && (
                          <kbd className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono border border-[var(--axiom-border)] rounded px-1.5 py-0.5">
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </div>
                    </button>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-[var(--axiom-border)] flex items-center gap-4 text-[10px] text-[var(--axiom-text-tertiary)]">
              <span>
                <kbd className="font-mono border border-[var(--axiom-border)] rounded px-1">↑↓</kbd> Navigate
              </span>
              <span>
                <kbd className="font-mono border border-[var(--axiom-border)] rounded px-1">↵</kbd> Select
              </span>
              <span>
                <kbd className="font-mono border border-[var(--axiom-border)] rounded px-1">Esc</kbd> Close
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}