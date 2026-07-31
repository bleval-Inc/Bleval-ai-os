"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system, instances as apiInstances } from "../../../lib/api";
import type { RuntimeStatus, WorkflowInstance } from "../../../lib/api-types";

const stagger = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const slideUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" as const } },
};

function sc(s: string) {
  if (s === "running" || s === "completed") return "text-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.3)]";
  if (s === "failed" || s === "error") return "text-red-400 shadow-[0_0_8px_rgba(248,113,113,0.3)]";
  if (s === "paused" || s === "pending") return "text-amber-400";
  return "text-gray-500";
}

function Dot({ s }: { s: string }) {
  return <span className={`inline-block w-2 h-2 rounded-full bg-current ${sc(s)}`} />;
}

function Loading() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" as const }}
          className="w-8 h-8 border-2 border-[var(--axiom-border)] border-t-[var(--axiom-accent)] rounded-full mx-auto mb-4" />
        <p className="text-sm text-[var(--axiom-text-tertiary)] font-mono">Establishing telemetry link...</p>
      </div>
    </div>
  );
}

function ErrorState({ msg, retry }: { msg: string; retry: () => void }) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-md text-center">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-4 text-red-400">
          <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)] mb-2">Telemetry Offline</h3>
        <p className="text-xs text-[var(--axiom-text-tertiary)] mb-4 font-mono">{msg}</p>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={retry}
          className="px-4 py-1.5 text-xs font-medium text-[var(--axiom-accent)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors">
          Re-establish Link
        </motion.button>
      </div>
    </div>
  );
}

function Metric({ l, v, a }: { l: string; v: number | string; a: string }) {
  return (
    <motion.div variants={slideUp}
      className="flex-1 min-w-0 rounded-lg border border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]/50 backdrop-blur-sm px-4 py-3">
      <p className="text-[10px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wider mb-1">{l}</p>
      <p className={`text-lg font-bold font-mono ${a}`}>{v}</p>
    </motion.div>
  );
}

function CompCard({ n, on }: { n: string; on: boolean }) {
  return (
    <motion.div variants={slideUp}
      className="rounded-lg border border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]/40 backdrop-blur-sm px-3 py-3 flex items-center gap-3">
      <Dot s={on ? "running" : "failed"} />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-[var(--axiom-text-primary)] truncate">{n}</p>
        <p className={`text-[10px] font-mono ${on ? "text-emerald-500" : "text-red-400"}`}>{on ? "Online" : "Offline"}</p>
      </div>
    </motion.div>
  );
}

function WFRow({ w }: { w: WorkflowInstance }) {
  return (
    <motion.div variants={slideUp}
      className="flex items-center gap-3 px-4 py-2.5 rounded-lg border border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]/30 backdrop-blur-sm">
      <Dot s={w.status} />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-[var(--axiom-text-primary)] truncate">{w.workflow_id}</p>
        <p className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono">{w.instance_id.slice(0, 12)}...</p>
      </div>
      <span className={`text-[10px] font-semibold font-mono px-2 py-0.5 rounded-full border border-current`}>
        {w.status}
      </span>
      <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono whitespace-nowrap">
        {w.current_step}/{w.total_steps}
      </span>
    </motion.div>
  );
}

export default function OperationsCenter() {
  const { runtime, setRuntime } = useAxiomStore();
  const [workflows, setWorkflows] = useState<WorkflowInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [status, wfList] = await Promise.all([system.status(), apiInstances.list()]);
      setRuntime(status);
      setWorkflows(wfList);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection lost");
    } finally {
      setLoading(false);
    }
  }, [setRuntime]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading && !runtime) return <Loading />;
  if (error && !runtime) return <ErrorState msg={error} retry={fetchData} />;

  const rs = runtime as RuntimeStatus;
  const healthy = rs.health?.overall === "healthy";
  const comps = Object.entries(rs.components ?? {});

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className={`rounded-xl border px-5 py-4 flex items-center gap-4 ${healthy ? "border-emerald-500/30 bg-emerald-500/5" : "border-red-500/30 bg-red-500/5"}`}>
          <span className={`flex-shrink-0 w-3 h-3 rounded-full ${healthy ? "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.6)]" : "bg-red-400 shadow-[0_0_12px_rgba(248,113,113,0.6)] animate-pulse"}`} />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[var(--axiom-text-primary)]">
              {healthy ? "All Systems Operational" : "System Degraded"}
            </p>
            <p className="text-xs text-[var(--axiom-text-tertiary)] font-mono">
              v{rs.version} &middot; {rs.initialised ? "Initialised" : "Booting"}
              {rs.health?.last_check ? ` &middot; Last check: ${new Date(rs.health.last_check).toLocaleTimeString()}` : ""}
            </p>
          </div>
        </motion.div>

        <motion.div variants={stagger} initial="hidden" animate="visible" className="flex gap-3">
          <Metric l="Workflows Defined" v={rs.workflows_defined} a="text-cyan-400" />
          <Metric l="Executives" v={rs.executives} a="text-violet-400" />
          <Metric l="Organizations" v={rs.org_count} a="text-emerald-400" />
          <Metric l="Health" v={`${rs.health?.healthy ?? "?"}/${rs.health?.total ?? "?"}`} a="text-amber-400" />
        </motion.div>

        {comps.length > 0 && (
          <div>
            <h3 className="text-[11px] font-semibold text-[var(--axiom-text-tertiary)] uppercase tracking-wider mb-3">Components</h3>
            <motion.div variants={stagger} initial="hidden" animate="visible" className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {comps.map(([n, on]) => <CompCard key={n} n={n} on={on} />)}
            </motion.div>
          </div>
        )}
        {comps.length === 0 && (
          <div className="rounded-lg border border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]/30 p-6 text-center">
            <p className="text-xs text-[var(--axiom-text-tertiary)] font-mono">No component telemetry available</p>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[11px] font-semibold text-[var(--axiom-text-tertiary)] uppercase tracking-wider">Active Workflows</h3>
            {workflows.length > 0 && <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)]">{workflows.length} instance{workflows.length !== 1 ? "s" : ""}</span>}
          </div>
          <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-1.5">
            {workflows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] mb-3">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" />
                </svg>
                <p className="text-xs text-[var(--axiom-text-tertiary)]">No active workflows</p>
                <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-1 opacity-60">Launch a workflow to see it here</p>
              </div>
            ) : workflows.map((w) => <WFRow key={w.instance_id} w={w} />)}
          </motion.div>
        </div>
      </div>
    </div>
  );
}