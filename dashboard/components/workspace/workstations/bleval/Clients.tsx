"use client";

import { motion } from "framer-motion";
import { Panel, SectionTitle, WorkspaceHeader, KpiGrid, StatusChip, StageFlow } from "./bleval-ui";
import { BLEVAL_ACCENT, BLEVAL_VIOLET, type StatusTone } from "./types";
import { clientsKpis, clientPipeline, clientList, activeProjects, clientHealth } from "./clients-data";

const healthLabel: Record<StatusTone, string> = {
  healthy: "HEALTHY",
  active: "ONBOARDING",
  warning: "ATTENTION",
  danger: "AT RISK",
  neutral: "—",
};

export default function Clients() {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-28 min-w-0">
      <WorkspaceHeader
        icon="clients"
        title="CLIENTS"
        subtitle="Client relationships, projects and delivery"
        right={
          <>
            <StatusChip label="14 ACTIVE" tone="healthy" />
            <StatusChip label="1 AT RISK" tone="danger" />
          </>
        }
      />

      <KpiGrid kpis={clientsKpis} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="min-w-0">
          <SectionTitle title="Client Pipeline" hint="Acquire → Retain" />
          <div className="px-4 pb-5">
            <StageFlow stages={clientPipeline} currentIndex={5} />
          </div>
        </Panel>

        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Client List" hint={`${clientList.length} records`} />
          <div className="px-4 pb-4 overflow-x-auto hide-scrollbar">
            <div className="min-w-[720px]">
              <div className="grid grid-cols-[1.4fr_1fr_1fr_1fr_1.2fr_0.7fr_0.9fr] gap-2 px-1 pb-2 text-[9px] font-semibold tracking-[0.12em] uppercase text-[var(--axiom-text-tertiary)]">
                <span>Business</span><span>Industry</span><span>Status</span><span>Project</span><span>Revenue</span><span>Retainer</span><span>Health</span>
              </div>
              <div className="flex flex-col">
                {clientList.map((c, i) => (
                  <motion.div key={c.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.12 + i * 0.05 }} className="grid grid-cols-[1.4fr_1fr_1fr_1fr_1.2fr_0.7fr_0.9fr] items-center gap-2 px-1 py-2.5 border-b last:border-b-0" style={{ borderColor: "rgba(240,241,243,0.04)" }}>
                    <span className="text-[12px] font-medium text-[var(--axiom-text-primary)] truncate">{c.business}</span>
                    <span className="text-[11px] text-[var(--axiom-text-secondary)]">{c.industry}</span>
                    <span className="text-[11px] text-[var(--axiom-text-secondary)]">{c.status}</span>
                    <span className="text-[11px] text-[var(--axiom-text-secondary)] truncate">{c.project}</span>
                    <span className="text-[11px] tabular-nums text-[var(--axiom-text-primary)]">{c.revenue}</span>
                    <span className="text-[11px] text-[var(--axiom-text-secondary)]">{c.retainer}</span>
                    <span><StatusChip label={healthLabel[c.health]} tone={c.health} /></span>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Active Projects" hint={`${activeProjects.length} in flight`} />
          <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            {activeProjects.map((p, i) => (
              <motion.div key={p.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 + i * 0.05 }} className="rounded-xl border p-3.5" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{p.project}</span>
                  <span className="text-[11px] tabular-nums text-[var(--axiom-text-primary)] font-semibold">{p.progress}%</span>
                </div>
                <p className="text-[10px] text-[var(--axiom-text-tertiary)] mb-3">{p.client} · {p.workflow}</p>
                <div className="h-[5px] rounded-full mb-2" style={{ background: "rgba(109,124,255,0.1)" }}>
                  <motion.div className="h-full rounded-full" style={{ background: `linear-gradient(90deg,${BLEVAL_ACCENT},${BLEVAL_VIOLET})` }} initial={{ width: 0 }} animate={{ width: `${p.progress}%` }} transition={{ duration: 0.8, delay: 0.2 + i * 0.05 }} />
                </div>
                <div className="flex items-center justify-between text-[10px] text-[var(--axiom-text-tertiary)]">
                  <span>Stage: {p.stage}</span>
                  <span>Due {p.deadline}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </Panel>

        <Panel className="min-w-0">
          <SectionTitle title="Client Health" hint="Delivery signals" />
          <div className="px-4 pb-4 flex flex-col gap-3">
            {clientHealth.map((h, i) => (
              <motion.div key={h.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.06 }} className="rounded-xl border p-3.5" style={{ borderColor: h.tone === "danger" ? "rgba(255,77,106,0.2)" : h.tone === "warning" ? "rgba(255,184,48,0.18)" : "rgba(240,241,243,0.06)" }}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{h.client}</span>
                  <StatusChip label={healthLabel[h.tone]} tone={h.tone} />
                </div>
                <p className="text-[11px] leading-snug text-[var(--axiom-text-secondary)]">{h.detail}</p>
              </motion.div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}