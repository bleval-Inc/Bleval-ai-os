"use client";

import { motion } from "framer-motion";
import { Panel, SectionTitle, WorkspaceHeader, KpiGrid, StatusChip, StageFlow } from "./bleval-ui";
import { BLEVAL_ACCENT } from "./types";
import { contentKpis, contentPipeline, contentCalendar, contentLibrary, qcStatuses } from "./content-data";

const kindHue: Record<string, string> = {
  Reel: "linear-gradient(135deg,#6d7cff,#a88cff)",
  Carousel: "linear-gradient(135deg,#00d4ff,#6d7cff)",
  Post: "linear-gradient(135deg,#a88cff,#00d4ff)",
  Image: "linear-gradient(135deg,#5a67e0,#6d7cff)",
  Campaign: "linear-gradient(135deg,#6d7cff,#00d4ff)",
};

export default function ContentStudio() {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-28 min-w-0">
      <WorkspaceHeader
        icon="content"
        title="CONTENT"
        subtitle="Content production, quality control and distribution"
        right={<StatusChip label="8 IN QC" tone="warning" />}
      />

      <KpiGrid kpis={contentKpis} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="min-w-0">
          <SectionTitle title="Content Pipeline" hint="Idea → Published" />
          <div className="px-4 pb-5">
            <StageFlow stages={contentPipeline} currentIndex={4} />
          </div>
        </Panel>

        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="QC Status" hint="Review gate" />
          <div className="px-4 pb-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {qcStatuses.map((q, i) => (
                <motion.div
                  key={q.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 + i * 0.05 }}
                  className="rounded-xl border p-3 flex flex-col gap-1.5"
                  style={{
                    borderColor:
                      q.tone === "active" ? "rgba(109,124,255,0.28)" : q.tone === "danger" ? "rgba(255,77,106,0.2)" : q.tone === "warning" ? "rgba(255,184,48,0.2)" : "rgba(240,241,243,0.06)",
                    background: q.tone === "active" ? "rgba(109,124,255,0.06)" : "rgba(15,18,24,0.4)",
                  }}
                >
                  <div className="flex items-center justify-between">
                    <StatusChip label={q.label} tone={q.tone} />
                    <span className="text-lg font-semibold tabular-nums text-[var(--axiom-text-primary)]">{q.count}</span>
                  </div>
                </motion.div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-xl px-3.5 py-2.5 border" style={{ borderColor: BLEVAL_ACCENT + "26", background: "rgba(109,124,255,0.05)" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={BLEVAL_ACCENT} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
              <span className="text-[11px] text-[var(--axiom-text-secondary)]">Nothing publishes automatically — every item requires <span className="text-[var(--axiom-text-primary)] font-medium">Founder approval</span> before scheduling.</span>
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Content Calendar" hint="Next 7 days" />
          <div className="px-4 pb-4 flex flex-col">
            <div className="grid grid-cols-[1.2fr_1fr_1fr_1fr] gap-2 px-1 pb-2 text-[9px] font-semibold tracking-[0.12em] uppercase text-[var(--axiom-text-tertiary)]">
              <span>Platform</span><span>Type</span><span>Date</span><span>Status</span>
            </div>
            {contentCalendar.map((c, i) => (
              <motion.div key={c.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 + i * 0.05 }} className="grid grid-cols-[1.2fr_1fr_1fr_1fr] items-center gap-2 px-1 py-2.5 border-b last:border-b-0" style={{ borderColor: "rgba(240,241,243,0.04)" }}>
                <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{c.platform}</span>
                <span className="text-[11px] text-[var(--axiom-text-secondary)]">{c.contentType}</span>
                <span className="text-[11px] tabular-nums text-[var(--axiom-text-secondary)]">{c.date}</span>
                <span>
                  <StatusChip label={c.status === "warning" ? "QC REVIEW" : c.status === "healthy" ? "SCHEDULED" : "DRAFT"} tone={c.status} />
                </span>
              </motion.div>
            ))}
          </div>
        </Panel>

        <Panel className="min-w-0">
          <SectionTitle title="Content Library" hint={`${contentLibrary.length} assets`} />
          <div className="px-3 pb-4 grid grid-cols-1 gap-2.5">
            {contentLibrary.map((a, i) => (
              <motion.div key={a.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 + i * 0.05 }} className="flex items-center gap-3 rounded-xl border px-2.5 py-2" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
                <div className="w-10 h-10 rounded-lg flex-shrink-0 flex items-center justify-center text-white relative overflow-hidden" style={{ background: kindHue[a.kind] }}>
                  <span className="text-[8px] font-bold tracking-wider">{a.kind.slice(0, 4)}</span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[12px] font-medium text-[var(--axiom-text-primary)] truncate">{a.title}</p>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{a.platform}</p>
                </div>
                <StatusChip label={a.status === "healthy" ? "READY" : a.status === "warning" ? "QC FAIL" : "DRAFT"} tone={a.status} />
              </motion.div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}