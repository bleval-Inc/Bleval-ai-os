"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { MonoLabel } from "./boardroom-ui";

// ── Collaboration canvas (SHARE) ──────────────────────────────────────
// An interactive collaboration area — NOT screen sharing. Prepared for
// future modes (BOARD / MIND MAP / DOCUMENT / PLAN / DATA / PRESENTATION)
// via a clean mode registry. Each mode is an isolated component so new
// modes slot in without touching the shell. Content shown is illustrative
// AXIOM-generated workspace, clearly labelled — no fabricated live data.

type ShareMode = "board" | "mindmap" | "document" | "plan" | "data" | "presentation";

interface ModeDef {
  id: ShareMode;
  label: string;
  available: boolean;
}

const MODES: ModeDef[] = [
  { id: "document", label: "Document", available: true },
  { id: "data", label: "Data", available: true },
  { id: "board", label: "Board", available: false },
  { id: "mindmap", label: "Mind Map", available: false },
  { id: "plan", label: "Plan", available: false },
  { id: "presentation", label: "Presentation", available: false },
];

interface ShareItem {
  id: string;
  mode: ShareMode;
  title: string;
  kind: string;
}

const LIBRARY: ShareItem[] = [
  { id: "acq", mode: "document", title: "Acquisition campaign — draft approach", kind: "Strategy document" },
  { id: "ops", mode: "data", title: "Operations KPI snapshot", kind: "Charts / data" },
  { id: "risk", mode: "document", title: "Capital deployment — risk framework", kind: "Recommendation" },
];

const MODE_META: Record<ShareMode, { title: string; blurb: string }> = {
  board: { title: "Board", blurb: "Arrange strategic content on an open canvas." },
  mindmap: { title: "Mind Map", blurb: "Map ideas and relationships visually." },
  document: { title: "Document", blurb: "Review a shared document with the room." },
  plan: { title: "Plan", blurb: "Lay out a plan and its workflow." },
  data: { title: "Data", blurb: "Inspect charts and data together." },
  presentation: { title: "Presentation", blurb: "Present slides to the room." },
};

export default function BoardroomShare({ onClose }: { onClose: () => void }) {
  const [mode, setMode] = useState<ShareMode>("document");
  const [openDoc, setOpenDoc] = useState<string | null>("acq");

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="absolute inset-0 z-30 flex flex-col glass-panel-strong rounded-2xl overflow-hidden"
      style={{ border: "1px solid rgba(240,241,243,0.08)" }}
    >
      {/* Canvas header */}
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)] flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <MonoLabel>SHARE</MonoLabel>
          <span className="text-[10px] text-[var(--axiom-text-tertiary)] truncate">{MODE_META[mode].blurb}</span>
        </div>
        <button onClick={onClose} className="w-6 h-6 rounded-md flex items-center justify-center text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)] hover:bg-white/5 text-[13px]">
          ✕
        </button>
      </header>

      <div className="flex-1 flex min-h-0">
        {/* Mode rail */}
        <div className="w-36 border-r border-[var(--axiom-border)] flex-shrink-0 flex flex-col p-2 gap-1">
          <MonoLabel>{"ROOM // " + mode.toUpperCase()}</MonoLabel>
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => m.available && setMode(m.id)}
              disabled={!m.available}
              className={cn(
                "text-left px-3 py-2 rounded-lg text-[11px] transition-colors",
                mode === m.id ? "bg-[#6d7cff]/10 text-[var(--axiom-accent)]" : "text-[var(--axiom-text-secondary)] hover:bg-white/5",
                !m.available && "opacity-40 cursor-not-allowed",
              )}
            >
              <span className="flex items-center justify-between gap-2">
                {m.label}
                {!m.available && <span className="text-[8px] text-[var(--axiom-text-tertiary)]">SOON</span>}
              </span>
            </button>
          ))}

          {/* Library */}
          <div className="mt-3 border-t border-[var(--axiom-border)] pt-2">
            <MonoLabel>LIBRARY</MonoLabel>
            <div className="mt-1.5 space-y-1">
              {LIBRARY.map((item) => (
                <button
                  key={item.id}
                  onClick={() => { setMode(item.mode); setOpenDoc(item.id); }}
                  className={cn("block w-full text-left px-3 py-2 rounded-lg text-[10px] transition-colors border", openDoc === item.id ? "border-[#6d7cff]/25 bg-[#6d7cff]/[0.05] text-[var(--axiom-text-primary)]" : "border-transparent text-[var(--axiom-text-secondary)] hover:bg-white/5")}
                >
                  <span className="block truncate">{item.title}</span>
                  <span className="text-[8px] text-[var(--axiom-text-tertiary)]">{item.kind}</span>
                </button>
              ))}
              <p className="px-3 pt-1 text-[8px] text-[var(--axiom-text-tertiary)]/70">AXIOM-generated workspace preview</p>
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 min-w-0 overflow-y-auto hide-scrollbar p-5">
          {mode === "document" && <DocumentView />}
          {mode === "data" && <DataView />}
          {(mode === "board" || mode === "mindmap" || mode === "plan" || mode === "presentation") && (
            <ComingSoon title={MODE_META[mode].title} />
          )}
        </div>
      </div>
    </motion.div>
  );
}

function DocumentView() {
  return (
    <div className="max-w-2xl mx-auto">
      <MonoLabel>{"// DOCUMENT"}</MonoLabel>
      <h2 className="mt-2 text-xl font-light text-[var(--axiom-text-primary)]">Acquisition campaign — draft approach</h2>
      <p className="mt-1 text-[10px] text-[var(--axiom-text-tertiary)]">Prepared by Jenson · COO · BLEVAL INC</p>
      <article className="mt-5 space-y-3 text-[12.5px] leading-relaxed text-[var(--axiom-text-secondary)] [&>h3]:text-[var(--axiom-text-primary)] [&>h3]:font-medium">
        <h3>Objective</h3>
        <p>Establish a controlled acquisition pipeline for the next cycle, prioritising fit over volume while we consolidate the current client base.</p>
        <h3>Proposed approach</h3>
        <p>Develop a shortlist of target profiles, size each opportunity against existing operations capacity, and stage outreach across the month to avoid over-committing.</p>
        <h3>Decision required</h3>
        <p>This is a recommendation — execution should not start until the Founder approves the approach and the Owner is nominated.</p>
      </article>
    </div>
  );
}

function DataView() {
  const bars = [
    { label: "Content", v: 82 },
    { label: "Clients", v: 64 },
    { label: "Ops", v: 71 },
    { label: "Q1 target", v: 90 },
  ];
  return (
    <div className="max-w-2xl mx-auto">
      <MonoLabel>{"// DATA"}</MonoLabel>
      <h2 className="mt-2 text-xl font-light text-[var(--axiom-text-primary)]">Operations KPI snapshot</h2>
      <p className="mt-1 text-[10px] text-[var(--axiom-text-tertiary)]">Illustrative grouped metrics · vertical bars</p>
      <div className="mt-6 grid grid-cols-4 gap-3 items-end h-44">
        {bars.map((b) => (
          <div key={b.label} className="flex flex-col items-center gap-2 justify-end h-full">
            <span className="font-mono text-[10px] text-[var(--axiom-text-secondary)]">{b.v}%</span>
            <div className="w-full rounded-t-lg" style={{ height: `${b.v}%`, background: "linear-gradient(180deg, var(--axiom-accent), var(--axiom-violet))" }} />
            <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{b.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ComingSoon({ title }: { title: string }) {
  return (
    <div className="h-full min-h-[200px] flex flex-col items-center justify-center gap-2 text-center">
      <div className="w-8 h-8 rounded-lg border border-[var(--axiom-border-hover)] flex items-center justify-center text-[var(--axiom-text-tertiary)]">＋</div>
      <p className="text-[12px] text-[var(--axiom-text-primary)]">{title} canvas</p>
      <p className="text-[10px] text-[var(--axiom-text-tertiary)]">Mode scaffold is in place — rendering arrives with the mode modules.</p>
    </div>
  );
}