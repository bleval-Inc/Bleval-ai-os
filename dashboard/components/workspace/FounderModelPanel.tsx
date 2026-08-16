"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";

// ── FounderModelPanel ──────────────────────────────────────────────────
// In-memory preference model. Never modifies authority or safety rules.

export default function FounderModelPanel() {
  const { founderModel, setFounderModel } = useAxiomStore();
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  // ── Simulate learning a decision ──────────────────────────────────────

  const recordDecision = useCallback(
    (outcome: string) => {
      const pattern = outcome === "approve" ? "Approves quickly" :
        outcome === "reject" ? "Rejects with reasoning" :
        "Requests modifications";

      setFounderModel({
        decisionPatterns: {
          ...founderModel.decisionPatterns,
          [pattern]: (founderModel.decisionPatterns[pattern] || 0) + 1,
        },
      });
    },
    [founderModel.decisionPatterns, setFounderModel],
  );

  // ── Reset ────────────────────────────────────────────────────────────

  const resetModel = useCallback(() => {
    setFounderModel({
      decisionPatterns: {},
      approvedFormats: [],
      workingHours: { start: 5, end: 21 },
      preferredOutputs: [],
      communicationStyle: "professional",
      recurringPriorities: [],
      approvedStandards: [],
    });
    setShowResetConfirm(false);
  }, [setFounderModel]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-2.5">
          <span className="text-sm">👤</span>
          <h2 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Founder Model</h2>
        </div>
        <span className="text-[9px] text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded-full font-mono">
          Local only
        </span>
      </div>

      {/* Security boundary notice */}
      <div className="px-3 py-2 text-[9px] text-blue-400 bg-blue-400/5 border-b border-blue-400/10">
        🔒 Learned preferences never modify authority or safety rules.
        This model operates in a read-only observation layer.
      </div>

      <div className="flex-1 overflow-y-auto scroll-smooth p-3 space-y-3">
        {/* Decision patterns */}
        <div className="glass-panel p-3">
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Decision Patterns</h3>
          {Object.keys(founderModel.decisionPatterns).length === 0 ? (
            <p className="text-[10px] text-[var(--axiom-text-tertiary)]">No decisions tracked yet. Simulate below.</p>
          ) : (
            <div className="space-y-1.5">
              {Object.entries(founderModel.decisionPatterns)
                .sort(([, a], [, b]) => b - a)
                .map(([pattern, count]) => (
                  <div key={pattern} className="flex items-center justify-between px-2 py-1.5 bg-white/5 rounded-md">
                    <span className="text-[10px] text-[var(--axiom-text-primary)]">{pattern}</span>
                    <span className="text-[10px] font-bold text-[var(--axiom-text-primary)]">{count}x</span>
                  </div>
                ))}
            </div>
          )}

          {/* Simulate buttons */}
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => recordDecision("approve")}
              className="px-2 py-1 text-[9px] font-medium text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded-md hover:bg-emerald-400/20 transition-colors"
            >
              + Approve
            </button>
            <button
              onClick={() => recordDecision("reject")}
              className="px-2 py-1 text-[9px] font-medium text-red-400 bg-red-400/10 border border-red-400/20 rounded-md hover:bg-red-400/20 transition-colors"
            >
              + Reject
            </button>
            <button
              onClick={() => recordDecision("modify")}
              className="px-2 py-1 text-[9px] font-medium text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-md hover:bg-amber-400/20 transition-colors"
            >
              + Modify
            </button>
          </div>
        </div>

        {/* Communication style */}
        <div className="glass-panel p-3">
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Communication</h3>
          <div className="flex items-center gap-2">
            {["brief", "professional", "detailed", "casual"].map((style) => (
              <button
                key={style}
                onClick={() => setFounderModel({ communicationStyle: style })}
                className={`px-2.5 py-1 text-[9px] font-medium rounded-md transition-colors ${
                  founderModel.communicationStyle === style
                    ? "text-violet-400 bg-violet-400/10 border border-violet-400/20"
                    : "text-[var(--axiom-text-tertiary)] bg-white/5 border border-transparent hover:bg-white/10"
                }`}
              >
                {style.charAt(0).toUpperCase() + style.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Working hours */}
        <div className="glass-panel p-3">
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Working Hours</h3>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">Start:</span>
              <input
                type="number"
                min={0}
                max={23}
                value={founderModel.workingHours.start}
                onChange={(e) => setFounderModel({ workingHours: { ...founderModel.workingHours, start: parseInt(e.target.value) || 5 } })}
                className="w-12 px-2 py-1 text-[10px] bg-white/5 border border-[var(--axiom-border)] rounded-md text-[var(--axiom-text-primary)] text-center"
              />
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">:00</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">End:</span>
              <input
                type="number"
                min={0}
                max={23}
                value={founderModel.workingHours.end}
                onChange={(e) => setFounderModel({ workingHours: { ...founderModel.workingHours, end: parseInt(e.target.value) || 21 } })}
                className="w-12 px-2 py-1 text-[10px] bg-white/5 border border-[var(--axiom-border)] rounded-md text-[var(--axiom-text-primary)] text-center"
              />
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">:00</span>
            </div>
          </div>
        </div>

        {/* Approved formats */}
        <div className="glass-panel p-3">
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Approved Formats</h3>
          <div className="flex flex-wrap gap-1">
            {founderModel.approvedFormats.length === 0 && (
              <p className="text-[10px] text-[var(--axiom-text-tertiary)]">No formats approved yet</p>
            )}
            {founderModel.approvedFormats.map((fmt) => (
              <span key={fmt} className="px-2 py-0.5 text-[9px] text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded-full">
                {fmt}
              </span>
            ))}
            <button
              onClick={() => {
                const fmt = prompt("Enter approved format name:");
                if (fmt) setFounderModel({ approvedFormats: [...founderModel.approvedFormats, fmt] });
              }}
              className="px-2 py-0.5 text-[9px] text-[var(--axiom-text-tertiary)] bg-white/5 border border-dashed border-[var(--axiom-border)] rounded-full hover:bg-white/10 transition-colors"
            >
              + Add
            </button>
          </div>
        </div>

        {/* Recurring priorities */}
        <div className="glass-panel p-3">
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Recurring Priorities</h3>
          <div className="flex flex-wrap gap-1">
            {founderModel.recurringPriorities.length === 0 && (
              <p className="text-[10px] text-[var(--axiom-text-tertiary)]">No priorities detected</p>
            )}
            {founderModel.recurringPriorities.map((p) => (
              <span key={p} className="px-2 py-0.5 text-[9px] text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-full">
                {p}
              </span>
            ))}
            <button
              onClick={() => {
                const p = prompt("Enter detected priority:");
                if (p) setFounderModel({ recurringPriorities: [...founderModel.recurringPriorities, p] });
              }}
              className="px-2 py-0.5 text-[9px] text-[var(--axiom-text-tertiary)] bg-white/5 border border-dashed border-[var(--axiom-border)] rounded-full hover:bg-white/10 transition-colors"
            >
              + Add
            </button>
          </div>
        </div>

        {/* Approved standards */}
        <div className="glass-panel p-3">
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2 uppercase tracking-wider">Approved Standards</h3>
          <div className="flex flex-wrap gap-1">
            {founderModel.approvedStandards.length === 0 && (
              <p className="text-[10px] text-[var(--axiom-text-tertiary)]">No standards approved yet</p>
            )}
            {founderModel.approvedStandards.map((s) => (
              <span key={s} className="px-2 py-0.5 text-[9px] text-blue-400 bg-blue-400/10 border border-blue-400/20 rounded-full">
                {s}
              </span>
            ))}
            <button
              onClick={() => {
                const s = prompt("Enter approved standard:");
                if (s) setFounderModel({ approvedStandards: [...founderModel.approvedStandards, s] });
              }}
              className="px-2 py-0.5 text-[9px] text-[var(--axiom-text-tertiary)] bg-white/5 border border-dashed border-[var(--axiom-border)] rounded-full hover:bg-white/10 transition-colors"
            >
              + Add
            </button>
          </div>
        </div>

        {/* Reset */}
        <div className="flex items-center justify-center py-2">
          {showResetConfirm ? (
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-red-400">Reset all learned preferences?</span>
              <button
                onClick={resetModel}
                className="px-2.5 py-1 text-[9px] font-medium text-white bg-red-400 rounded-md hover:bg-red-500 transition-colors"
              >
                Confirm Reset
              </button>
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-2.5 py-1 text-[9px] font-medium text-[var(--axiom-text-tertiary)] bg-white/5 rounded-md hover:bg-white/10 transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowResetConfirm(true)}
              className="text-[9px] text-[var(--axiom-text-tertiary)] hover:text-red-400 transition-colors"
            >
              Reset learned preferences
            </button>
          )}
        </div>
      </div>
    </div>
  );
}