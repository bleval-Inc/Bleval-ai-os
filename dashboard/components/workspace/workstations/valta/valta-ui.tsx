"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  VALTA_GRADIENT,
  VALTA_VIOLET,
  VALTA_GOLD,
  VALTA_CYAN,
  VALTA_SUCCESS,
  VALTA_LOSS,
  VALTA_NEUTRAL,
  type BaseIcon,
  type MetricKpi,
  type ResultTone,
  type StatusTone,
} from "./types";
import { Sparkline } from "./valta-charts";

// ── Glyphs (inline SVG, thin 1.6 stroke — matches AXIOM icon language) ──────
export function Glyph({ name, size = 16 }: { name: BaseIcon; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "dashboard":
      return <svg {...common}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>;
    case "calendar":
      return <svg {...common}><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4" /><path d="M8 2v4" /><path d="M3 10h18" /><path d="M8 15h3M8 18h2M14 15h3M14 18h2" /></svg>;
    case "journal":
      return <svg {...common}><path d="M6 3h9a4 4 0 0 1 4 4v14l-2-1.33L15 21l-2-1.33L11 21l-2-1.33L7 21l-2-1.33L4 21V7a4 4 0 0 1 4-4z" /><path d="M7 7h6M7 11h9M7 15h9M7 19h2" /></svg>;
    case "reports":
      return <svg {...common}><path d="M3 3v18h18" /><path d="M7 15l3.5-3 2.5 2 5-6" /><path d="M7 9h2M7 12h1" /></svg>;
  }
}

// ── Surfaces ────────────────────────────────────────────────────────────────
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
    <div
      className="flex items-center justify-center rounded-xl text-white flex-shrink-0 relative overflow-hidden"
      style={{ width: size, height: size, background: VALTA_GRADIENT, boxShadow: "0 0 24px -4px rgba(109,124,255,0.5)" }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
      <svg width={Math.round(size * 0.52)} height={Math.round(size * 0.52)} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="relative">
        <path d="M12 12l9-5-9-5-9 5 9 5z" />
        <path d="M3 17l9 5 9-5" />
        <path d="M3 12l9 5 9-5" />
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

export function StatusChip({ label, tone }: { label: string; tone: StatusTone }) {
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
      <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", c.dot)} />
      <span className={cn("text-[9px] font-semibold tracking-widest", c.text)}>{label}</span>
    </div>
  );
}

// ── Trend helpers ───────────────────────────────────────────────────────────
export function TrendArrow({ trend }: { trend: "up" | "down" | "flat" }) {
  if (trend === "flat") return <span className="text-[var(--axiom-text-tertiary)]">—</span>;
  const up = trend === "up";
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={up ? "text-emerald-400/90" : "text-rose-400/90"}>
      {up ? <path d="M6 18L18 6M9 6h9v9" /> : <path d="M6 6l12 12M15 18h3v-3" />}
    </svg>
  );
}

export function PlText({ value, className }: { value: number; className?: string }) {
  const positive = value >= 0;
  return (
    <span className={cn("tabular-nums", positive ? "text-emerald-400/90" : "text-rose-400/90", className)}>
      {positive ? "+" : ""}${Math.abs(value).toLocaleString("en-US")}
    </span>
  );
}

export function ResolutionDot({ tone, className }: { tone: ResultTone; className?: string }) {
  const color = tone === "win" ? VALTA_SUCCESS : tone === "loss" ? VALTA_LOSS : VALTA_NEUTRAL;
  return <span className={cn("inline-block w-1.5 h-1.5 rounded-full flex-shrink-0", className)} style={{ background: color }} />;
}

// ── Metric card (glassmorphism) ─────────────────────────────────────────────
export function MetricCard({ kpi, index, className }: { kpi: MetricKpi; index: number; className?: string }) {
  const hasSpark = !!kpi.series && kpi.series.length > 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 + index * 0.06, ease: "easeOut" }}
      className={cn("relative flex flex-col rounded-2xl p-4 border overflow-hidden min-w-0", className)}
      style={{
        borderColor: "rgba(109,124,255,0.12)",
        background: "linear-gradient(145deg, rgba(109,124,255,0.05) 0%, rgba(168,140,255,0.04) 100%)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)",
      }}
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3" style={{ background: "linear-gradient(90deg, transparent, rgba(109,124,255,0.6), transparent)" }} />
      <div className="flex items-center justify-between mb-3">
        <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)]">{kpi.label}</span>
        {kpi.delta && <TrendArrow trend={kpi.trend ?? "flat"} />}
      </div>
      <div className={cn("flex items-end justify-between gap-3", hasSpark && "min-h-[36px]")}>
        <p className="text-2xl font-medium leading-none text-[var(--axiom-text-primary)] tabular-nums truncate">{kpi.value}</p>
        {hasSpark && (
          <div className="w-16 h-9 flex-shrink-0 -mb-1">
            <Sparkline series={kpi.series!} width={64} height={36} />
          </div>
        )}
      </div>
      {kpi.delta && <span className="mt-2 text-[10px] font-medium text-[var(--axiom-text-secondary)]/80">{kpi.delta}</span>}
    </motion.div>
  );
}

// ── Instrument asset chip (gold distinct flavor) ────────────────────────────
export function AssetChip({ label }: { label: string }) {
  const isGold = label.toUpperCase().includes("XAU") || label === "Gold";
  const color = isGold ? VALTA_GOLD : VALTA_CYAN;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold tracking-wide"
      style={{ color, background: `${color}14`, border: `1px solid ${color}33` }}
    >
      <span className="w-1 h-1 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}

// ── Authority note (analysis-only boundary) ─────────────────────────────────
export function AuthorityNote({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className="flex items-center gap-2.5 rounded-xl border px-3.5 py-2.5"
      style={{ borderColor: "rgba(168,140,255,0.16)", background: "rgba(168,140,255,0.05)" }}
    >
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={VALTA_VIOLET} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
        <path d="M12 3l2.5 5.1L20 9l-4 3.9.9 5.6L12 15.9l-4.9 2.6.9-5.6L4 9l5.5-.9z" />
      </svg>
      {compact ? (
        <span className="text-[10px] leading-snug text-[var(--axiom-text-secondary)]">VALTA PRIME · ANALYSIS ONLY — cannot execute trades</span>
      ) : (
        <span className="text-[11px] leading-snug text-[var(--axiom-text-secondary)]">
          Valta Prime analyses, monitors, researches, prepares, challenges, notifies and coaches. It cannot execute, modify or close trades.
        </span>
      )}
    </div>
  );
}