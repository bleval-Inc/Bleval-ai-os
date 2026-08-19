"use client";

import { motion } from "framer-motion";
import { Panel, SectionTitle, WorkspaceHeader, KpiGrid, StatusChip, StageFlow } from "./bleval-ui";
import { BLEVAL_ACCENT, BLEVAL_VIOLET, type StatusTone } from "./types";
import { operationsKpis, workflows, agents, productionPipeline, activityEvents } from "./operations-data";

const agentTone: Record<string, StatusTone> = {
  ACTIVE: "healthy",
  WORKING: "active",
  STANDBY: "neutral",
};

export default function Operations() {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-28 min-w-0">
      <WorkspaceHeader
        icon="operations"
        title="OPERATIONS"
        subtitle="Automated agency operations and workflow control"
        right={<StatusChip label="6 WORKFLOWS ACTIVE" tone="active" />}
      />

      <KpiGrid kpis={operationsKpis} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="min-w-0">
          <SectionTitle title="Production Pipeline" hint="Company flow" />
          <div className="px-4 pb-5">
            <StageFlow stages={productionPipeline} currentIndex={4} />
          </div>
        </Panel>

        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Workflow Monitor" hint={`${workflows.length} tracked`} />
          <div className="px-4 pb-4 flex flex-col gap-2.5">
            {workflows.map((w, i) => (
              <motion.div key={w.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 + i * 0.05 }} className="rounded-xl border px-3.5 py-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{w.name}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{w.stage}</span>
                    <span className="text-[10px] tabular-nums text-[var(--axiom-text-tertiary)]">{w.tasks} tasks</span>
                    <StatusChip label={w.status.toUpperCase().replace("_", " ")} tone={w.status} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-[5px] rounded-full" style={{ background: "rgba(109,124,255,0.1)" }}>
                    <motion.div className="h-full rounded-full" style={{ background: w.status === "warning" ? "linear-gradient(90deg,#ffb830,#ff8a4d)" : `linear-gradient(90deg,${BLEVAL_ACCENT},${BLEVAL_VIOLET})` }} initial={{ width: 0 }} animate={{ width: `${w.progress}%` }} transition={{ duration: 0.8, delay: 0.2 + i * 0.05 }} />
                  </div>
                  <span className="text-[11px] tabular-nums text-[var(--axiom-text-primary)] font-semibold w-8 text-right">{w.progress}%</span>
                </div>
              </motion.div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Agent Activity" hint="Background workers" />
          <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {agents.map((a, i) => (
              <motion.div key={a.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 + i * 0.05 }} className="flex items-center gap-3 rounded-xl border px-3.5 py-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white flex-shrink-0" style={{ background: a.state === "STANDBY" ? "rgba(240,241,243,0.12)" : `linear-gradient(135deg,${BLEVAL_ACCENT},${BLEVAL_VIOLET})` }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="8" width="16" height="12" rx="2" /><circle cx="12" cy="14" r="2.5" /><path d="M9 8V7a3 3 0 0 1 6 0v1" /></svg>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{a.name}</span>
                    <StatusChip label={a.state} tone={agentTone[a.state]} />
                  </div>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)] truncate">{a.task}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </Panel>

        <Panel className="min-w-0">
          <SectionTitle title="System Activity" hint="Latest events" />
          <div className="px-4 pb-4 flex flex-col gap-2.5">
            {activityEvents.map((e, i) => (
              <motion.div key={e.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.06 }} className="flex items-start gap-2.5">
                <span className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: "rgba(34,211,119,0.12)" }}>
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#22d377" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
                </span>
                <p className="text-[11px] leading-snug text-[var(--axiom-text-secondary)]">{e.text}</p>
                <span className="ml-auto text-[9px] tabular-nums text-[var(--axiom-text-tertiary)] flex-shrink-0">{e.time}</span>
              </motion.div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}