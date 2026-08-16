"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAxiomStore } from "@/lib/store/axiom-store";
import { cn } from "@/lib/utils";
import { blevalData, type KPI } from "./bleval-data";
import { RevenueAreaChart, Sparkline, DonutChart } from "./bleval-charts";

const identity = "linear-gradient(135deg, #6d7cff 0%, #a88cff 100%)";
const BLEVAL = "BLEVAL INC";

function PanelTitle({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h4 className="text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)]">
        {title}
      </h4>
      {hint && <span className="text-[10px] text-[var(--axiom-text-tertiary)]/70 font-medium">{hint}</span>}
    </div>
  );
}

function KpiCard({ kpi, index }: { kpi: KPI; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.25 + index * 0.08, ease: "easeOut" }}
      className="relative flex flex-col rounded-2xl p-3.5 overflow-hidden border"
      style={{
        background: "linear-gradient(145deg, rgba(109,124,255,0.05) 0%, rgba(168,140,255,0.04) 100%)",
        borderColor: "rgba(109,124,255,0.12)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)",
      }}
    >
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3"
        style={{ background: "linear-gradient(90deg, transparent, rgba(109,124,255,0.6), transparent)" }}
      />
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)]">
          {kpi.label}
        </span>
        <span
          className={cn(
            "text-[10px] font-medium tabular-nums",
            kpi.trend === "up" ? "text-emerald-400/90" : "text-rose-400/90",
          )}
        >
          {kpi.delta}
        </span>
      </div>
      <p className="text-[22px] leading-none font-medium text-[var(--axiom-text-primary)] tabular-nums mb-2">
        {kpi.value}
      </p>
      <div className="h-9 -mx-1">
        <Sparkline series={kpi.series} height={36} width={96} />
      </div>
    </motion.div>
  );
}

function ClientRow({ c, index }: { c: (typeof blevalData.clients)[number]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: 0.4 + index * 0.07 }}
      className="flex items-center gap-2.5 rounded-xl px-2.5 py-2 transition-colors"
      style={{ border: "1px solid transparent" }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "rgba(109,124,255,0.14)";
        (e.currentTarget as HTMLElement).style.background = "rgba(109,124,255,0.04)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "transparent";
        (e.currentTarget as HTMLElement).style.background = "transparent";
      }}
    >
      <div
        className={cn(
          "w-9 h-9 rounded-lg flex items-center justify-center text-[11px] font-semibold text-white flex-shrink-0 bg-gradient-to-br",
          c.hue,
        )}
      >
        {c.initials}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-medium text-[var(--axiom-text-primary)] truncate">{c.name}</p>
        <p className="text-[10px] text-[var(--axiom-text-tertiary)] truncate">{c.initiative}</p>
      </div>
      <span className="text-[10px] font-medium tabular-nums text-emerald-400/90 flex-shrink-0">{c.value}</span>
    </motion.div>
  );
}

export default function BLEVALConsole() {
  const router = useRouter();
  const { setActiveWorkstation } = useAxiomStore();
  const d = blevalData;
  const maxStage = Math.max(...d.funnel.stages.map((s) => s.value));

  const openWorkstation = () => {
    setActiveWorkstation("bleval");
    router.push("/bleval");
  };

  return (
    <div
      className="relative w-full h-full rounded-3xl overflow-hidden backdrop-blur-xl flex flex-col"
      style={{
        background: `
          radial-gradient(ellipse at top left, rgba(109,124,255,0.09) 0%, transparent 55%),
          radial-gradient(ellipse at bottom right, rgba(168,140,255,0.07) 0%, transparent 50%),
          linear-gradient(150deg, rgba(10,12,16,0.6) 0%, rgba(15,18,24,0.6) 100%)
        `,
        border: "1px solid rgba(109,124,255,0.16)",
        boxShadow: `
          0 8px 40px -12px rgba(109,124,255,0.18),
          inset 0 1px 0 rgba(255,255,255,0.03)
        `,
      }}
    >
      {/* Scanline texture */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(240,241,243,0.6) 2px, rgba(240,241,243,0.6) 4px)",
        }}
      />

      {/* Header */}
      <div className="relative flex items-center justify-between px-5 pt-4 pb-3 border-b border-[rgba(109,124,255,0.12)] z-10">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-white relative overflow-hidden"
            style={{
              background: identity,
              boxShadow: "0 0 24px -4px rgba(109,124,255,0.55)",
            }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="relative">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-tight text-[var(--axiom-text-primary)]">{BLEVAL}</h3>
            <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">
              Company Operations
            </p>
          </div>
        </div>

        <motion.button
          onClick={openWorkstation}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-accent-hover)] transition-colors"
          style={{ border: "1px solid rgba(109,124,255,0.15)", background: "rgba(109,124,255,0.05)" }}
          aria-label="Open BLEVAL INC workstation"
        >
          <span>Workstation</span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17L17 7M7 7h10v10" />
          </svg>
        </motion.button>
      </div>

      {/* Scrollable content */}
      <div className="relative flex-1 min-h-0 overflow-y-auto hide-scrollbar px-5 pb-5 z-10 flex flex-col gap-4">
        {/* Revenue Overview */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.12, ease: "easeOut" }}
          className="mt-4 rounded-2xl p-4 border"
          style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(109,124,255,0.03)" }}
        >
          <div className="flex items-end justify-between mb-2">
            <div>
              <p className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)]">
                Revenue Overview
              </p>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-2xl font-semibold text-[var(--axiom-text-primary)] tabular-nums">
                  {d.revenueTotal}
                </span>
                <span className="text-[11px] font-medium text-emerald-400/90">{d.revenueDelta} this period</span>
              </div>
            </div>
          </div>
          <div className="h-[164px] -mx-1">
            <RevenueAreaChart series={d.revenueSeries} height={164} />
          </div>
        </motion.section>

        {/* KPI row */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
          {d.kpis.map((kpi, i) => (
            <KpiCard key={kpi.key} kpi={kpi} index={i} />
          ))}
        </div>

        {/* Three panels */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* CLIENTS */}
          <section
            className="rounded-2xl p-4 border flex flex-col min-h-0"
            style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}
          >
            <PanelTitle title="CLIENTS" hint={`${d.clients.length} active`} />
            <div className="flex-1 flex flex-col gap-1">
              {d.clients.map((c, i) => (
                <ClientRow key={c.id} c={c} index={i} />
              ))}
            </div>
          </section>

          {/* SALES FUNNEL */}
          <section
            className="rounded-2xl p-4 border flex flex-col min-h-0"
            style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}
          >
            <PanelTitle title="SALES FUNNEL" hint={d.funnel.total} />
            <div className="flex-1 flex flex-col justify-center gap-4">
              {d.funnel.stages.map((s, i) => (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                >
                  <div className="flex items-center justify-between mb-1.5 text-[11px]">
                    <span className="text-[var(--axiom-text-secondary)] font-medium">{s.label}</span>
                    <span className="text-[var(--axiom-text-primary)] font-semibold tabular-nums">{s.value}%</span>
                  </div>
                  <div className="h-2 rounded-full" style={{ background: "rgba(109,124,255,0.1)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{
                        width: `${(s.value / maxStage) * 100}%`,
                        background: i === 0 ? identity : i === 1 ? "linear-gradient(90deg,#6d7cff,#a88cff)" : "linear-gradient(90deg,#00d4ff,#6d7cff)",
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${(s.value / maxStage) * 100}%` }}
                      transition={{ duration: 0.8, delay: 0.55 + i * 0.1, ease: "easeOut" }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </section>

          {/* REVENUE BREAKDOWN */}
          <section
            className="rounded-2xl p-4 border flex flex-col min-h-0"
            style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}
          >
            <PanelTitle title="REVENUE BREAKDOWN" hint={d.breakdown.total} />
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.45 }}
                className="relative"
              >
                <DonutChart slices={d.breakdown.slices} size={148} />
              </motion.div>
              <div className="grid grid-cols-3 gap-2 w-full">
                {d.breakdown.slices.map((s) => (
                  <div key={s.id} className="flex flex-col items-center gap-1">
                    <div className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide">{s.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}