"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { BaseIcon } from "./types";
import { SETTING_ACCENT, SETTING_VIOLET } from "./types";

// ── Glyphs (thin 1.6 stroke, matches the AXIOM icon language) ───────────────
export function Glyph({ name, size = 16 }: { name: BaseIcon; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "system":
      return <svg {...common}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3" /></svg>;
    case "ai":
      return <svg {...common}><path d="M12 3l1.7 4.4L18 9l-4.3 1.6L12 15l-1.7-4.4L6 9l4.3-1.6z" /><path d="M18.5 15l.9 2.2 2.2.9-2.2.9-.9 2.2-.9-2.2-2.2-.9 2.2-.9z" /></svg>;
    case "executives":
      return <svg {...common}><circle cx="12" cy="7" r="3.2" /><path d="M5 20c0-3.6 3-6 7-6s7 2.4 7 6" /></svg>;
    case "founder":
      return <svg {...common}><path d="M12 3l7 3v5c0 4.6-3 7.6-7 9-4-1.4-7-4.4-7-9V6z" /></svg>;
    case "voice":
      return <svg {...common}><rect x="9" y="2" width="6" height="12" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v4M9 22h6" /></svg>;
    case "notifications":
      return <svg {...common}><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6" /><path d="M10 20a2 2 0 0 0 4 0" /></svg>;
    case "integrations":
      return <svg {...common}><path d="M9 2v5M12 2v5M15 2v5M7 7h10v3a5 5 0 0 1-10 0z" /><path d="M12 15v8" /></svg>;
    case "security":
      return <svg {...common}><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>;
    case "appearance":
      return <svg {...common}><path d="M4 17h16M4 7h16" /><circle cx="15" cy="7" r="2.4" /><circle cx="9" cy="17" r="2.4" /></svg>;
  }
}

// ── Surfaces ────────────────────────────────────────────────────────────────
export function SettingsPanel({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-2xl border backdrop-blur-xl overflow-hidden min-w-0", className)} style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(15,18,24,0.42)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)" }}>
      {children}
    </div>
  );
}

export function GroupTitle({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex items-center gap-2.5 h-11 px-4 border-b" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
      <span className="h-3.5 w-0.5 rounded-full" style={{ background: "linear-gradient(180deg,var(--axiom-accent),rgba(109,124,255,0))" }} />
      <h4 className="text-[10px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-secondary)]">{title}</h4>
      {hint && <span className="ml-auto text-[9px] text-[var(--axiom-text-tertiary)]/70">{hint}</span>}
    </div>
  );
}

export function ViewHeader({ title, description, right }: { title: string; description: string; right?: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">
          <span>SETTINGS</span><span className="opacity-40">·</span><span style={{ color: SETTING_ACCENT }}>{title}</span>
        </div>
        <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">{title}</h1>
        <p className="text-[12px] text-[var(--axiom-text-secondary)] mt-0.5">{description}</p>
      </div>
      {right}
    </motion.div>
  );
}

// ── Status pill ──────────────────────────────────────────────────────────────
const PILL_MAP = {
  healthy: { text: "text-emerald-400", border: "rgba(34,211,119,0.25)", bg: "rgba(34,211,119,0.06)" },
  active: { text: "text-[var(--axiom-accent-hover)]", border: "rgba(109,124,255,0.28)", bg: "rgba(109,124,255,0.06)" },
  warning: { text: "text-amber-400", border: "rgba(255,184,48,0.28)", bg: "rgba(255,184,48,0.06)" },
  danger: { text: "text-rose-400", border: "rgba(255,77,106,0.28)", bg: "rgba(255,77,106,0.06)" },
  neutral: { text: "text-[var(--axiom-text-secondary)]", border: "rgba(240,241,243,0.12)", bg: "rgba(240,241,243,0.03)" },
} as const;

export function StatusPill({ label, tone = "neutral", dot = true }: { label: string; tone?: keyof typeof PILL_MAP; dot?: boolean }) {
  const c = PILL_MAP[tone];
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 border text-[9px] font-semibold tracking-wide whitespace-nowrap" style={{ color: c.text, borderColor: c.border, background: c.bg }}>
      {dot && <span className={cn("w-1 h-1 rounded-full", tone === "active" ? "animate-pulse bg-[var(--axiom-accent)]" : tone === "healthy" ? "bg-emerald-400" : tone === "warning" ? "bg-amber-400" : tone === "danger" ? "bg-rose-400" : "bg-[var(--axiom-text-tertiary)]")} />}
      {label}
    </span>
  );
}

// ── Setting row ──────────────────────────────────────────────────────────────
export function Row({ label, desc, right, hint }: { label: string; desc?: string; right?: React.ReactNode; hint?: string }) {
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[12px] text-[var(--axiom-text-primary)]">{label}</span>
          {hint && <span className="text-[9px] text-[var(--axiom-text-tertiary)]/60">{hint}</span>}
        </div>
        {desc && <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">{desc}</p>}
      </div>
      {right && <div className="flex items-center gap-3 flex-shrink-0 min-w-0 justify-end">{right}</div>}
    </div>
  );
}

export function Value({ children, mono = false }: { children: React.ReactNode; mono?: boolean }) {
  return <span className={cn("text-[12px] font-medium text-[var(--axiom-text-primary)] text-right truncate", mono && "font-mono tabular-nums")}>{children}</span>;
}

// ── Interactive controls (local state only — no backend) ─────────────────────
export function Toggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      aria-pressed={on}
      className="relative w-9 h-[22px] rounded-full border transition-colors flex-shrink-0"
      style={{ background: on ? "linear-gradient(135deg,#6d7cff,#a88cff)" : "rgba(240,241,243,0.08)", borderColor: on ? "rgba(109,124,255,0.6)" : "rgba(240,241,243,0.12)", boxShadow: on ? `0 0 12px -2px rgba(109,124,255,0.6)` : "none" }}
    >
      <span className={cn("absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white transition-all", on ? "left-[18px]" : "left-[3px] opacity-70")} />
    </button>
  );
}

export function Segmented<T extends string>({ options, value, onValue }: { options: readonly T[]; value: T; onValue: (v: T) => void }) {
  return (
    <div className="flex items-center rounded-lg border p-0.5" style={{ borderColor: "rgba(240,241,243,0.1)", background: "rgba(10,12,16,0.4)" }}>
      {options.map((o) => (
        <button key={o} onClick={() => onValue(o)} className={cn("rounded-md px-2.5 py-1 text-[10px] font-semibold transition-colors", value === o ? "text-white" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)]")} style={value === o ? { background: "linear-gradient(135deg,#6d7cff,#a88cff)" } : {}}>
          {o}
        </button>
      ))}
    </div>
  );
}

export function Meter({ value, color = SETTING_ACCENT }: { value: number; color?: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-24 h-1 rounded-full bg-[rgba(240,241,243,0.08)] overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, Math.max(0, value))}%` }} transition={{ duration: 0.8, ease: "easeOut" }} className="h-full rounded-full" style={{ background: color }} />
      </div>
      <span className="w-9 text-right text-[11px] tabular-nums text-[var(--axiom-text-secondary)]">{value}%</span>
    </div>
  );
}

// ── Brand emblem (settings gear) ─────────────────────────────────────────────
export function Emblem({ size = 36 }: { size?: number }) {
  const s = Math.round(size * 0.5);
  return (
    <div className="flex items-center justify-center rounded-xl text-white flex-shrink-0 relative overflow-hidden" style={{ width: size, height: size, background: `linear-gradient(135deg,${SETTING_ACCENT},${SETTING_VIOLET})`, boxShadow: "0 0 22px -4px rgba(109,124,255,0.55)" }}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
      <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="relative">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 0 1-4 0v-.09a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.55-1H3a2 2 0 0 1 0-4h.09a1.7 1.7 0 0 0 1.55-1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34h.09a1.7 1.7 0 0 0 1-1.55V3a2 2 0 0 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87v.09a1.7 1.7 0 0 0 1.55 1H21a2 2 0 0 1 0 4h-.09a1.7 1.7 0 0 0-1.55 1z" />
      </svg>
    </div>
  );
}