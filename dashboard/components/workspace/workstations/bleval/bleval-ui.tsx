"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { BLEVAL_GRADIENT, BLEVAL_ACCENT, BLEVAL_VIOLET, BLEVAL_CYAN, type StatusTone, type MetricKpi, type FlowStage, type BaseIcon } from "./types";
import { WSSparkline } from "./bleval-charts";

// ── Glyph ────────────────────────────────────────────────────────────────────
export function Glyph({ name, size = 16 }: { name: BaseIcon; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "dashboard":
      return <svg {...common}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>;
    case "jenson":
      return <svg {...common}><path d="M12 8V4l8 8-8 8v-4" /><path d="M4 14h8" /></svg>;
    case "truth":
      return <svg {...common}><path d="M9 3h6v3h3v3h3v9h-3v3h-3v3H9v-3H6v-3H3V9h3V6h3z" /><circle cx="12" cy="12" r="2.5" /><path d="M12 7v3M12 14v3" /><path d="M7 12h3M14 12h3" /></svg>;
    case "acquisition":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /><path d="M14.5 8.5l-2.6 3.8-1.4-1-2 2.4" /></svg>;
    case "content":
      return <svg {...common}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="M8 13h8M8 17h5" /></svg>;
    case "clients":
      return <svg {...common}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>;
    case "operations":
      return <svg {...common}><circle cx="5" cy="12" r="2" /><circle cx="19" cy="12" r="2" /><path d="M7 12h10" /><path d="M12 7v10" /></svg>;
  }
}

// ── Surfaces ─────────────────────────────────────────────────────────────────
export function Panel({ children, className, style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
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

export function SectionTitle({ title, hint, className }: { title: string; hint?: string; className?: string }) {
  return (
    <div className={cn("flex items-center justify-between mb-3 px-4 pt-4", className)}>
      <h4 className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)]">{title}</h4>
      {hint && <span className="text-[10px] font-medium text-[var(--axiom-text-tertiary)]/70">{hint}</span>}
    </div>
  );
}

export function Emblem({ name, size = 40 }: { name: BaseIcon; size?: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-xl text-white flex-shrink-0 relative overflow-hidden"
      style={{ width: size, height: size, background: BLEVAL_GRADIENT, boxShadow: "0 0 24px -4px rgba(109,124,255,0.5)" }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
      <div className="relative">
        <Glyph name={name} size={Math.round(size * 0.52)} />
      </div>
    </div>
  );
}

// ── Header ───────────────────────────────────────────────────────────────────
export function WorkspaceHeader({ icon, title, subtitle, right }: { icon: BaseIcon; title: string; subtitle: string; right?: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <Emblem name={icon} />
        <div>
          <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">{title}</h1>
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">{subtitle}</p>
        </div>
      </div>
      {right && <div className="flex items-center gap-2 flex-wrap">{right}</div>}
    </motion.div>
  );
}

export function StatusChip({ label, tone }: { label: string; tone: StatusTone }) {
  const map: Record<StatusTone, { dot: string; text: string; border: string; bg: string }> = {
    healthy: { dot: "bg-emerald-400", text: "text-emerald-400", border: "rgba(34,211,119,0.25)", bg: "rgba(34,211,119,0.06)" },
    active: { dot: "bg-[var(--axiom-accent)]", text: "text-[var(--axiom-accent-hover)]", border: "rgba(109,124,255,0.28)", bg: "rgba(109,124,255,0.06)" },
    warning: { dot: "bg-amber-400", text: "text-amber-400", border: "rgba(255,184,48,0.28)", bg: "rgba(255,184,48,0.06)" },
    danger: { dot: "bg-rose-400", text: "text-rose-400", border: "rgba(255,77,106,0.28)", bg: "rgba(255,77,106,0.06)" },
    neutral: { dot: "bg-[var(--axiom-text-tertiary)]", text: "text-[var(--axiom-text-secondary)]", border: "rgba(240,241,243,0.1)", bg: "rgba(240,241,243,0.03)" },
  };
  const c = map[tone];
  return (
    <div className="flex items-center gap-1.5 rounded-full px-3 py-1 border" style={{ borderColor: c.border, background: c.bg }}>
      <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", c.dot)} />
      <span className={cn("text-[9px] font-semibold tracking-widest", c.text)}>{label}</span>
    </div>
  );
}

// ── Metric card ──────────────────────────────────────────────────────────────
export function MetricCard({ kpi, index, className }: { kpi: MetricKpi; index: number; className?: string }) {
  const hasSpark = !!kpi.series && kpi.series.length > 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 + index * 0.07, ease: "easeOut" }}
      className={cn("relative flex flex-col rounded-2xl p-4 border overflow-hidden min-w-0", className)}
      style={{
        borderColor: "rgba(109,124,255,0.12)",
        background: "linear-gradient(145deg, rgba(109,124,255,0.05) 0%, rgba(168,140,255,0.04) 100%)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)",
      }}
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3" style={{ background: "linear-gradient(90deg, transparent, rgba(109,124,255,0.6), transparent)" }} />
      <div className="flex items-center justify-between mb-2">
        <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)]">{kpi.label}</span>
        {kpi.delta && (
          <span className={cn("text-[10px] font-medium tabular-nums", kpi.trend === "down" ? "text-rose-400/90" : "text-emerald-400/90")}>
            {kpi.delta}
          </span>
        )}
      </div>
      <div className={cn("flex items-end justify-between gap-3", hasSpark && "min-h-[36px]")}>
        <p className="text-2xl font-medium leading-none text-[var(--axiom-text-primary)] tabular-nums">{kpi.value}</p>
        {hasSpark && (
          <div className="w-16 h-9 flex-shrink-0 -mb-1">
            <WSSparkline series={kpi.series!} width={64} height={36} />
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function KpiGrid({ kpis }: { kpis: MetricKpi[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {kpis.map((kpi, i) => (
        <MetricCard key={kpi.key} kpi={kpi} index={i} />
      ))}
    </div>
  );
}

// ── Stage flow (vertical connected steps) ────────────────────────────────────
export function StageFlow({ stages, currentIndex = -1, className }: { stages: FlowStage[]; currentIndex?: number; className?: string }) {
  return (
    <div className={cn("relative", className)}>
      {/* Connector line behind the dots */}
      <div className="absolute left-[7px] top-2 bottom-2 w-px" style={{ background: "linear-gradient(180deg, rgba(109,124,255,0.35), rgba(168,140,255,0.15))" }} />
      <div className="flex flex-col gap-4">
        {stages.map((s, i) => {
          const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "upcoming";
          return (
            <div key={s.id} className="relative flex items-center gap-3 pl-5">
              <div
                className="absolute left-0 top-1/2 -translate-y-1/2 w-[15px] h-[15px] rounded-full flex items-center justify-center"
                style={{
                  background: state === "upcoming" ? "rgba(240,241,243,0.04)" : BLEVAL_GRADIENT,
                  border: `1px solid ${state === "upcoming" ? "rgba(240,241,243,0.12)" : "transparent"}`,
                  boxShadow: state === "current" ? "0 0 12px rgba(109,124,255,0.5)" : "none",
                }}
              >
                {state === "done" && <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>}
              </div>
              <span className={cn("text-[12px] font-medium", state === "upcoming" ? "text-[var(--axiom-text-secondary)]" : "text-[var(--axiom-text-primary)]")}>
                {s.label}
              </span>
              {state === "current" && <span className="text-[9px] font-semibold tracking-wider text-[var(--axiom-accent-hover)] uppercase">Current</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Funnel bars (counts + animated width) ────────────────────────────────────
export function FunnelBars({ stages, accentByIndex }: { stages: { id: string; label: string; value: number }[]; accentByIndex?: (i: number) => string }) {
  const max = Math.max(...stages.map((s) => s.value));
  const color = accentByIndex ?? ((i: number) => (i === 0 ? BLEVAL_GRADIENT : i < 3 ? `linear-gradient(90deg, ${BLEVAL_ACCENT}, ${BLEVAL_VIOLET})` : `linear-gradient(90deg, ${BLEVAL_CYAN}, ${BLEVAL_ACCENT})`));
  return (
    <div className="flex flex-col gap-2.5">
      {stages.map((stage, i) => (
        <motion.div key={stage.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 + i * 0.05 }}>
          <div className="flex items-center justify-between mb-1 text-[11px]">
            <span className="text-[var(--axiom-text-secondary)] font-medium">{stage.label}</span>
            <span className="text-[var(--axiom-text-primary)] font-semibold tabular-nums">{stage.value}</span>
          </div>
          <div className="h-[7px] rounded-full" style={{ background: "rgba(109,124,255,0.1)" }}>
            <motion.div
              className="h-full rounded-full"
              style={{ width: `${(stage.value / max) * 100}%`, background: color(i) }}
              initial={{ width: 0 }}
              animate={{ width: `${(stage.value / max) * 100}%` }}
              transition={{ duration: 0.8, delay: 0.3 + i * 0.05, ease: "easeOut" }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export const gradientByIndex = (i: number) => (i === 0 ? BLEVAL_GRADIENT : i === 1 ? `linear-gradient(90deg, ${BLEVAL_ACCENT}, ${BLEVAL_VIOLET})` : `linear-gradient(90deg, ${BLEVAL_CYAN}, ${BLEVAL_ACCENT})`);