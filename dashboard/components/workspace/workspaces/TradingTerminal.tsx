"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { system } from "../../../lib/api";
import type { WorkflowAnalytics, HealthSummary } from "../../../lib/api-types";

/* ── SVG icon helpers ──────────────────────────────────────────────── */

function IconArrow() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  );
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === "up") return <span className="text-green-400">↑</span>;
  if (trend === "down") return <span className="text-red-400">↓</span>;
  return <span className="text-[var(--axiom-text-tertiary)]">→</span>;
}

function SuccessBadge({ rate }: { rate: number }) {
  const color = rate >= 0.8 ? "bg-green-500/10 text-green-400" :
                rate >= 0.5 ? "bg-amber-500/10 text-amber-400" :
                "bg-red-500/10 text-red-400";
  return <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${color}`}>{(rate * 100).toFixed(0)}%</span>;
}

/* ── Trading Terminal ──────────────────────────────────────────────── */

export default function TradingTerminal() {
  const [analytics, setAnalytics] = useState<WorkflowAnalytics[]>([]);
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, wa] = await Promise.all([
        system.health(),
        system.getWorkflowAnalytics().catch(() => [] as WorkflowAnalytics[]),
      ]);
      setHealth(h);
      setAnalytics(wa);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load terminal data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, []);

  /* ── Metrics summary ───────────────────────────────────────────── */
  const totalRuns = analytics.reduce((s, a) => s + a.total_runs, 0);
  const avgSuccess = analytics.length
    ? analytics.reduce((s, a) => s + a.success_rate, 0) / analytics.length
    : 0;
  const avgDuration = analytics.length
    ? analytics.reduce((s, a) => s + a.avg_duration_seconds, 0) / analytics.length
    : 0;

  const METRICS = [
    { label: "Total Workflows", value: analytics.length.toString(), accent: "from-blue-500/20 to-cyan-500/20" },
    { label: "Total Runs", value: totalRuns.toLocaleString(), accent: "from-green-500/20 to-emerald-500/20" },
    { label: "Avg Success", value: `${(avgSuccess * 100).toFixed(0)}%`, accent: "from-purple-500/20 to-violet-500/20" },
    { label: "Avg Duration", value: `${avgDuration.toFixed(1)}s`, accent: "from-amber-500/20 to-orange-500/20" },
  ];

  /* ── Loading ────────────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 3, ease: "linear" as const }}>
            <IconArrow />
          </motion.div>
          <p className="text-sm text-[var(--axiom-text-tertiary)]">Initializing terminal...</p>
        </div>
      </div>
    );
  }

  /* ── Error ──────────────────────────────────────────────────────── */
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
          <button onClick={fetch} className="px-4 py-2 text-xs font-medium rounded-lg border border-[var(--axiom-border)] hover:bg-[var(--axiom-bg-elevated)] transition-colors">Reconnect</button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-[var(--axiom-text-primary)]">Trading Terminal</h2>
          {health && (
            <span className={`flex items-center gap-1 text-[10px] font-mono ${health.overall === "healthy" ? "text-green-400" : "text-red-400"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${health.overall === "healthy" ? "bg-green-400" : "bg-red-400"}`} />
              {health.overall}
            </span>
          )}
        </div>
        <button onClick={fetch} className="p-1.5 rounded-md text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors" title="Refresh">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Metric cards */}
        <div className="grid grid-cols-4 gap-3 p-6">
          {METRICS.map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-panel p-4"
            >
              <p className="text-[11px] text-[var(--axiom-text-tertiary)] mb-1">{m.label}</p>
              <p className="text-2xl font-semibold text-[var(--axiom-text-primary)]">{m.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Health bar */}
        {health && (
          <div className="px-6 pb-3">
            <div className="flex gap-3 text-[11px]">
              <span className="text-[var(--axiom-text-tertiary)]">
                <span className="text-green-400">●</span> {health.healthy} healthy
              </span>
              <span className="text-[var(--axiom-text-tertiary)]">
                <span className="text-amber-400">●</span> {health.degraded} degraded
              </span>
              <span className="text-[var(--axiom-text-tertiary)]">
                <span className="text-red-400">●</span> {health.unhealthy} unhealthy
              </span>
            </div>
          </div>
        )}

        {/* Analytics table */}
        <div className="px-6 pb-6">
          <h3 className="text-xs font-semibold text-[var(--axiom-text-secondary)] uppercase tracking-wide mb-3">Workflow Performance</h3>

          {analytics.length === 0 ? (
            <div className="text-center py-12">
              <IconArrow />
              <p className="text-sm text-[var(--axiom-text-tertiary)] mt-2">No analytics data available</p>
            </div>
          ) : (
            <div className="glass-panel overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[var(--axiom-border)]">
                    <th className="text-left py-3 px-4 text-[var(--axiom-text-tertiary)] font-medium">Workflow</th>
                    <th className="text-right py-3 px-4 text-[var(--axiom-text-tertiary)] font-medium">Success Rate</th>
                    <th className="text-right py-3 px-4 text-[var(--axiom-text-tertiary)] font-medium">Runs</th>
                    <th className="text-right py-3 px-4 text-[var(--axiom-text-tertiary)] font-medium">Avg Duration</th>
                    <th className="text-right py-3 px-4 text-[var(--axiom-text-tertiary)] font-medium">Avg Retries</th>
                    <th className="text-right py-3 px-4 text-[var(--axiom-text-tertiary)] font-medium">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.map((a, i) => (
                    <tr key={a.workflow_id} className="border-b border-[var(--axiom-border)]/50 hover:bg-[var(--axiom-bg-elevated)]/30 transition-colors">
                      <td className="py-3 px-4 text-[var(--axiom-text-primary)] font-mono">{a.workflow_id.slice(0, 20)}</td>
                      <td className="py-3 px-4 text-right"><SuccessBadge rate={a.success_rate} /></td>
                      <td className="py-3 px-4 text-right text-[var(--axiom-text-secondary)]">{a.total_runs}</td>
                      <td className="py-3 px-4 text-right text-[var(--axiom-text-secondary)]">{a.avg_duration_seconds.toFixed(1)}s</td>
                      <td className="py-3 px-4 text-right text-[var(--axiom-text-secondary)]">{a.avg_retries.toFixed(1)}</td>
                      <td className="py-3 px-4 text-right"><TrendIcon trend={a.trend} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}