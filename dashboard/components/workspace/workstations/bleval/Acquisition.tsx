"use client";

import { motion } from "framer-motion";
import { Panel, SectionTitle, WorkspaceHeader, KpiGrid, StatusChip, FunnelBars } from "./bleval-ui";
import { BLEVAL_ACCENT } from "./types";
import { acquisitionKpis, acquisitionFunnel, leadColumns, outreachChannels, jensonOversight } from "./acquisition-data";

export default function Acquisition() {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-28 min-w-0">
      <WorkspaceHeader
        icon="acquisition"
        title="ACQUISITION"
        subtitle="Automated prospect discovery and client acquisition"
        right={<StatusChip label="CAMPAIGN LIVE" tone="active" />}
      />

      <KpiGrid kpis={acquisitionKpis} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="min-w-0">
          <SectionTitle title="Acquisition Funnel" hint="All pipeline" />
          <div className="px-4 pb-5">
            <FunnelBars stages={acquisitionFunnel} />
          </div>
        </Panel>

        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Lead Pipeline" hint="Drag-ready columns" />
          <div className="px-3 pb-4 overflow-x-auto hide-scrollbar">
            <div className="flex gap-3 min-w-[900px]">
              {leadColumns.map((col, ci) => (
                <div key={col.id} className="flex-1 min-w-[120px]">
                  <div className="flex items-center justify-between px-1 mb-2">
                    <span className="text-[10px] font-semibold tracking-[0.14em] uppercase text-[var(--axiom-text-secondary)]">{col.label}</span>
                    <span className="w-5 h-5 flex items-center justify-center rounded-md text-[10px] font-semibold tabular-nums" style={{ background: "rgba(109,124,255,0.12)", color: "var(--axiom-text-primary)" }}>{col.leads.length}</span>
                  </div>
                  <div className="flex flex-col gap-2">
                    {col.leads.map((lead, li) => (
                      <motion.div
                        key={lead.id}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + ci * 0.06 + li * 0.04 }}
                        className="rounded-xl border px-3 py-2.5"
                        style={{ borderColor: "rgba(109,124,255,0.1)", background: "rgba(10,12,16,0.45)" }}
                      >
                        <p className="text-[12px] font-medium text-[var(--axiom-text-primary)] truncate">{lead.company}</p>
                        <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{lead.contact} · {lead.industry}</p>
                        <div className="mt-1.5">
                          <span className="inline-flex rounded-md px-1.5 py-0.5 text-[9px] font-semibold tabular-nums" style={{ background: "rgba(109,124,255,0.1)", color: "var(--axiom-accent-hover)" }}>{lead.value}</span>
                        </div>
                      </motion.div>
                    ))}
                    {col.leads.length === 0 && (
                      <div className="rounded-xl border border-dashed px-3 py-4 text-center text-[10px] text-[var(--axiom-text-tertiary)]/60" style={{ borderColor: "rgba(240,241,243,0.06)" }}>Empty</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Outreach Activity" hint="This week" />
          <div className="px-4 pb-4 flex flex-col">
            <div className="grid grid-cols-[1fr_repeat(3,64px)_92px] gap-2 px-1 pb-2 text-[9px] font-semibold tracking-[0.12em] uppercase text-[var(--axiom-text-tertiary)]">
              <span>Channel</span><span className="text-right">Sent</span><span className="text-right">Responded</span><span className="text-right">Rate</span><span className="text-right">Status</span>
            </div>
            {outreachChannels.map((c, i) => (
              <motion.div key={c.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 + i * 0.05 }} className="grid grid-cols-[1fr_repeat(3,64px)_92px] items-center gap-2 px-1 py-2 border-b last:border-b-0" style={{ borderColor: "rgba(240,241,243,0.04)" }}>
                <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{c.label}</span>
                <span className="text-right text-[12px] tabular-nums text-[var(--axiom-text-secondary)]">{c.sent}</span>
                <span className="text-right text-[12px] tabular-nums text-[var(--axiom-text-secondary)]">{c.responded}</span>
                <span className="text-right text-[12px] tabular-nums text-emerald-400/90">{c.sent ? Math.round((c.responded / c.sent) * 100) : 0}%</span>
                <span className="text-right">
                  <StatusChip label={c.status.toUpperCase()} tone={c.status === "paused" ? "neutral" : "healthy"} />
                </span>
              </motion.div>
            ))}
          </div>
        </Panel>

        <Panel className="min-w-0" style={{ borderColor: "rgba(168,140,255,0.18)" }}>
          <SectionTitle title="Jenson Oversight" hint="Monitoring acquisition" />
          <div className="px-4 pb-5 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[11px] font-medium text-[var(--axiom-text-secondary)]">Jenson is monitoring acquisition.</span>
            </div>
            <div className="rounded-xl border p-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}>
              <div className="flex justify-between text-[11px] py-1"><span className="text-[var(--axiom-text-tertiary)]">Current campaign</span><span className="text-[var(--axiom-text-primary)] font-medium">{jensonOversight.campaign}</span></div>
              <div className="flex justify-between text-[11px] py-1"><span className="text-[var(--axiom-text-tertiary)]">Active workflow</span><span className="text-[var(--axiom-text-primary)] font-medium">{jensonOversight.workflow}</span></div>
              <div className="flex justify-between text-[11px] py-1"><span className="text-[var(--axiom-text-tertiary)]">Leads needing attention</span><span className="text-[var(--axiom-text-warning)] font-semibold tabular-nums">{jensonOversight.attentionLeads}</span></div>
            </div>
            <div>
              <div className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)] mb-2">Recommendations</div>
              <ul className="space-y-2">
                {jensonOversight.recommendations.map((r, i) => (
                  <li key={i} className="flex gap-2 text-[11px] leading-snug text-[var(--axiom-text-secondary)]">
                    <span className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0" style={{ background: BLEVAL_ACCENT }} />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}