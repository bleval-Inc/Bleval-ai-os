"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { system } from "../../../lib/api";
import type { Capability, PerformanceScore } from "../../../lib/api-types";

/* Content categories */

const CATEGORIES = [
  { key: "all", label: "All", icon: "grid" },
  { key: "creation", label: "Creation", icon: "pen" },
  { key: "design", label: "Design", icon: "palette" },
  { key: "marketing", label: "Campaigns", icon: "megaphone" },
  { key: "writing", label: "Content", icon: "file" },
] as const;

type CategoryKey = (typeof CATEGORIES)[number]["key"];

/* SVG Icons */

function Icon({ name, size = 16 }: { name: string; size?: number }) {
  const paths: Record<string, string> = {
    grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
    pen: "M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z",
    palette: "M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z",
    megaphone: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
    file: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z",
    sparkle: "M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z",
    lightning: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
    layers: "M12 2L2 7l10 5 10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
  };
  const d = paths[name] || paths.grid;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

/* ── Creator Studio ────────────────────────────────────────────────── */

export default function CreatorStudio() {
  const [activeTab, setActiveTab] = useState<CategoryKey>("all");
  const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [scores, setScores] = useState<PerformanceScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const [caps, perfScores] = await Promise.all([
        system.listCapabilities(),
        system.getPerformanceScores().catch(() => [] as PerformanceScore[]),
      ]);
      setCapabilities(caps);
      setScores(perfScores);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load studio data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, []);

  const filtered = useMemo(() => {
    if (activeTab === "all") return capabilities;
    return capabilities.filter((c) => c.category === activeTab);
  }, [capabilities, activeTab]);

  /* ── Loading state ─────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" as const }}>
            <Icon name="sparkle" size={32} />
          </motion.div>
          <p className="text-sm text-[var(--axiom-text-tertiary)]">Loading Creator Studio...</p>
        </div>
      </div>
    );
  }

  /* ── Error state ───────────────────────────────────────────────── */
  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="glass-panel p-8 text-center max-w-sm">
          <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--axiom-error)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <p className="text-sm text-[var(--axiom-text-secondary)] mb-4">{error}</p>
          <button onClick={fetch} className="px-4 py-2 text-xs font-medium rounded-lg border border-[var(--axiom-border)] hover:bg-[var(--axiom-bg-elevated)] transition-colors">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-[var(--axiom-text-primary)]">Creator Studio</h2>
          <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono">{capabilities.length} capabilities</span>
        </div>
        <button onClick={fetch} className="p-1.5 rounded-md text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors" title="Refresh">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Category tabs */}
        <div className="flex gap-1 px-6 py-3 border-b border-[var(--axiom-border)]">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              onClick={() => setActiveTab(cat.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === cat.key
                  ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
              }`}
            >
              <Icon name={cat.icon} size={14} />
              {cat.label}
            </button>
          ))}
        </div>

        {/* Capabilities grid */}
        <div className="p-6">
          {filtered.length === 0 ? (
            <div className="text-center py-12">
              <Icon name="layers" size={32} />
              <p className="text-sm text-[var(--axiom-text-tertiary)] mt-3">No capabilities found in this category</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {filtered.map((cap, i) => (
                <motion.div
                  key={cap.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="glass-panel p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-medium text-[var(--axiom-text-primary)]">{cap.name}</h3>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                      cap.level === "expert" ? "bg-purple-500/10 text-purple-400" :
                      cap.level === "advanced" ? "bg-blue-500/10 text-blue-400" :
                      cap.level === "intermediate" ? "bg-green-500/10 text-green-400" :
                      "bg-amber-500/10 text-amber-400"
                    }`}>{cap.level}</span>
                  </div>
                  {cap.agents.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {cap.agents.map((a) => (
                        <span key={a} className="px-1.5 py-0.5 text-[10px] rounded bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)]">{a}</span>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Performance section */}
        {scores.length > 0 && (
          <div className="px-6 pb-6">
            <h3 className="text-xs font-semibold text-[var(--axiom-text-secondary)] uppercase tracking-wide mb-3">Recent Performance</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {scores.slice(0, 4).map((s, i) => (
                <div key={i} className="glass-panel p-3">
                  <p className="text-[11px] text-[var(--axiom-text-tertiary)] truncate">{s.entity_id}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-lg font-semibold text-[var(--axiom-text-primary)]">{(s.running_average * 100).toFixed(0)}%</span>
                    <span className={`text-[10px] ${s.trend === "up" ? "text-green-400" : s.trend === "down" ? "text-red-400" : "text-[var(--axiom-text-tertiary)]"}`}>
                      {s.trend === "up" ? "↑" : s.trend === "down" ? "↓" : "→"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}