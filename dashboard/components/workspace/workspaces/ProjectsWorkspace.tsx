"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { system, workflows, instances } from "../../../lib/api";
import type { Workflow, WorkflowInstance } from "../../../lib/api-types";

function fmt(raw: string) {
  return new Date(raw).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

type TabId = "all" | "running" | "completed" | "failed";
const TABS: { id: TabId; label: string }[] = [
  { id: "all", label: "All" }, { id: "running", label: "Running" },
  { id: "completed", label: "Completed" }, { id: "failed", label: "Failed" },
];
const TAB_FILTER: Record<TabId, (s: string) => boolean> = {
  all: () => true, running: (s) => s.toLowerCase() === "running",
  completed: (s) => s.toLowerCase() === "completed", failed: (s) => s.toLowerCase() === "failed",
};

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const c = s === "running" ? "bg-[var(--axiom-info)]/10 text-[var(--axiom-info)]"
    : s === "completed" ? "bg-[var(--axiom-success)]/10 text-[var(--axiom-success)]"
    : s === "failed" ? "bg-[var(--axiom-error)]/10 text-[var(--axiom-error)]"
    : "bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)]";
  return <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${c}`}>{status}</span>;
}

function StepPct({ cur, tot }: { cur: number; tot: number }) {
  const pct = tot > 0 ? Math.round((cur / tot) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-[var(--axiom-bg-elevated)] overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: "easeOut" as const }}
          className="h-full rounded-full bg-[var(--axiom-accent)]" />
      </div>
      <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)]">{cur}/{tot}</span>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span key={i} className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse"
              style={{ animationDelay: `${i * 200}ms` }} />
          ))}
        </div>
        <p className="text-xs text-[var(--axiom-text-tertiary)]">Loading projects...</p>
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
          <circle cx="12" cy="12" r="10" /><path d="m15 9-6 6" /><path d="m9 9 6 6" />
        </svg>
        <p className="text-sm text-[var(--axiom-error)] mb-2">Failed to load workflows</p>
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

function WfCard({ inst, wf }: { inst: WorkflowInstance; wf: Workflow | undefined }) {
  const dep = <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></svg>;
  const org = <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>;
  return (
    <motion.div layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-medium text-[var(--axiom-text-primary)] truncate">
            {wf?.description || inst.workflow_id}
          </h4>
          <p className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] mt-0.5">
            {inst.instance_id.slice(0, 12)}...
          </p>
        </div>
        <StatusBadge status={inst.status} />
      </div>
      <StepPct cur={inst.current_step} tot={inst.total_steps} />
      <div className="flex items-center justify-between text-[10px] text-[var(--axiom-text-tertiary)]">
        <div className="flex items-center gap-3">
          {wf?.department && <span className="flex items-center gap-1">{dep}{wf.department}</span>}
          {wf?.org && <span className="flex items-center gap-1">{org}{wf.org}</span>}
        </div>
        <span>{fmt(inst.created_at)}</span>
      </div>
    </motion.div>
  );
}

export default function ProjectsWorkspace() {
  const [wfList, setWorkflows] = useState<Workflow[]>([]);
  const [instList, setInstances] = useState<WorkflowInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("all");

  const fetchAll = async () => {
    setLoading(true); setError(null);
    try {
      const [w, i] = await Promise.all([workflows.list(), instances.list()]);
      setWorkflows(w); setInstances(i);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Unknown error"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const wfMap = useMemo(() => new Map(wfList.map((w) => [w.id, w])), [wfList]);
  const visible = useMemo(() => instList.filter((i) => TAB_FILTER[tab](i.status)), [instList, tab]);

  if (loading) return <Skeleton />;
  if (error) return <ErrorPanel msg={error} onRetry={fetchAll} />;

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <h2 className="text-sm font-medium text-[var(--axiom-text-primary)]">Projects Hub</h2>
        <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono">{instList.length} instances</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full px-6 py-5 space-y-5">
          <div className="flex gap-1 p-1 rounded-md bg-[var(--axiom-bg-elevated)] neumorph">
            {TABS.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  tab === t.id
                    ? "bg-[var(--axiom-bg-surface)] text-[var(--axiom-text-primary)] shadow-sm"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
                }`}>{t.label}</button>
            ))}
          </div>

          {visible.length === 0 && (
            <div className="flex flex-col items-center py-16 text-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                className="text-[var(--axiom-text-tertiary)] mb-3">
                <rect x="3" y="3" width="18" height="18" rx="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" />
              </svg>
              <p className="text-sm text-[var(--axiom-text-secondary)]">
                {tab === "all" ? "No workflow instances yet" : `No ${tab} workflows`}
              </p>
              <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">
                {tab === "all" ? "Launch a workflow from the Operations Center" : "No instances match this status filter"}
              </p>
            </div>
          )}

          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {visible.map((inst) => <WfCard key={inst.instance_id} inst={inst} wf={wfMap.get(inst.workflow_id)} />)}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}