"use client";

import { motion } from "framer-motion";
import { SkeletonStat } from "../Skeletons";
import type { HealthSummary } from "../../../lib/api-types";

interface CommandCenterHealthProps {
  health: HealthSummary | null;
  loading: boolean;
  error: string | null;
  onNavigate: () => void;
}

function Metric({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="rounded-lg border border-[var(--axiom-border)] p-3 text-center">
      <p className="text-lg font-semibold tabular-nums" style={{ color }}>{value}</p>
      <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{label}</p>
    </div>
  );
}

export default function CommandCenterHealth({ health, loading, error, onNavigate }: CommandCenterHealthProps) {
  if (loading && !health) {
    return (
      <div className="glass-card p-4">
        <div className="h-4 w-1/2 rounded bg-[var(--axiom-bg-elevated)] mb-3" />
        <div className="grid grid-cols-2 gap-2">
          <SkeletonStat /><SkeletonStat /><SkeletonStat /><SkeletonStat />
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="glass-card p-4">
        <p className="text-xs text-[var(--axiom-error)]">{error}</p>
      </div>
    );
  }

  const isHealthy = health?.overall === "healthy";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: 0.05 }}
      className={`glass-card p-4 ${!isHealthy ? "border-red-400/30" : ""}`}
    >
      <button onClick={onNavigate} className="w-full text-left">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Runtime Health</h3>
          <span className={`text-[9px] font-medium ${isHealthy ? "text-emerald-400" : "text-red-400 animate-pulse"}`}>
            {isHealthy ? "All Systems Normal" : `${health?.unhealthy ?? 0} Issue${(health?.unhealthy ?? 0) !== 1 ? "s" : ""}`}
          </span>
        </div>
      </button>

      {health && (
        <div className="grid grid-cols-2 gap-2">
          <Metric label="Total" value={health.total} color="var(--axiom-text-primary)" />
          <Metric label="Healthy" value={health.healthy} color="var(--axiom-success)" />
          <Metric label="Degraded" value={health.degraded} color="var(--axiom-warning)" />
          <Metric label="Unhealthy" value={health.unhealthy} color={health.unhealthy > 0 ? "var(--axiom-error)" : "var(--axiom-text-tertiary)"} />
        </div>
      )}
    </motion.div>
  );
}