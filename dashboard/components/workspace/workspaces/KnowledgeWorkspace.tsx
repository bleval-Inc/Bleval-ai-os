"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { system, learning } from "../../../lib/api";
import type { LearningStatus, KnowledgeEntry } from "../../../lib/api-types";

function formatDate(raw: string) {
  const d = new Date(raw);
  return d.toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

function uniqueSources(e: KnowledgeEntry[]) { return new Set(e.map((x) => x.source)).size; }

function Skeleton() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse"
              style={{ animationDelay: `${i * 200}ms` }}
            />
          ))}
        </div>
        <p className="text-xs text-[var(--axiom-text-tertiary)]">Loading knowledge base...</p>
      </div>
    </div>
  );
}

function ErrorPanel({ msg, onRetry }: { msg: string; onRetry: () => void }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-xs">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
          className="mx-auto mb-3 text-[var(--axiom-error)]">
          <circle cx="12" cy="12" r="10" />
          <path d="m15 9-6 6" /><path d="m9 9 6 6" />
        </svg>
        <p className="text-sm text-[var(--axiom-error)] mb-2">Failed to load knowledge</p>
        <p className="text-xs text-[var(--axiom-text-tertiary)] mb-4">{msg}</p>
        <button onClick={onRetry}
          className="px-4 py-1.5 text-xs font-medium rounded-md border border-[var(--axiom-border)]
            text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors">
          Retry
        </button>
      </div>
    </div>
  );
}

/* Knowledge card */

function KnowledgeCard({ entry }: { entry: KnowledgeEntry }) {
  const [open, setOpen] = useState(false);
  const preview = entry.content.length > 120
    ? entry.content.slice(0, 120) + "..."
    : entry.content;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-3 p-4 text-left transition-colors hover:bg-[var(--axiom-accent-subtle)]"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
          className="mt-0.5 shrink-0 text-[var(--axiom-accent)]">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-[var(--axiom-text-primary)] truncate">
            {entry.title}
          </h4>
          <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1 leading-relaxed">
            {open ? entry.content : preview}
          </p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {entry.tags.map((tag) => (
              <span key={tag}
                className="px-1.5 py-0.5 text-[10px] font-medium rounded-full
                  bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]">
                {tag}
              </span>
            ))}
            <span className="text-[10px] text-[var(--axiom-text-tertiary)] ml-auto">
              {formatDate(entry.created_at)}
            </span>
          </div>
        </div>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className={`mt-1 shrink-0 text-[var(--axiom-text-tertiary)] transition-transform ${
            open ? "rotate-180" : ""
          }`}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </motion.div>
  );
}

/* KnowledgeWorkspace (default export) */

export default function KnowledgeWorkspace() {
  const [status, setStatus] = useState<LearningStatus | null>(null);
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, k] = await Promise.all([
        learning.status(),
        learning.knowledge(),
      ]);
      setStatus(s);
      setEntries(k);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const filtered = useMemo(
    () =>
      search.trim()
        ? entries.filter(
            (e) =>
              e.title.toLowerCase().includes(search.toLowerCase()) ||
              e.content.toLowerCase().includes(search.toLowerCase()) ||
              e.tags.some((t) => t.toLowerCase().includes(search.toLowerCase())),
          )
        : entries,
    [entries, search],
  );

  /* Render */
  if (loading) return <Skeleton />;
  if (error) return <ErrorPanel msg={error} onRetry={fetchAll} />;

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <h2 className="text-sm font-medium text-[var(--axiom-text-primary)]">Knowledge Base</h2>
        <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono">
          {status?.total_knowledge_entries ?? 0} entries
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full px-6 py-5 space-y-5">
          {/* Search bar */}
          <div className="relative">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--axiom-text-tertiary)]">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search knowledge entries..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-md border border-[var(--axiom-border)]
                bg-[var(--axiom-bg-surface)] text-[var(--axiom-text-primary)]
                placeholder:text-[var(--axiom-text-tertiary)] outline-none
                focus:border-[var(--axiom-accent)] transition-colors"
            />
          </div>

          {/* Stats row */}
          <div className="flex gap-4">
            <div className="glass-card flex-1 px-4 py-3 text-center">
              <span className="text-lg font-semibold text-[var(--axiom-text-primary)]">
                {status?.total_knowledge_entries ?? 0}
              </span>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">Total entries</p>
            </div>
            <div className="glass-card flex-1 px-4 py-3 text-center">
              <span className="text-lg font-semibold text-[var(--axiom-text-primary)]">
                {status?.last_cycle ? formatDate(status.last_cycle) : "—"}
              </span>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">Last updated</p>
            </div>
            <div className="glass-card flex-1 px-4 py-3 text-center">
              <span className="text-lg font-semibold text-[var(--axiom-text-primary)]">
                {uniqueSources(entries)}
              </span>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">Sources</p>
            </div>
          </div>

          {/* Empty state */}
          {filtered.length === 0 && (
            <div className="flex flex-col items-center py-16 text-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                className="text-[var(--axiom-text-tertiary)] mb-3">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <p className="text-sm text-[var(--axiom-text-secondary)]">
                {search ? "No entries match your search" : "Knowledge base is empty"}
              </p>
              <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">
                {search
                  ? "Try a different search term"
                  : "New learning cycles will populate entries here"}
              </p>
            </div>
          )}

          {/* Entry list */}
          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {filtered.map((entry) => (
                <KnowledgeCard key={entry.entry_id} entry={entry} />
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}