"use client";

import { motion } from "framer-motion";
import { Panel, SectionTitle, WorkspaceHeader, KpiGrid, StatusChip } from "./bleval-ui";
import { BLEVAL_ACCENT, BLEVAL_VIOLET, type StatusTone } from "./types";
import { truthKpis, marketIntelligence, researchProjects, intelligenceFindings, strategicOutputs } from "./truth-data";

const toneForStatus: Record<string, StatusTone> = {
  active: "active",
  paused: "neutral",
  complete: "healthy",
};
const toneForPriority: Record<string, StatusTone> = {
  high: "danger",
  medium: "warning",
  low: "neutral",
};

function IntelligenceBlock({ block }: { block: (typeof marketIntelligence)[number] }) {
  return (
    <div className="rounded-xl border p-4 min-w-0" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-semibold tracking-wide text-[var(--axiom-text-primary)]">{block.title}</span>
        <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{block.meta}</span>
      </div>
      <div className="h-[4px] rounded-full mb-3" style={{ background: "rgba(109,124,255,0.1)" }}>
        <motion.div
          className="h-full rounded-full"
          style={{ width: `${block.value}%`, background: `linear-gradient(90deg, ${BLEVAL_ACCENT}, ${BLEVAL_VIOLET})` }}
          initial={{ width: 0 }}
          animate={{ width: `${block.value}%` }}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
        />
      </div>
      <ul className="space-y-1.5">
        {block.points.map((p) => (
          <li key={p} className="flex gap-2 text-[11px] leading-snug text-[var(--axiom-text-secondary)]">
            <span className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0" style={{ background: BLEVAL_ACCENT }} />
            {p}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function TruthEngine() {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-28 min-w-0">
      <WorkspaceHeader
        icon="truth"
        title="TRUTH ENGINE"
        subtitle="Market intelligence, research and strategic truth"
        right={<StatusChip label="RESEARCH ACTIVE" tone="active" />}
      />

      <KpiGrid kpis={truthKpis} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Market Intelligence" hint={`Updated ${researchProjects[0].lastUpdated}`} />
          <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            {marketIntelligence.map((b) => (
              <IntelligenceBlock key={b.id} block={b} />
            ))}
          </div>
        </Panel>

        <Panel className="min-w-0">
          <SectionTitle title="Strategic Outputs" hint="Where intelligence is used" />
          <div className="px-4 pb-5 flex flex-col gap-3">
            {strategicOutputs.map((s, i) => (
              <div key={s.id}>
                <div className="flex items-center justify-between mb-1 text-[11px]">
                  <span className="text-[var(--axiom-text-secondary)]">{s.channel}</span>
                  <span className="text-[var(--axiom-text-primary)] font-semibold tabular-nums">{s.usage}</span>
                </div>
                <div className="h-[6px] rounded-full" style={{ background: "rgba(109,124,255,0.1)" }}>
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: i % 2 ? `linear-gradient(90deg,${BLEVAL_VIOLET},${BLEVAL_ACCENT})` : `linear-gradient(90deg,${BLEVAL_ACCENT},${BLEVAL_VIOLET})` }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(s.usage / Math.max(...strategicOutputs.map((x) => x.usage))) * 100}%` }}
                    transition={{ duration: 0.8, delay: 0.2 + i * 0.06, ease: "easeOut" }}
                  />
                </div>
              </div>
            ))}
            <p className="text-[10px] text-[var(--axiom-text-tertiary)]/70 mt-1">Feeds Content, Offers, Proposals, Acquisition, Sales and Client strategy.</p>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="min-w-0">
          <SectionTitle title="Research Projects" hint={`${researchProjects.length} tracked`} />
          <div className="px-3 pb-4 flex flex-col gap-1.5 max-h-[420px] overflow-y-auto hide-scrollbar">
            {researchProjects.map((p, i) => (
              <motion.div key={p.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.05 }} className="rounded-xl px-3 py-3 border" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-[12px] font-medium text-[var(--axiom-text-primary)] truncate">{p.topic}</p>
                    <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{p.market}</p>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <StatusChip label={p.status.toUpperCase()} tone={toneForStatus[p.status]} />
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-3 text-[10px] text-[var(--axiom-text-tertiary)]">
                  <span>Updated {p.lastUpdated}</span>
                  <span>{p.findings} findings</span>
                  <span className="ml-auto"><StatusChip label={p.priority} tone={toneForPriority[p.priority]} /></span>
                </div>
              </motion.div>
            ))}
          </div>
        </Panel>

        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Intelligence Findings" hint={`${intelligenceFindings.length} generated`} />
          <div className="px-4 pb-4 flex flex-col gap-3">
            {intelligenceFindings.map((f, i) => (
              <motion.div key={f.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 + i * 0.08 }} className="rounded-xl border p-4" style={{ borderColor: "rgba(109,124,255,0.12)", background: "linear-gradient(145deg, rgba(109,124,255,0.04), rgba(168,140,255,0.03))" }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: BLEVAL_ACCENT }} />
                  <p className="text-[13px] font-medium text-[var(--axiom-text-primary)]">{f.finding}</p>
                </div>
                <p className="text-[11px] text-[var(--axiom-text-secondary)] mb-3">{f.evidence}</p>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[10px] text-[var(--axiom-text-tertiary)]">
                  <span>{f.sources} sources</span>
                  <span className="inline-flex items-center gap-1.5"><span className="text-emerald-400/90 font-semibold">{f.confidence}%</span> confidence</span>
                  <span className="inline-flex items-center gap-1.5 font-medium text-[var(--axiom-accent-hover)]">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6" /></svg>
                    {f.implication}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}