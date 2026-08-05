"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { learning as learningApi } from "../../lib/api";
import type { WorkflowAnalytics } from "../../lib/api-types";

// ── WorkflowAnalyticsPanel ─────────────────────────────────────────────

export default function WorkflowAnalyticsPanel() {
  const [analytics, setAnalytics] = useState<WorkflowAnalytics[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const data = await learningApi.workflowAnalytics();
      setAnalytics((data as WorkflowAnalytics[]).sort((a, b) => a.success_rate - b.success_rate));
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          <span className="text-xs text-[var(--axiom-text-tertiary)]">Loading workflow analytics...</span>
        </div>
      </div>
    );
  }

  // Bottleneck identification
  const worstSuccessRate = analytics.filter((a) => a.total_runs > 0).slice(0, 3);
  const highestDuration = [...analytics].sort((a, b) => b.avg_duration_seconds - a.avg_duration_seconds).slice(0, 3);
  const mostRetries = [...analytics].sort((a, b) => b.avg_retries - a.avg_retries).slice(0, 3);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-2.5">
          <span className="text-sm">⚡</span>
          <h2 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Workflow Analytics</h2>
        </div>
        <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">
          {analytics.length} workflows tracked
        </span>
      </div>

      <div className="flex-1 overflow-y-auto scroll-smooth p-3 space-y-3">
        {/* Bottleneck alerts */}
        {worstSuccessRate.filter((w) => w.success_rate < 80).length > 0 && (
          <div className="glass-panel p-3 border border-red-400/20">
            <h3 className="text-[10px] font-medium text-red-400 mb-2 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
              Bottlenecks Detected
            </h3>
            <div className="space-y-1">
              {worstSuccessRate.filter((w) => w.success_rate < 80).map((w) => (
                <div key={w.workflow_id} className="flex items-center justify-between px-2 py-1.5 bg-red-400/5 rounded-md">
                  <span className="text-[10px] font-medium text-[var(--axiom-text-primary)]">{w.workflow_id}</span>
                  <span className="text-[10px] text-red-400">{w.success_rate.toFixed(0)}% success</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Insight cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <InsightCard title="Slowest" icon="🐢" items={highestDuration} format={(w) => `${w.avg_duration_seconds.toFixed(0)}s`} />
          <InsightCard title="Most Retries" icon="🔄" items={mostRetries} format={(w) => `${w.avg_retries.toFixed(1)} avg`} />
          <InsightCard title="Worst Success" icon="⚠️" items={worstSuccessRate} format={(w) => `${w.success_rate.toFixed(0)}%`} />
        </div>

        {/* Full list */}
        <div className="space-y-1.5">
          {analytics.map((w) => {
            const isExpanded = expanded === w.workflow_id;
            return (
              <div key={w.workflow_id} className="glass-panel overflow-hidden">
                <button
                  onClick={() => setExpanded(isExpanded ? null : w.workflow_id)}
                  className="w-full flex items-center gap-3 p-2.5 text-left"
                >
                  {/* Success rate bar */}
                  <div className="w-16 flex-shrink-0">
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          w.success_rate >= 80 ? "bg-emerald-400" :
                          w.success_rate >= 50 ? "bg-amber-400" : "bg-red-400"
                        }`}
                        style={{ width: `${w.success_rate}%` }}
                      />
                    </div>
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono mt-0.5 block">
                      {w.success_rate.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-[11px] font-medium text-[var(--axiom-text-primary)] truncate block">
                      {w.workflow_id}
                    </span>
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                      {w.total_runs} runs · {w.avg_duration_seconds.toFixed(0)}s avg · {w.avg_retries.toFixed(1)} retries
                    </span>
                  </div>
                  <span className={`text-[9px] font-medium ${
                    w.trend === "improving" ? "text-emerald-400" :
                    w.trend === "declining" ? "text-red-400" : "text-blue-400"
                  }`}>
                    {w.trend === "improving" ? "↑" : w.trend === "declining" ? "↓" : "→"}
                  </span>
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
                        <h4 className="text-[9px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wider">Failure Reasons</h4>
                        {Object.entries(w.failure_reasons || {}).length > 0 ? (
                          <div className="space-y-1">
                            {Object.entries(w.failure_reasons)
                              .sort(([, a], [, b]) => b - a)
                              .map(([reason, count]) => (
                                <div key={reason} className="flex items-center gap-2">
                                  <span className="flex-1 text-[10px] text-[var(--axiom-text-secondary)]">{reason}</span>
                                  <div className="h-2 rounded-full bg-white/5 overflow-hidden flex-1 max-w-[100px]">
                                    <div className="h-full rounded-full bg-red-400/60" style={{ width: `${Math.min(100, (count / w.total_runs) * 100)}%` }} />
                                  </div>
                                  <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono w-8 text-right">{count}</span>
                                </div>
                              ))}
                          </div>
                        ) : (
                          <p className="text-[10px] text-[var(--axiom-text-tertiary)]">No failures recorded</p>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── InsightCard ────────────────────────────────────────────────────────

function InsightCard({
  title,
  icon,
  items,
  format,
}: {
  title: string;
  icon: string;
  items: WorkflowAnalytics[];
  format: (w: WorkflowAnalytics) => string;
}) {
  return (
    <div className="glass-panel p-2.5">
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className="text-sm">{icon}</span>
        <span className="text-[10px] font-medium text-[var(--axiom-text-secondary)]">{title}</span>
      </div>
      {items.slice(0, 3).map((w, i) => (
        <div key={w.workflow_id} className="flex items-center justify-between py-0.5">
          <span className="text-[9px] text-[var(--axiom-text-primary)] truncate max-w-[120px]">{w.workflow_id}</span>
          <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">{format(w)}</span>
        </div>
      ))}
    </div>
  );
}