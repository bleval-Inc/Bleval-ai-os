"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { rndCategories, rndProjects } from "./personal-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip } from "./personal-ui";
import { PERSONAL_TEAL, PERSONAL_VIOLET, PERSONAL_GOLD, PERSONAL_CYAN } from "./types";

const MEDIA_CARD: { kind: string; title: string }[] = [
  { kind: "VIDEO", title: "Video evidence" },
  { kind: "DIAGRAM", title: "Concept diagram" },
  { kind: "CHART", title: "Evidence chart" },
  { kind: "DOCUMENT", title: "Source document" },
];

// Deep Work — the seeded example project.
const DEEPWORK = {
  summary: "Deep work is the ability to focus without distraction on a cognitively demanding task. In an attention economy, this scarcity is a competitive advantage — and it is trainable through deliberate protocols.",
  findings: [
    "Deep work is a rare skill in an attention-scattered economy.",
    "It compounds: quality and quantity of output rise together.",
    "Phone and notification escape is a precondition, not a courtesy.",
    "Shorter, high-intensity blocks beat longer unfocused ones.",
  ],
  concepts: ["Deliberate practice", "Attention residue", "Capacity training", "Downtime as recovery", "Shallow-work budgeting"],
  methods: [
    "Time-block the deep session; make the start ritual concrete.",
    "Close the OODA loop after each block — observe, orient, decide, act.",
    "Batch shallow work; guard the deep window from interruption.",
    "Log every session to expose the true attention pattern.",
  ],
  evidence: [
    "Newport — Deep Work (2016): focus scarcity thesis.",
    "Orty (OODA): decision-cycle speed as the edge.",
    "Erickson — deliberate practice: effortful, feedback-rich repetition.",
  ],
};

function MediaPlaceholder({ title, variant }: { title: string; variant: "video" | "diagram" | "chart" | "doc" }) {
  const accent = variant === "video" ? PERSONAL_GOLD : variant === "diagram" ? PERSONAL_VIOLET : variant === "chart" ? PERSONAL_TEAL : PERSONAL_CYAN;
  return (
    <div className="rounded-xl border p-4 flex flex-col items-center justify-center gap-2 h-[120px] text-center" style={{ borderColor: `${accent}30`, background: `radial-gradient(ellipse at top, ${accent}0f, transparent 60%), rgba(10,12,16,0.4)` }}>
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke={accent} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        {variant === "video" && <><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M10 9l5 3-5 3z" /></>}
        {variant === "diagram" && <><circle cx="5" cy="12" r="2.5" /><circle cx="19" cy="6" r="2.5" /><circle cx="19" cy="18" r="2.5" /><path d="M7.5 12h8M15 7l-7 4M15 17l-7-5" /></>}
        {variant === "chart" && <><path d="M3 3v18h18" /><path d="M7 15l3.5-3 2.5 2 5-6" /></>}
        {variant === "doc" && <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="M8 13h8M8 17h5" /></>}
      </svg>
      <div>
        <div className="text-[10px] font-bold tracking-[0.14em] uppercase" style={{ color: accent }}>{title}</div>
        <div className="text-[9px] text-[var(--axiom-text-tertiary)]">Placeholder — media ingested here later</div>
      </div>
    </div>
  );
}

export default function Rnd() {
  const [activeId, setActiveId] = useState("rnd1");
  const active = rndProjects.find((p) => p.id === activeId) ?? rndProjects[0];
  const media = MEDIA_CARD;
  const isDeepWork = active.id === "rnd1";

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="R&D — Personal Research"
        subtitle="Media-first truth & research engine"
        right={<StatusChip label="Demo data" tone="neutral" />}
      />

      {/* Research categories */}
      <div className="flex flex-wrap gap-1.5">
        {rndCategories.map((c) => (
          <span key={c} className="rounded-full px-2.5 py-1 text-[9px] font-medium text-[var(--axiom-text-secondary)] border" style={{ borderColor: "rgba(240,241,243,0.08)" }}>{c}</span>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(240px,26%)_1fr] gap-5 items-start">
        {/* Projects */}
        <Panel className="min-w-0">
          <SectionTitle title="Research projects" hint={`${rndProjects.length}`} />
          <div className="px-3 pb-3 space-y-1">
            {rndProjects.map((p) => {
              const activeP = p.id === activeId;
              return (
                <button key={p.id} onClick={() => setActiveId(p.id)} className={cn("w-full text-left rounded-lg px-2.5 py-2.5 transition-colors", activeP && "bg-[var(--axiom-accent-subtle)]")}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className={cn("text-[12px] font-semibold", activeP ? "text-[var(--axiom-text-primary)]" : "text-[var(--axiom-text-secondary)]")}>{p.title}</span>
                    <span className={cn("text-[8px] font-semibold uppercase tracking-wider", p.status === "active" ? "text-emerald-400" : "text-[var(--axiom-text-tertiary)]")}>{p.status}</span>
                  </div>
                  <div className="text-[9px] text-[var(--axiom-text-tertiary)]">{p.category}</div>
                </button>
              );
            })}
          </div>
        </Panel>

        {/* Active project */}
        <Panel className="min-w-0">
          <AnimatePresence mode="wait">
            <motion.div key={active.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18 }} className="px-5 py-4">
              {/* Head */}
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)]">{active.category}</span>
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)]">Updated {active.updated}</span>
                  </div>
                  <h2 className="text-lg font-semibold text-[var(--axiom-text-primary)] tracking-tight">R&D Project — {active.title}</h2>
                  <p className="text-[11px] text-[var(--axiom-text-secondary)] mt-0.5">{active.question}</p>
                </div>
              </div>

              {/* Executive summary */}
              <div className="mb-4">
                <div className="text-[9px] font-semibold uppercase tracking-[0.16em] text-[var(--axiom-violet)] mb-1.5" style={{ color: PERSONAL_VIOLET }}>Executive summary</div>
                <p className="text-[12px] leading-relaxed text-[var(--axiom-text-secondary)]">
                  {isDeepWork ? DEEPWORK.summary : active.summary}
                </p>
              </div>

              {/* Key findings */}
              <div className="mb-4">
                <div className="text-[9px] font-semibold uppercase tracking-[0.16em] text-[var(--axiom-text-tertiary)] mb-2">Key findings</div>
                <div className="flex flex-col gap-1.5">
                  {DEEPWORK.findings.map((f) => (
                    <div key={f} className="flex items-start gap-2">
                      <span className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: PERSONAL_TEAL }} />
                      <span className="text-[11px] text-[var(--axiom-text-secondary)] leading-snug">{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Media row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mb-4">
                {media.map((m) => (
                  <MediaPlaceholder key={m.kind} title={m.kind} variant={m.kind.toLowerCase() as "video" | "diagram" | "chart" | "doc"} />
                ))}
              </div>

              {/* Concepts + methods + evidence */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div className="rounded-xl border p-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(10,12,16,0.4)" }}>
                  <div className="text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-2">Key concepts</div>
                  <div className="flex flex-wrap gap-1">
                    {DEEPWORK.concepts.map((c) => (
                      <span key={c} className="rounded-full px-2 py-0.5 text-[9px] text-[var(--axiom-text-secondary)] border border-[rgba(240,241,243,0.08)]">{c}</span>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border p-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(10,12,16,0.4)" }}>
                  <div className="text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-2">Methods</div>
                  <ul className="space-y-1.5">
                    {DEEPWORK.methods.map((m) => <li key={m} className="flex items-start gap-1.5 text-[10px] text-[var(--axiom-text-secondary)] leading-snug"><span className="text-[var(--axiom-text-tertiary)]">·</span>{m}</li>)}
                  </ul>
                </div>
                <div className="rounded-xl border p-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(10,12,16,0.4)" }}>
                  <div className="text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-2">Evidence · Sources</div>
                  <ul className="space-y-1.5">
                    {DEEPWORK.evidence.map((e) => <li key={e} className="text-[10px] text-[var(--axiom-text-secondary)] leading-snug">· {e}</li>)}
                  </ul>
                </div>
              </div>

              {/* Recommendation */}
              <div className="rounded-xl border p-3.5 flex items-start gap-3" style={{ borderColor: "rgba(45,212,191,0.18)", background: "rgba(45,212,191,0.05)" }}>
                <span className="mt-0.5 w-8 h-8 rounded-lg flex items-center justify-center text-white flex-shrink-0" style={{ background: "linear-gradient(135deg,#2dd4bf,#4da3ff)" }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l2.5 5.1L20 9l-4 3.9.9 5.6L12 15.9l-4.9 2.6.9-5.6L4 9l5.5-.9z" /></svg>
                </span>
                <div>
                  <div className="text-[10px] font-semibold tracking-[0.16em] uppercase mb-1" style={{ color: PERSONAL_TEAL }}>Yamako recommendation</div>
                  <p className="text-[12px] leading-relaxed text-[var(--axiom-text-secondary)]">
                    Adopt a 90-minute daily deep-work block with a written OODA reflection. Log each session in the Learning workstation for 30 days, then review the Progress trends to decide whether to extend the block or tighten the shutdown ritual.
                  </p>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </Panel>
      </div>
    </div>
  );
}