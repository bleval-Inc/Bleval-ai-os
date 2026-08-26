"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { BLEVAL_GRADIENT, BLEVAL_ACCENT, BLEVAL_VIOLET, BLEVAL_CYAN } from "./types";
import { wsKpis, performanceSeries, salesPipeline, jensonBriefing } from "./bleval-ws-data";
import { WSSparkline, PerformanceChart } from "./bleval-charts";

interface BlevalDashboardProps {
  onOpenJenson: () => void;
}

function Panel({
  children,
  className,
  style,
}: {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={cn("relative rounded-2xl border backdrop-blur-xl overflow-hidden min-w-0", className)}
      style={{
        borderColor: "rgba(109,124,255,0.14)",
        background: "rgba(15,18,24,0.42)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function SectionTitle({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex items-center justify-between mb-3 px-4 pt-4">
      <h4 className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)]">
        {title}
      </h4>
      {hint && <span className="text-[10px] font-medium text-[var(--axiom-text-tertiary)]/70">{hint}</span>}
    </div>
  );
}

function KpiCard({ kpi, index }: { kpi: (typeof wsKpis)[number]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 + index * 0.07, ease: "easeOut" }}
      className="relative flex flex-col rounded-2xl p-4 border overflow-hidden min-w-0"
      style={{
        borderColor: "rgba(109,124,255,0.12)",
        background: "linear-gradient(145deg, rgba(109,124,255,0.05) 0%, rgba(168,140,255,0.04) 100%)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)",
      }}
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3" style={{ background: "linear-gradient(90deg, transparent, rgba(109,124,255,0.6), transparent)" }} />
      <div className="flex items-center justify-between mb-2">
        <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)]">{kpi.label}</span>
        <span
          className={cn(
            "text-[10px] font-medium tabular-nums",
            kpi.trend === "up" ? "text-emerald-400/90" : "text-rose-400/90",
          )}
        >
          {kpi.delta}
        </span>
      </div>
      <div className="flex items-end justify-between gap-3">
        <p className="text-2xl font-medium leading-none text-[var(--axiom-text-primary)] tabular-nums">{kpi.value}</p>
        <div className="w-16 h-9 flex-shrink-0 -mb-1">
          <WSSparkline series={kpi.series} width={64} height={36} />
        </div>
      </div>
    </motion.div>
  );
}

function Pipeline() {
  const max = Math.max(...salesPipeline.map((s) => s.value));
  return (
    <div className="flex flex-col gap-2.5">
      {salesPipeline.map((stage, i) => (
        <motion.div key={stage.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 + i * 0.06 }}>
          <div className="flex items-center justify-between mb-1 text-[11px]">
            <span className="text-[var(--axiom-text-secondary)] font-medium">{stage.label}</span>
            <span className="text-[var(--axiom-text-primary)] font-semibold tabular-nums">{stage.value}</span>
          </div>
          <div className="h-[7px] rounded-full" style={{ background: "rgba(109,124,255,0.1)" }}>
            <motion.div
              className="h-full rounded-full"
              style={{
                width: `${(stage.value / max) * 100}%`,
                background:
                  i === 0
                    ? BLEVAL_GRADIENT
                    : i < 3
                      ? `linear-gradient(90deg, ${BLEVAL_ACCENT}, ${BLEVAL_VIOLET})`
                      : `linear-gradient(90deg, ${BLEVAL_CYAN}, ${BLEVAL_ACCENT})`,
              }}
              initial={{ width: 0 }}
              animate={{ width: `${(stage.value / max) * 100}%` }}
              transition={{ duration: 0.8, delay: 0.35 + i * 0.06, ease: "easeOut" }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
}

const PRIORITY_KIND_LABEL: Record<string, string> = {
  prospects: "follow-ups",
  calls: "calls",
  projects: "in production",
  approvals: "awaiting review",
  content: "assets",
};

function JensonBriefing({ onOpenJenson }: { onOpenJenson: () => void }) {
  const b = jensonBriefing;
  return (
    <Panel className="p-0 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 60% 120% at 0% 0%, rgba(109,124,255,0.10), transparent 60%)" }} />
      <div className="relative flex flex-col lg:flex-row">
        {/* Left — content */}
        <div className="flex-1 min-w-0 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center text-white" style={{ background: BLEVAL_GRADIENT, boxShadow: "0 0 18px -2px rgba(109,124,255,0.5)" }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4l8 8-8 8v-4" /><path d="M4 14h8" /></svg>
            </div>
            <div className="flex items-center gap-2.5">
              <div>
                <h4 className="text-[13px] font-semibold tracking-wide text-[var(--axiom-text-primary)]">JENSON</h4>
                <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">COO — BLEVAL INC</p>
              </div>
              <div className="ml-2 flex items-center gap-1.5 rounded-full px-2 py-0.5 border" style={{ borderColor: "rgba(34,211,119,0.25)", background: "rgba(34,211,119,0.06)" }}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[9px] font-semibold tracking-wider text-emerald-400">ONLINE</span>
              </div>
            </div>
          </div>

          <p className="text-sm font-medium text-[var(--axiom-text-primary)]">{b.salutation}</p>
          <p className="text-[13px] text-[var(--axiom-text-secondary)] mt-1">{b.statusLine}</p>

          <div className="mt-5 mb-2 text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)]">
            Today&apos;s priorities
          </div>
          <ul className="space-y-2">
            {b.priorities.map((p) => (
              <li key={p.label} className="flex items-center gap-2.5 text-[12px]">
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: BLEVAL_ACCENT }} />
                <span className="text-[var(--axiom-text-primary)]">{p.meta}</span>
                <span className="text-[var(--axiom-text-secondary)]">{p.label}</span>
                <span className="text-[var(--axiom-text-tertiary)]/70 text-[10px]">{PRIORITY_KIND_LABEL[p.kind]}</span>
              </li>
            ))}
          </ul>

          <div className="mt-5 rounded-xl border p-3.5" style={{ borderColor: "rgba(168,140,255,0.16)", background: "rgba(168,140,255,0.05)" }}>
            <div className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-violet)] mb-1.5">Recommendation</div>
            <p className="text-[12px] leading-relaxed text-[var(--axiom-text-secondary)]">{b.recommendation}</p>
          </div>
        </div>

        {/* Right — OPEN JENSON */}
        <div className="flex items-center justify-center p-5 border-l lg:w-[200px] border-t lg:border-t-0 shrink-0" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
          <motion.button
            onClick={onOpenJenson}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-[12px] font-semibold text-white"
            style={{ background: BLEVAL_GRADIENT, boxShadow: "0 6px 24px -6px rgba(109,124,255,0.6)" }}
          >
            <span>OPEN JENSON</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14" /><path d="M12 5l7 7-7 7" /></svg>
          </motion.button>
        </div>
      </div>
    </Panel>
  );
}

export default function BlevalDashboard({ onOpenJenson }: BlevalDashboardProps) {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-28 min-w-0">
      {/* Identity header */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white relative overflow-hidden" style={{ background: BLEVAL_GRADIENT, boxShadow: "0 0 26px -4px rgba(109,124,255,0.55)" }}>
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="relative">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">BLEVAL INC</h1>
            <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">Autonomous Agency Operations</p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-full px-3 py-1.5 border self-start" style={{ borderColor: "rgba(34,211,119,0.25)", background: "rgba(34,211,119,0.06)" }}>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] font-semibold tracking-widest text-emerald-400">OPERATIONAL</span>
        </div>
      </motion.div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {wsKpis.map((kpi, i) => (
          <KpiCard key={kpi.key} kpi={kpi} index={i} />
        ))}
      </div>

      {/* Revenue + Pipeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-w-0">
        <Panel className="lg:col-span-2 min-w-0">
          <SectionTitle title="Revenue Performance" hint="Last 8 months · R'000" />
          <div className="px-4 pb-4 flex items-baseline gap-3">
            <span className="text-xl font-semibold text-[var(--axiom-text-primary)] tabular-nums">R125,400</span>
            <span className="text-[11px] font-medium text-emerald-400/90">+18.4% this period</span>
            <div className="ml-auto flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-[10px] text-[var(--axiom-text-secondary)]">
                <span className="w-2 h-2 rounded-full" style={{ background: BLEVAL_ACCENT }} /> Revenue
              </span>
              <span className="flex items-center gap-1.5 text-[10px] text-[var(--axiom-text-secondary)]">
                <span className="w-2 h-2 rounded-full" style={{ background: BLEVAL_VIOLET }} /> Net Profit
              </span>
            </div>
          </div>
          <div className="px-3 h-[220px] min-w-0">
            <PerformanceChart series={performanceSeries} height={220} />
          </div>
        </Panel>

        <Panel className="min-w-0">
          <SectionTitle title="Sales Pipeline" hint={`${salesPipeline[0].value} prospects`} />
          <div className="px-4 pb-5">
            <Pipeline />
          </div>
        </Panel>
      </div>

      {/* Jenson briefing */}
      <JensonBriefing onOpenJenson={onOpenJenson} />
    </div>
  );
}