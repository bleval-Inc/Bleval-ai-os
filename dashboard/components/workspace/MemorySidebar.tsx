"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { memory } from "../../lib/api";
import { timeAgo } from "../../lib/utils";

interface MemoryFile {
  path: string;
  content: string;
  preview: string;
}

export default function MemorySidebar() {
  const { sidePanel, setSidePanel } = useAxiomStore();
  const [memories, setMemories] = useState<MemoryFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<string | null>(null);

  const isOpen = sidePanel === "memory";

  // Fetch memory on open
  useEffect(() => {
    if (!isOpen) return;
    const fetchMemories = async () => {
      setLoading(true);
      try {
        const res = await memory.get("founder", "personal");
        const files = Object.entries(res.content ?? {}).map(
          ([path, content]) => ({
            path,
            content: content as string,
            preview: (content as string).slice(0, 150),
          }),
        );
        setMemories(files);
      } catch {
        // Use placeholder data if backend not available
        setMemories([
          { path: "preferences.md", content: "User preferences", preview: "Theme: dark, Voice: enabled, Default workspace: personal" },
          { path: "routines.md", content: "Daily routines", preview: "Morning review 8am, Midday check 12pm, Evening report 6pm" },
          { path: "goals.md", content: "Current goals", preview: "Q3 2026: Scale operations, Launch new product line" },
        ]);
      }
      setLoading(false);
    };
    fetchMemories();
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 280, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-hidden flex-shrink-0"
        >
          <div className="w-[280px] h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--axiom-border)]">
              <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] tracking-wide uppercase">
                Memory
              </h3>
              <button
                onClick={() => setSidePanel("none")}
                className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 6 6 18" /><path d="m6 6 12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-16 rounded-md bg-[var(--axiom-bg-elevated)] animate-pulse"
                    />
                  ))}
                </div>
              ) : (
                memories.map((mem) => (
                  <button
                    key={mem.path}
                    onClick={() =>
                      setSelectedMemory(
                        selectedMemory === mem.path ? null : mem.path,
                      )
                    }
                    className={`w-full text-left p-3 rounded-lg transition-all duration-150 ${
                      selectedMemory === mem.path
                        ? "bg-[var(--axiom-accent-subtle)] border border-[var(--axiom-accent-muted)]"
                        : "bg-[var(--axiom-bg-elevated)] border border-transparent hover:border-[var(--axiom-border)]"
                    }`}
                  >
                    <div className="text-xs font-medium text-[var(--axiom-text-primary)] font-mono truncate">
                      {mem.path}
                    </div>
                    <p className="text-[11px] text-[var(--axiom-text-tertiary)] mt-1 line-clamp-2 leading-relaxed">
                      {mem.preview}
                    </p>
                  </button>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-[var(--axiom-border)]">
              <button className="w-full text-[11px] text-[var(--axiom-accent)] hover:text-[var(--axiom-accent-hover)] font-medium transition-colors">
                + New memory entry
              </button>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}