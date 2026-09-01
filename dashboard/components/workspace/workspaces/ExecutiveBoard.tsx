"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { executives } from "../../../lib/api";
import type { ExecutiveBoardStatus } from "../../../lib/api-types";

/* Constants */

const EXEC_META: Record<string, { name: string; icon: React.ReactNode }> = {
  jenson: {
    name: "Jenson",
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>,
  },
  valta_prime: {
    name: "Valta Prime",
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="12 2 22 22 2 22 12 2"/></svg>,
  },
  yamako: {
    name: "Yamako",
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4Z"/><path d="M2 22v-2a6 6 0 0 1 6-6h8a6 6 0 0 1 6 6v2"/></svg>,
  },
};

const STATUS_COLORS: Record<string, { bg: string; shadow: string }> = {
  running: { bg: "var(--axiom-success)", shadow: "0 0 8px var(--axiom-success)" },
  error: { bg: "var(--axiom-error)", shadow: "none" },
  stopped: { bg: "var(--axiom-text-tertiary)", shadow: "none" },
};

function fmt(iso?: string) {
  if (!iso) return "Never";
  try { return new Date(iso).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }); }
  catch { return iso; }
}

/* Executive Card */

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

function ExecCard({ id, data, onToggle, toggling }: {
  id: string; data: ExecutiveBoardStatus[string]; onToggle: () => void; toggling: boolean;
}) {
  const meta = EXEC_META[id];
  const nm = meta?.name ?? id;
  const running = data.status === "running";
  const sc = STATUS_COLORS[data.status] ?? STATUS_COLORS.stopped;
  const schedKeys = Object.keys(data.schedules);

  return (
    <motion.div layout variants={cardVariants}
      whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
      className="glass-panel p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[var(--axiom-bg-elevated)] flex items-center justify-center text-[var(--axiom-accent)]">
            {meta?.icon}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)]">{nm}</h3>
            <p className="text-[11px] text-[var(--axiom-text-tertiary)] font-mono">{data.org}</p>
          </div>
        </div>
        <span className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ backgroundColor: sc.bg, boxShadow: sc.shadow }} />
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-4">
          <div><span className="text-[var(--axiom-text-tertiary)]">Cycles: </span>
            <span className="text-[var(--axiom-text-secondary)] font-mono font-medium">{data.cycle_count}</span></div>
          <div><span className="text-[var(--axiom-text-tertiary)]">Last: </span>
            <span className="text-[var(--axiom-text-secondary)] font-mono">{fmt(data.last_cycle)}</span></div>
        </div>
        {running && <div className="flex items-center gap-1.5 text-[11px] text-[var(--axiom-success)]">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--axiom-success)] animate-dot-pulse" />Running</div>}
      </div>

      <div className="flex items-center justify-between gap-2 pt-1 border-t border-[var(--axiom-border)]">
        <div className="flex flex-wrap gap-1.5 text-[10px]">
          {schedKeys.slice(0, 2).map((k) => (
            <span key={k} className="px-1.5 py-0.5 rounded bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)] font-mono">{k}</span>
          ))}
          {schedKeys.length > 2 && <span className="px-1.5 py-0.5 rounded text-[var(--axiom-text-tertiary)]">+{schedKeys.length - 2}</span>}
        </div>
        <button onClick={onToggle} disabled={toggling}
          className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-all duration-150 ${
            running
              ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)] hover:bg-[var(--axiom-accent-muted)]"
              : "bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)]"
          } disabled:opacity-50`}>
          {toggling ? "…" : running ? "Stop" : "Start"}
        </button>
      </div>
    </motion.div>
  );
}

/* Stateful screens */

function LoadingState() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <div className="flex items-center justify-center gap-1 mb-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="w-2 h-2 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse"
              style={{ animationDelay: `${i * 200}ms` }} />
          ))}
        </div>
        <p className="text-sm text-[var(--axiom-text-tertiary)]">Loading Executive Board...</p>
      </div>
    </div>
  );
}

function ErrorState({ msg, onRetry }: { msg: string; onRetry: () => void }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-xs">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
          className="mx-auto mb-3 text-[var(--axiom-error)]">
          <circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>
        </svg>
        <p className="text-sm font-medium text-[var(--axiom-error)] mb-1">Connection Error</p>
        <p className="text-xs text-[var(--axiom-text-tertiary)] mb-4">{msg}</p>
        <button onClick={onRetry}
          className="px-4 py-2 rounded-md text-xs font-medium bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors">
          Retry
        </button>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2"
          className="mx-auto mb-3 text-[var(--axiom-text-tertiary)]">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <p className="text-sm text-[var(--axiom-text-tertiary)]">No executives registered</p>
      </div>
    </div>
  );
}

/* Main Export */

export default function ExecutiveBoard() {
  const { executiveBoard, setExecutiveBoard } = useAxiomStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<Record<string, boolean>>({});

  const fetchStatus = useCallback(async () => {
    try {
      setError(null);
      setExecutiveBoard(await executives.boardStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load board status");
    } finally {
      setLoading(false);
    }
  }, [setExecutiveBoard]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15_000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleToggle = useCallback(async (id: string) => {
    setToggling((p) => ({ ...p, [id]: true }));
    try {
      await executives.triggerCycle(id, "manual");
      setTimeout(fetchStatus, 500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Toggle failed");
    } finally {
      setToggling((p) => ({ ...p, [id]: false }));
    }
  }, [fetchStatus]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState msg={error} onRetry={fetchStatus} />;
  if (!executiveBoard || Object.keys(executiveBoard).length === 0) return <EmptyState />;

  const entries = Object.entries(executiveBoard);
  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-[var(--axiom-text-primary)]">Executive Board</h2>
          <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono bg-[var(--axiom-bg-elevated)] px-1.5 py-0.5 rounded">
            {entries.length} agent{entries.length !== 1 ? "s" : ""}
          </span>
        </div>
        <button onClick={fetchStatus}
          className="p-1.5 rounded-md text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors"
          title="Refresh">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
          </svg>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.06 } } }}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 max-w-5xl mx-auto"
        >
          {entries.map(([id, data]) => (
            <ExecCard key={id} id={id} data={data}
              onToggle={() => handleToggle(id)} toggling={!!toggling[id]} />
          ))}
        </motion.div>
      </div>
    </div>
  );
}