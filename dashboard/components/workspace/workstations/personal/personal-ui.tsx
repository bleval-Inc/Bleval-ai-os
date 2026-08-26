"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  PERSONAL_GRADIENT,
  PERSONAL_TEAL,
  PERSONAL_CYAN,
  type BaseIcon,
  type MetricKpi,
  type StatusTone,
} from "./types";
import { Sparkline } from "./personal-charts";

// ── Glyphs (thin 1.6 stroke, matches AXIOM icon language) ───────────────────
export function Glyph({ name, size = 16 }: { name: BaseIcon; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "dashboard":
      return <svg {...common}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>;
    case "yamako":
      return <svg {...common}><circle cx="12" cy="12" r="3.2" /><circle cx="12" cy="12" r="7" opacity="0.5" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2" /></svg>;
    case "schedule":
      return <svg {...common}><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /><path d="M8 15h3M8 18h2M14 15h3M14 18h2" /></svg>;
    case "learning":
      return <svg {...common}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /><path d="M9 7h6" /></svg>;
    case "rnd":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /><path d="M14.5 8.5l-2.6 3.8-1.4-1-2 2.4" /></svg>;
    case "progress":
      return <svg {...common}><path d="M20 6L9 17l-5-5" /><circle cx="6" cy="18" r="2.4" /><circle cx="18" cy="6" r="2" /></svg>;
  }
}

// ── Surfaces ────────────────────────────────────────────────────────────────
export function Panel({ children, className, style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={cn("relative rounded-2xl border backdrop-blur-xl overflow-hidden min-w-0", className)}
      style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(15,18,24,0.42)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)", ...style }}
    >
      {children}
    </div>
  );
}

export function SectionTitle({ title, hint, className, right }: { title: string; hint?: string; className?: string; right?: React.ReactNode }) {
  return (
    <div className={cn("flex items-center justify-between mb-3 px-4 pt-4", className)}>
      <h4 className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)]">{title}</h4>
      <div className="flex items-center gap-2">
        {hint && <span className="text-[10px] font-medium text-[var(--axiom-text-tertiary)]/70">{hint}</span>}
        {right}
      </div>
    </div>
  );
}

// ── Brand emblem + header ───────────────────────────────────────────────────
export function Emblem({ size = 40 }: { size?: number }) {
  return (
    <div className="flex items-center justify-center rounded-xl text-white flex-shrink-0 relative overflow-hidden" style={{ width: size, height: size, background: PERSONAL_GRADIENT, boxShadow: "0 0 24px -4px rgba(109,124,255,0.5)" }}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
      <svg width={Math.round(size * 0.5)} height={Math.round(size * 0.5)} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="relative">
        <circle cx="12" cy="12" r="3.2" />
        <circle cx="12" cy="12" r="7" opacity="0.5" />
        <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
      </svg>
    </div>
  );
}

export function WorkspaceHeader({ title, subtitle, right }: { title: string; subtitle: string; right?: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <Emblem />
        <div>
          <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">{title}</h1>
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">{subtitle}</p>
        </div>
      </div>
      {right && <div className="flex items-center gap-2 flex-wrap">{right}</div>}
    </motion.div>
  );
}

export function StatusChip({ label, tone, icon }: { label: string; tone: StatusTone; icon?: React.ReactNode }) {
  const map: Record<StatusTone, { dot: string; text: string; border: string; bg: string }> = {
    healthy: { dot: "bg-emerald-400", text: "text-emerald-400", border: "rgba(34,211,119,0.25)", bg: "rgba(34,211,119,0.06)" },
    active: { dot: "bg-[var(--axiom-accent)]", text: "text-[var(--axiom-accent-hover)]", border: "rgba(109,124,255,0.28)", bg: "rgba(109,124,255,0.06)" },
    warning: { dot: "bg-amber-400", text: "text-amber-400", border: "rgba(255,184,48,0.28)", bg: "rgba(255,184,48,0.06)" },
    danger: { dot: "bg-rose-400", text: "text-rose-400", border: "rgba(255,77,106,0.28)", bg: "rgba(255,77,106,0.06)" },
    neutral: { dot: "bg-[var(--axiom-text-tertiary)]", text: "text-[var(--axiom-text-secondary)]", border: "rgba(240,241,243,0.12)", bg: "rgba(240,241,243,0.03)" },
  };
  const c = map[tone];
  return (
    <div className="flex items-center gap-1.5 rounded-full px-3 py-1 border" style={{ borderColor: c.border, background: c.bg }}>
      {icon ?? <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", c.dot)} />}
      <span className={cn("text-[9px] font-semibold tracking-widest", c.text)}>{label}</span>
    </div>
  );
}

// ── Metric card (glassmorphism) ─────────────────────────────────────────────
export function MetricCard({ kpi, index, className }: { kpi: MetricKpi; index: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 + index * 0.06, ease: "easeOut" }}
      className={cn("relative flex flex-col rounded-2xl p-4 border overflow-hidden min-w-0", className)}
      style={{ borderColor: "rgba(109,124,255,0.12)", background: "linear-gradient(145deg, rgba(109,124,255,0.05) 0%, rgba(168,140,255,0.04) 100%)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)" }}
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3" style={{ background: "linear-gradient(90deg, transparent, rgba(109,124,255,0.6), transparent)" }} />
      <div className="flex items-center justify-between mb-3">
        <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)]">{kpi.label}</span>
        <span className={cn("text-[10px] font-medium tabular-nums", kpi.trend === "down" ? "text-rose-400/90" : "text-emerald-400/90")}>{kpi.delta}</span>
      </div>
      <div className="flex items-end justify-between gap-3">
        <p className="text-2xl font-medium leading-none text-[var(--axiom-text-primary)] tabular-nums truncate">{kpi.value}</p>
        {kpi.series && kpi.series.length > 0 && (
          <div className="w-16 h-9 flex-shrink-0 -mb-1"><Sparkline series={kpi.series} width={64} height={36} /></div>
        )}
      </div>
    </motion.div>
  );
}

// ── Yamako presence mark ────────────────────────────────────────────────────
export function YamakoAvatar({ size = 34 }: { size?: number }) {
  return (
    <div className="flex items-center justify-center rounded-xl flex-shrink-0 relative overflow-hidden" style={{ width: size, height: size, background: `linear-gradient(135deg, ${PERSONAL_TEAL}, ${PERSONAL_CYAN})`, boxShadow: `0 0 20px -2px ${PERSONAL_TEAL}66` }}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
      <svg width={Math.round(size * 0.5)} height={Math.round(size * 0.5)} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="relative">
        <circle cx="12" cy="12" r="3.2" />
        <circle cx="12" cy="12" r="7" opacity="0.5" />
      </svg>
    </div>
  );
}