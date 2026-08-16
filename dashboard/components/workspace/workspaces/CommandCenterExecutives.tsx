"use client";

import { motion } from "framer-motion";
import { SkeletonRow } from "../Skeletons";
import { EmptyState } from "../States";
import type { ExecutiveBoardStatus } from "../../../lib/api-types";

interface CommandCenterExecutivesProps {
  board: ExecutiveBoardStatus | null;
  loading: boolean;
  error: string | null;
  onNavigate: () => void;
}

export default function CommandCenterExecutives({ board, loading, error, onNavigate }: CommandCenterExecutivesProps) {
  if (loading && !board) {
    return (
      <div className="glass-card p-4">
        <div className="h-4 w-1/2 rounded bg-[var(--axiom-bg-elevated)] mb-3" />
        <SkeletonRow /><SkeletonRow /><SkeletonRow />
      </div>
    );
  }

  if (error && !board) {
    return (
      <div className="glass-card p-4">
        <p className="text-xs text-[var(--axiom-error)]">{error}</p>
      </div>
    );
  }

  const entries = board ? Object.entries(board) : [];
  const displayEntries = entries.slice(0, 3);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="glass-card p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Executive Status</h3>
        <button onClick={onNavigate} className="text-[9px] text-[var(--axiom-accent)] hover:underline">View All</button>
      </div>

      {entries.length === 0 ? (
        <EmptyState title="No executives registered" className="py-6" />
      ) : (
        <div className="space-y-2">
          {displayEntries.map(([id, exec]) => {
            const dotColor = exec.status === "running" ? "bg-emerald-400" : exec.status === "error" ? "bg-red-400" : "bg-amber-400";
            const lastCycle = exec.last_cycle
              ? Math.floor((Date.now() - new Date(exec.last_cycle).getTime()) / 3600000)
              : null;
            return (
              <motion.button
                key={id}
                whileHover={{ x: 2 }}
                onClick={onNavigate}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[var(--axiom-bg-elevated)] transition-colors"
              >
                <span className={`w-2 h-2 rounded-full ${dotColor} ${exec.status === "running" ? "animate-pulse" : ""}`} />
                <span className="flex-1 text-xs text-[var(--axiom-text-primary)] font-medium capitalize">{id.replace(/_/g, " ")}</span>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">{exec.cycle_count} cycles</span>
                {lastCycle !== null && <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{lastCycle}h ago</span>}
              </motion.button>
            );
          })}
          {entries.length > 3 && (
            <button onClick={onNavigate} className="w-full text-[10px] text-[var(--axiom-text-tertiary)] py-1 hover:text-[var(--axiom-text-secondary)] transition-colors">
              +{entries.length - 3} more
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}