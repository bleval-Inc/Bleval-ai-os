"use client";

import { useEffect, useState, useCallback } from "react";
import { qc as qcApi } from "../../lib/api";
import type { QCResultSummary } from "../../lib/api-types";

// ── QC Learning Panel ──────────────────────────────────────────────────
// Visualizes QC failures as learning signals — connects QC to Learning.

interface FailureTypeCount {
  type: string;
  count: number;
  workflows: Record<string, number>;
}

// ── Severity colors ─────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-400/10 border-red-400/20",
  high: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  medium: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  low: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  info: "text-gray-400 bg-gray-400/10 border-gray-400/20",
};

// ── QCLearningPanel ────────────────────────────────────────────────────

export default function QCLearningPanel() {
  const [results, setResults] = useState<QCResultSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedScope, setSelectedScope] = useState<string>("all");

  const fetchData = useCallback(async () => {
    try {
      const data = await qcApi.results(50);
      setResults(data as QCResultSummary[]);
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
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="text-xs text-[var(--axiom-text-tertiary)]">Loading QC data...</span>
        </div>
      </div>
    );
  }

  const failed = results.filter((r) => !r.passed);
  const passed = results.filter((r) => r.passed);
  const passRate = results.length > 0 ? Math.round((passed.length / results.length) * 100) : 0;
  const trend = passRate >= 70 ? "improving" : passRate >= 40 ? "stable" : "declining";

  // Aggregate failure types across all failed results
  const failureTypes: FailureTypeCount[] = [];
  const typeMap = new Map<string, FailureTypeCount>();

  for (const r of failed) {
    const findings = (r as any).findings;
    if (Array.isArray(findings)) {
      for (const f of findings) {
        const key = f.check_type || "unknown";
        let entry = typeMap.get(key);
        if (!entry) {
          entry = { type: key, count: 0, workflows: {} };
          typeMap.set(key, entry);
        }
        entry.count++;
        const workflowKey = (r as any).artifact_name || (r as any).artifact_type || "unknown";
        entry.workflows[workflowKey] = (entry.workflows[workflowKey] || 0) + 1;
      }
    }
  }
  failureTypes.push(...typeMap.values());
  failureTypes.sort((a, b) => b.count - a.count);

  const filteredFailureTypes = selectedScope === "all"
    ? failureTypes
    : failureTypes.filter((ft) => Object.keys(ft.workflows).some((w) => w === selectedScope));

  const scopes = [...new Set(results.map((r) => r.scope || "unknown"))];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-2.5">
          <span className="text-sm">🔬</span>
          <h2 className="text-xs font-semibold text-[var(--axiom-text-primary)]">QC Learning</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[9px] font-medium ${
            trend === "improving" ? "text-emerald-400" :
            trend === "declining" ? "text-red-400" : "text-amber-400"
          }`}>
            {passRate}% pass rate · {trend}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scroll-smooth p-3 space-y-3">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="glass-panel p-2.5 text-center">
            <span className="text-lg font-bold text-[var(--axiom-text-primary)]">{results.length}</span>
            <p className="text-[8px] text-[var(--axiom-text-tertiary)]">Total QC Checks</p>
          </div>
          <div className="glass-panel p-2.5 text-center">
            <span className="text-lg font-bold text-emerald-400">{passed.length}</span>
            <p className="text-[8px] text-[var(--axiom-text-tertiary)]">Passed</p>
          </div>
          <div className="glass-panel p-2.5 text-center">
            <span className="text-lg font-bold text-red-400">{failed.length}</span>
            <p className="text-[8px] text-[var(--axiom-text-tertiary)]">Failed</p>
          </div>
        </div>

        {/* Trend indicator */}
        <div className="glass-panel p-2.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[9px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">Quality Trend</span>
            <span className={`text-[9px] font-medium ${
              passRate >= 80 ? "text-emerald-400" :
              passRate >= 50 ? "text-amber-400" : "text-red-400"
            }`}>
              {passRate >= 80 ? "Healthy" : passRate >= 50 ? "Needs attention" : "Critical"}
            </span>
          </div>
          <div className="h-2 rounded-full bg-white/5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                passRate >= 80 ? "bg-emerald-400" :
                passRate >= 50 ? "bg-amber-400" : "bg-red-400"
              }`}
              style={{ width: `${passRate}%` }}
            />
          </div>
        </div>

        {/* Scope filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
          <button
            onClick={() => setSelectedScope("all")}
            className={`px-2 py-1 text-[9px] font-medium rounded-md whitespace-nowrap transition-colors ${
              selectedScope === "all"
                ? "text-amber-400 bg-amber-400/10"
                : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            }`}
          >
            All Scopes
          </button>
          {scopes.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedScope(s)}
              className={`px-2 py-1 text-[9px] font-medium rounded-md whitespace-nowrap transition-colors ${
                selectedScope === s
                  ? "text-amber-400 bg-amber-400/10"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
              }`}
            >
              {s.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {/* Most common failure types */}
        {filteredFailureTypes.length > 0 && (
          <div>
            <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">
              Failure Patterns — Learning Signals
            </h3>
            <div className="space-y-1.5">
              {filteredFailureTypes.slice(0, 10).map((ft) => (
                <div key={ft.type} className="glass-panel p-2.5">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                      <span className="text-[10px] font-medium text-[var(--axiom-text-primary)]">
                        {ft.type.replace(/_/g, " ")}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold text-red-400">{ft.count}x</span>
                  </div>
                  {/* Workflow breakdown */}
                  <div className="space-y-0.5">
                    {Object.entries(ft.workflows)
                      .sort(([, a], [, b]) => b - a)
                      .map(([wf, cnt]) => (
                        <div key={wf} className="flex items-center gap-2 pl-4">
                          <span className="flex-1 text-[9px] text-[var(--axiom-text-tertiary)] truncate">{wf}</span>
                          <div className="h-1.5 rounded-full bg-white/5 overflow-hidden flex-1 max-w-[80px]">
                            <div
                              className="h-full rounded-full bg-red-400/50"
                              style={{ width: `${Math.min(100, (cnt / ft.count) * 100)}%` }}
                            />
                          </div>
                          <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">{cnt}</span>
                        </div>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {filteredFailureTypes.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 gap-2">
            <span className="text-3xl opacity-30">✅</span>
            <p className="text-xs text-[var(--axiom-text-tertiary)]">No QC failures — clean slate</p>
            <p className="text-[9px] text-[var(--axiom-text-tertiary)] opacity-60">
              Learning signals will appear as QC checks run
            </p>
          </div>
        )}
      </div>
    </div>
  );
}