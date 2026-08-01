"use client";

import { motion } from "framer-motion";
import { EmptyState } from "../States";
import type { HealthSummary } from "../../../lib/api-types";

interface CommandCenterActionsProps {
  approvalCount: number;
  recommendations: { id: string; title: string }[];
  health: HealthSummary | null;
  knowledgeCount: number;
  loading: boolean;
  onNavigate: (view: string) => void;
}

interface ActionItem {
  id: string;
  label: string;
  description: string;
  priority: "high" | "normal" | "info";
  targetView: string;
}

export default function CommandCenterActions({
  approvalCount,
  recommendations,
  health,
  knowledgeCount,
  loading,
  onNavigate,
}: CommandCenterActionsProps) {
  const actions: ActionItem[] = [];

  if (approvalCount > 0) {
    actions.push({
      id: "approvals",
      label: `Review ${approvalCount} pending approval${approvalCount !== 1 ? "s" : ""}`,
      description: "Decisions needed from you",
      priority: "high",
      targetView: "console",
    });
  }

  if (health && health.unhealthy > 0) {
    actions.push({
      id: "health",
      label: `${health.unhealthy} unhealthy component${health.unhealthy !== 1 ? "s" : ""} need${health.unhealthy === 1 ? "s" : ""} attention`,
      description: `${health.degraded} degraded · Check operations`,
      priority: "high",
      targetView: "operations",
    });
  }

  if (recommendations.length > 0) {
    actions.push({
      id: "recommendation",
      label: `Review recommendation: ${recommendations[0].title}`,
      description: "AXIOM learning engine insight",
      priority: "normal",
      targetView: "knowledge",
    });
  }

  if (knowledgeCount > 0) {
    actions.push({
      id: "knowledge",
      label: `View ${knowledgeCount} knowledge entr${knowledgeCount !== 1 ? "ies" : "y"}`,
      description: "Recent learnings from AXIOM",
      priority: "info",
      targetView: "knowledge",
    });
  }

  if (loading && actions.length === 0) {
    return (
      <div className="glass-card p-4">
        <div className="h-4 w-1/2 rounded bg-[var(--axiom-bg-elevated)] mb-3" />
        <div className="space-y-2">{[1, 2].map((i) => <div key={i} className="h-10 rounded-lg bg-[var(--axiom-bg-elevated)] animate-pulse" />)}</div>
      </div>
    );
  }

  const highlight = (p: string) =>
    p === "high" ? "border-l-[3px] border-l-[var(--axiom-error)] bg-[var(--axiom-error)]/5" :
    p === "normal" ? "border-l-[3px] border-l-[var(--axiom-warning)]" :
    "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: 0.15 }}
      className="glass-card p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Suggested Actions</h3>
        {actions.length > 0 && <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{actions.length} item{actions.length !== 1 ? "s" : ""}</span>}
      </div>

      {actions.length === 0 ? (
        <EmptyState
          title="All clear"
          description="No urgent actions needed."
          className="py-6"
        />
      ) : (
        <div className="space-y-1.5">
          {actions.map((a) => (
            <motion.button
              key={a.id}
              whileHover={{ x: 2 }}
              onClick={() => onNavigate(a.targetView)}
              className={`w-full text-left px-3 py-2.5 rounded-lg hover:bg-[var(--axiom-bg-elevated)] transition-colors ${highlight(a.priority)}`}
            >
              <p className="text-xs font-medium text-[var(--axiom-text-primary)]">{a.label}</p>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">{a.description}</p>
            </motion.button>
          ))}
        </div>
      )}
    </motion.div>
  );
}