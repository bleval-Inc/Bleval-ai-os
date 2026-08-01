"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { SkeletonRow } from "../Skeletons";
import { EmptyState } from "../States";

interface ApprovalItem {
  id: string;
  approval_id: string;
  workflow_id: string;
  step_name: string;
  requested_by: string;
  requested_at: string;
}

interface CommandCenterApprovalsProps {
  approvals: ApprovalItem[];
  loading: boolean;
  error: string | null;
  onNavigate: () => void;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
}

function timeAgo(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function CommandCenterApprovals({
  approvals,
  loading,
  error,
  onNavigate,
  onApprove,
  onReject,
}: CommandCenterApprovalsProps) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  if (loading && !approvals.length) {
    return (
      <div className="glass-card p-4">
        <div className="h-4 w-1/2 rounded bg-[var(--axiom-bg-elevated)] mb-3" />
        <SkeletonRow /><SkeletonRow /><SkeletonRow />
      </div>
    );
  }

  if (error && !approvals.length) {
    return (
      <div className="glass-card p-4">
        <p className="text-xs text-[var(--axiom-error)]">{error}</p>
      </div>
    );
  }

  const display = approvals.slice(0, 3);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: 0.05 }}
      className="glass-card p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Pending Approvals</h3>
        <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-medium">
          {approvals.length}
        </span>
      </div>

      {display.length === 0 ? (
        <EmptyState
          title="No pending approvals"
          description="All approvals have been resolved."
          className="py-6"
        />
      ) : (
        <div className="space-y-2">
          {display.map((a) => (
            <div key={a.id} className="px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)]">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-[var(--axiom-text-primary)] truncate font-medium">{a.step_name}</p>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)]">
                    {a.workflow_id} · {a.requested_by} · {timeAgo(a.requested_at)}
                  </p>
                </div>
                <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                  <button
                    disabled={actionLoading === a.id}
                    onClick={async () => { setActionLoading(a.approval_id); try { await onApprove(a.approval_id); } finally { setActionLoading(null); } }}
                    className="px-2.5 py-1 text-[9px] font-medium rounded bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 disabled:opacity-40 transition-colors"
                  >
                    {actionLoading === a.approval_id ? "..." : "Approve"}
                  </button>
                  <button
                    disabled={actionLoading === a.id}
                    onClick={async () => { setActionLoading(a.approval_id); try { await onReject(a.approval_id); } finally { setActionLoading(null); } }}
                    className="px-2.5 py-1 text-[9px] font-medium rounded border border-[var(--axiom-border)] text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-error)] hover:border-red-400/30 disabled:opacity-40 transition-colors"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
          {approvals.length > 3 && (
            <button onClick={onNavigate} className="w-full text-[10px] text-[var(--axiom-text-tertiary)] py-1 hover:text-[var(--axiom-text-secondary)]">
              +{approvals.length - 3} more
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}