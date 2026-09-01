"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type Notification } from "../../lib/store/axiom-store";
import { learning as learningApi } from "../../lib/api";
import type {
  LearningStatus,
  LearningPattern,
  LearningRecommendation,
  KnowledgeEntry,
  LearningCycle,
  PerformanceScore,
} from "../../lib/api-types";

// Types

type LearningTab = "overview" | "patterns" | "recommendations" | "knowledge" | "cycles";

// Severity config

const SEVERITY_CONFIG: Record<string, { color: string; bg: string }> = {
  info: { color: "text-blue-400", bg: "bg-blue-400/10" },
  warning: { color: "text-amber-400", bg: "bg-amber-400/10" },
  critical: { color: "text-red-400", bg: "bg-red-400/10" },
  optimization: { color: "text-violet-400", bg: "bg-violet-400/10" },
};

const SCORE_COLORS: Record<string, string> = {
  improving: "text-emerald-400",
  declining: "text-red-400",
  stable: "text-blue-400",
};

// LearningPanel

export default function LearningPanel() {
  const {
    learningStatus,
    learningPatterns,
    learningRecommendations,
    learningKnowledge,
    learningCycles,
    performanceScores,
    setLearningStatus,
    setLearningPatterns,
    setLearningRecommendations,
    setLearningKnowledge,
    setLearningCycles,
    setPerformanceScores,
    selectedLearningTab,
    setSelectedLearningTab,
    addNotification,
  } = useAxiomStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [status, patterns, recs, knowledge, cycles, scores] = await Promise.all([
        learningApi.status().catch(() => null),
        learningApi.patterns().catch(() => []),
        learningApi.recommendations().catch(() => []),
        learningApi.knowledge().catch(() => []),
        learningApi.cycles().catch(() => []),
        learningApi.scores().catch(() => []),
      ]);

      if (status) setLearningStatus(status as LearningStatus);
      setLearningPatterns(patterns as LearningPattern[]);
      setLearningRecommendations(recs as LearningRecommendation[]);
      setLearningKnowledge(knowledge as KnowledgeEntry[]);
      setLearningCycles(cycles as LearningCycle[]);
      setPerformanceScores(scores as PerformanceScore[]);
      setError(null);
    } catch {
      setError("Failed to load learning data");
    } finally {
      setLoading(false);
    }
  }, [setLearningStatus, setLearningPatterns, setLearningRecommendations, setLearningKnowledge, setLearningCycles, setPerformanceScores]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const tabs: { id: LearningTab; label: string; icon: string }[] = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "patterns", label: "Patterns", icon: "🔍" },
    { id: "recommendations", label: "Recommendations", icon: "💡" },
    { id: "knowledge", label: "Knowledge", icon: "📚" },
    { id: "cycles", label: "Cycles", icon: "🔄" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
          <span className="text-xs text-[var(--axiom-text-tertiary)]">Loading Learning Engine...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-2.5">
          <span className="text-sm">🧠</span>
          <h2 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Learning Engine</h2>
        </div>
        {learningStatus && (
          <div className="flex items-center gap-2 text-[9px] text-[var(--axiom-text-tertiary)] font-mono">
            <span>{learningStatus.total_learning_cycles} cycles</span>
            {learningStatus.pending_recommendations > 0 && (
              <span className="text-amber-400">{learningStatus.pending_recommendations} pending</span>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--axiom-border)] overflow-x-auto scrollbar-none">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedLearningTab(tab.id)}
            className={`flex items-center gap-1.5 px-3.5 py-2 text-[10px] font-medium transition-colors relative whitespace-nowrap ${
              selectedLearningTab === tab.id
                ? "text-violet-400"
                : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            }`}
          >
            <span className="text-[11px]">{tab.icon}</span>
            {tab.label}
            {tab.id === "patterns" && learningPatterns.length > 0 && (
              <span className="px-1 py-0.5 text-[7px] font-bold text-amber-400 bg-amber-400/10 rounded-full">
                {learningPatterns.length}
              </span>
            )}
            {tab.id === "recommendations" && learningRecommendations.length > 0 && (
              <span className="px-1 py-0.5 text-[7px] font-bold text-violet-400 bg-violet-400/10 rounded-full">
                {learningRecommendations.length}
              </span>
            )}
            {selectedLearningTab === tab.id && (
              <motion.div layoutId="learn-tab-underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-violet-400" />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scroll-smooth">
        {error && (
          <div className="p-4 text-[11px] text-red-400 bg-red-400/5 border-b border-red-400/10">
            {error} — <button onClick={fetchAll} className="underline">retry</button>
          </div>
        )}

        {selectedLearningTab === "overview" && (
          <OverviewTab status={learningStatus} scores={performanceScores} fetchAll={fetchAll} />
        )}
        {selectedLearningTab === "patterns" && (
          <PatternsTab patterns={learningPatterns} />
        )}
        {selectedLearningTab === "recommendations" && (
          <RecommendationsTab
            recommendations={learningRecommendations}
            addNotification={addNotification}
          />
        )}
        {selectedLearningTab === "knowledge" && (
          <KnowledgeTab entries={learningKnowledge} />
        )}
        {selectedLearningTab === "cycles" && (
          <CyclesTab cycles={learningCycles} />
        )}
      </div>
    </div>
  );
}

// Overview Tab

function OverviewTab({
  status,
  scores,
  fetchAll,
}: {
  status: LearningStatus | null;
  scores: PerformanceScore[];
  fetchAll: () => void;
}) {
  const items = status
    ? [
        { label: "Learning Cycles", value: status.total_learning_cycles, icon: "🔄" },
        { label: "Patterns Detected", value: status.total_patterns_detected, icon: "🔍" },
        { label: "Recommendations", value: status.total_recommendations, icon: "💡" },
        { label: "Knowledge Entries", value: status.total_knowledge_entries, icon: "📚" },
      ]
    : [];

  return (
    <div className="p-3 space-y-4">
      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {items.map((item) => (
          <div key={item.label} className="glass-panel p-3 text-center">
            <span className="text-lg">{item.icon}</span>
            <p className="text-lg font-bold text-[var(--axiom-text-primary)] mt-1">{item.value}</p>
            <p className="text-[9px] text-[var(--axiom-text-tertiary)]">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Active indicators */}
      <div className="flex items-center gap-3 flex-wrap">
        {status && status.active_patterns > 0 && (
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-md">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            {status.active_patterns} active pattern{status.active_patterns > 1 ? "s" : ""}
          </div>
        )}
        {status && status.pending_recommendations > 0 && (
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] text-violet-400 bg-violet-400/10 border border-violet-400/20 rounded-md">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            {status.pending_recommendations} pending recommendation{status.pending_recommendations > 1 ? "s" : ""}
          </div>
        )}
        <button
          onClick={() => learningApi.runCycle()}
          className="px-2.5 py-1.5 text-[10px] font-medium text-violet-400 bg-violet-400/10 border border-violet-400/20 rounded-md hover:bg-violet-400/20 transition-colors"
        >
          Run Learning Cycle
        </button>
      </div>

      {/* Performance scores */}
      {scores.length > 0 && (
        <div>
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Executive Performance</h3>
          <div className="space-y-1.5">
            {scores.map((s) => (
              <div key={s.entity_id} className="glass-panel p-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    s.entity_id === "jenson" ? "bg-blue-400" :
                    s.entity_id === "valta_prime" ? "bg-amber-400" :
                    s.entity_id === "yamako" ? "bg-violet-400" :
                    "bg-indigo-400"
                  }`} />
                  <span className="text-[11px] font-medium text-[var(--axiom-text-primary)]">
                    {s.entity_id === "valta_prime" ? "Valta Prime" : s.entity_id.charAt(0).toUpperCase() + s.entity_id.slice(1)}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--axiom-text-primary)]">
                    {typeof s.running_average === "number" ? s.running_average.toFixed(1) : "—"}
                  </span>
                  <span className={`text-[10px] font-medium ${SCORE_COLORS[s.trend] ?? "text-blue-400"}`}>
                    {s.trend === "improving" ? "↑" : s.trend === "declining" ? "↓" : "→"}
                    {" "}{s.trend}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Patterns Tab

function PatternsTab({ patterns }: { patterns: LearningPattern[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (patterns.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-2">
        <span className="text-3xl opacity-30">🔍</span>
        <p className="text-xs text-[var(--axiom-text-tertiary)]">No patterns detected yet</p>
        <p className="text-[9px] text-[var(--axiom-text-tertiary)] opacity-60">Patterns appear after learning cycles complete</p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-1.5">
      {patterns.map((p) => {
        const sev = SEVERITY_CONFIG[p.severity] ?? SEVERITY_CONFIG.info;
        const isExpanded = expanded === p.pattern_id;

        return (
          <div key={p.pattern_id} className="glass-panel overflow-hidden">
            <button
              onClick={() => setExpanded(isExpanded ? null : p.pattern_id)}
              className="w-full flex items-center gap-3 p-2.5 text-left"
            >
              <span className={`px-1.5 py-0.5 text-[8px] font-medium rounded-full ${sev.color} ${sev.bg}`}>
                {p.severity}
              </span>
              <div className="flex-1 min-w-0">
                <span className="text-[11px] font-medium text-[var(--axiom-text-primary)] truncate block">
                  {p.title}
                </span>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                  {p.pattern_type} · {p.frequency}x · impact {Math.round(p.impact_score * 100)}%
                </span>
              </div>
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{isExpanded ? "▲" : "▼"}</span>
            </button>

            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-[var(--axiom-border)]"
                >
                  <div className="p-2.5 space-y-2">
                    <p className="text-[10px] text-[var(--axiom-text-secondary)]">{p.description}</p>
                    {p.entities_involved.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {p.entities_involved.map((e) => (
                          <span key={e} className="px-1.5 py-0.5 text-[8px] font-medium text-[var(--axiom-text-tertiary)] bg-white/5 rounded-md">
                            {e}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center gap-3 text-[8px] text-[var(--axiom-text-tertiary)] font-mono">
                      <span>First: {new Date(p.first_detected).toLocaleDateString()}</span>
                      <span>Last: {new Date(p.last_detected).toLocaleDateString()}</span>
                    </div>
                    {/* Impact bar */}
                    <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-violet-400/60"
                        style={{ width: `${Math.min(100, p.impact_score * 100)}%` }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

// Recommendations Tab

function RecommendationsTab({
  recommendations,
  addNotification,
}: {
  recommendations: LearningRecommendation[];
  addNotification: (n: Notification) => void;
}) {
  const STATUS_COLORS: Record<string, string> = {
    draft: "text-gray-400 border-gray-400/30 bg-gray-400/10",
    proposed: "text-amber-400 border-amber-400/30 bg-amber-400/10",
    approved: "text-green-400 border-green-400/30 bg-green-400/10",
    applied: "text-blue-400 border-blue-400/30 bg-blue-400/10",
    rejected: "text-red-400 border-red-400/30 bg-red-400/10",
    superseded: "text-violet-400 border-violet-400/30 bg-violet-400/10",
  };

  if (recommendations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-2">
        <span className="text-3xl opacity-30">💡</span>
        <p className="text-xs text-[var(--axiom-text-tertiary)]">No recommendations yet</p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-1.5">
      {recommendations.map((r) => {
        const sc = STATUS_COLORS[r.status] ?? STATUS_COLORS.draft;
        return (
          <div key={r.recommendation_id} className="glass-panel p-2.5">
            <div className="flex items-start gap-2.5">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-medium text-[var(--axiom-text-primary)]">{r.title}</span>
                  <span className={`px-1.5 py-0.5 text-[8px] font-medium border rounded-full ${sc}`}>
                    {r.status}
                  </span>
                </div>
                <p className="text-[10px] text-[var(--axiom-text-secondary)] mt-0.5">{r.description}</p>
                <div className="flex items-center gap-2.5 mt-1.5 flex-wrap">
                  {r.change_type && (
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                      Type: {r.change_type}
                    </span>
                  )}
                  <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                    Confidence: {Math.round(r.confidence * 100)}%
                  </span>
                  {r.expected_impact && (
                    <span className="text-[9px] text-violet-400">Impact: {r.expected_impact}</span>
                  )}
                  {r.status === "draft" && (
                    <button className="px-2 py-0.5 text-[9px] font-medium text-green-400 bg-green-400/10 border border-green-400/20 rounded-md hover:bg-green-400/20 transition-colors">
                      Apply
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Knowledge Tab

function KnowledgeTab({ entries }: { entries: KnowledgeEntry[] }) {
  const [search, setSearch] = useState("");

  const filtered = entries.filter(
    (e) =>
      e.title.toLowerCase().includes(search.toLowerCase()) ||
      e.tags.some((t) => t.toLowerCase().includes(search.toLowerCase())),
  );

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-2">
        <span className="text-3xl opacity-30">📚</span>
        <p className="text-xs text-[var(--axiom-text-tertiary)]">No knowledge entries yet</p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-2">
      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search knowledge..."
        className="w-full px-3 py-2 text-[11px] bg-white/5 border border-[var(--axiom-border)] rounded-md text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] focus:outline-none focus:border-violet-400/40"
      />

      <div className="space-y-1.5">
        {filtered.map((entry) => (
          <div key={entry.entry_id} className="glass-panel p-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium text-[var(--axiom-text-primary)]">{entry.title}</span>
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                {Math.round(entry.confidence * 100)}% confidence
              </span>
            </div>
            <p className="text-[10px] text-[var(--axiom-text-secondary)] mt-1">{entry.content}</p>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-[8px] text-[var(--axiom-text-tertiary)] font-mono">Source: {entry.source}</span>
              {entry.tags.length > 0 && (
                <div className="flex gap-1">
                  {entry.tags.map((tag) => (
                    <span key={tag} className="px-1.5 py-0.5 text-[8px] text-[var(--axiom-text-tertiary)] bg-white/5 rounded-md">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Cycles Tab

function CyclesTab({ cycles }: { cycles: LearningCycle[] }) {
  if (cycles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-2">
        <span className="text-3xl opacity-30">🔄</span>
        <p className="text-xs text-[var(--axiom-text-tertiary)]">No learning cycles recorded</p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-1.5">
      {cycles.map((c) => (
        <div key={c.cycle_id} className="glass-panel p-2.5 flex items-center gap-3">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${c.success ? "bg-emerald-400" : "bg-red-400"}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-[var(--axiom-text-primary)]">
                {c.source_entity}
              </span>
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                Score: {typeof c.scores === "number" ? c.scores.toFixed(1) : c.scores}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5 text-[9px] text-[var(--axiom-text-tertiary)]">
              <span>Patterns: {c.patterns_detected}</span>
              <span>Recs: {c.recommendations}</span>
              <span>Knowledge: {c.knowledge_written}</span>
              <span>{c.duration_seconds.toFixed(0)}s</span>
              {c.completed_at && (
                <span>{new Date(c.completed_at).toLocaleDateString()}</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}