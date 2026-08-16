"use client";

import { motion } from "framer-motion";
import { SkeletonRow } from "../Skeletons";
import { EmptyState } from "../States";

interface CommandCenterLearningProps {
  recommendations: { id: string; title: string; confidence: number; expected_impact: string }[];
  patterns: { id: string; title: string; severity: string; frequency: number }[];
  knowledge: { id: string; title: string }[];
  loading: boolean;
  error: string | null;
  onNavigate: () => void;
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-500/10 text-red-400",
    warning: "bg-amber-500/10 text-amber-400",
    info: "bg-blue-500/10 text-blue-400",
  };
  return (
    <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-medium uppercase ${colors[severity] || colors.info}`}>
      {severity}
    </span>
  );
}

export default function CommandCenterLearning({
  recommendations,
  patterns,
  knowledge,
  loading,
  error,
  onNavigate,
}: CommandCenterLearningProps) {
  if (loading && !recommendations.length && !patterns.length) {
    return (
      <div className="glass-card p-4">
        <div className="h-4 w-1/2 rounded bg-[var(--axiom-bg-elevated)] mb-3" />
        <SkeletonRow /><SkeletonRow />
      </div>
    );
  }

  if (error && !recommendations.length && !patterns.length) {
    return (
      <div className="glass-card p-4">
        <p className="text-xs text-[var(--axiom-error)]">{error}</p>
      </div>
    );
  }

  const hasData = recommendations.length > 0 || patterns.length > 0 || knowledge.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: 0.1 }}
      className="glass-card p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Recent Intelligence</h3>
        <button onClick={onNavigate} className="text-[9px] text-[var(--axiom-accent)] hover:underline">View All</button>
      </div>

      {!hasData ? (
        <EmptyState
          title="No learning data yet"
          description="Patterns and recommendations will appear here as AXIOM gains experience."
          className="py-6"
        />
      ) : (
        <div className="space-y-3">
          {recommendations.slice(0, 2).map((r) => (
            <div key={r.id} className="px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)]">
              <div className="flex items-center justify-between">
                <p className="text-xs text-[var(--axiom-text-primary)] font-medium truncate">{r.title}</p>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1 rounded-full bg-[var(--axiom-bg-base)] overflow-hidden">
                  <div className="h-full rounded-full bg-[var(--axiom-accent)]" style={{ width: `${Math.round(r.confidence * 100)}%` }} />
                </div>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{Math.round(r.confidence * 100)}%</span>
              </div>
            </div>
          ))}
          {patterns.slice(0, 2).map((p) => (
            <div key={p.id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)]">
              <div className="flex items-center gap-2">
                <SeverityBadge severity={p.severity} />
                <span className="text-xs text-[var(--axiom-text-primary)]">{p.title}</span>
              </div>
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">×{p.frequency}</span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}