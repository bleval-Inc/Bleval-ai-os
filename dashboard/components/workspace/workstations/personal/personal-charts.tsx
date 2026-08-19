"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { PERSONAL_ACCENT, PERSONAL_VIOLET, PERSONAL_SUCCESS } from "./types";
import type { QuickStat, TrendPoint } from "./personal-data";

// Personal workstation chart primitives — hand-built SVG, no third-party dep.

function buildPath(values: number[], width: number, height: number) {
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const padX = 4;
  const padY = 8;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const step = innerW / (values.length - 1 || 1);
  const pts = values.map((v, i) => ({
    x: padX + i * step,
    y: padY + innerH - ((v - min) / range) * innerH,
  }));
  let d = "";
  for (let i = 0; i < pts.length; i++) {
    if (i === 0) d += `M ${pts[i].x} ${pts[i].y}`;
    else {
      const p = pts[i - 1];
      const cx = (p.x + pts[i].x) / 2;
      d += ` C ${cx} ${p.y}, ${cx} ${pts[i].y}, ${pts[i].x} ${pts[i].y}`;
    }
  }
  return { d, pts };
}

// ── Circular completion ring ────────────────────────────────────────────────
export function ProgressRing({ value, size = 72, label, color }: { value: number; size?: number; label?: string; color?: string }) {
  const stroke = size * 0.11;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = (value / 100) * c;
  const accent = color ?? PERSONAL_ACCENT;
  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(240,241,243,0.07)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={accent}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          initial={{ strokeDasharray: `0 ${c}` }}
          animate={{ strokeDasharray: `${dash} ${c - dash}` }}
          transition={{ duration: 0.9, ease: "easeOut" }}
          style={{ filter: `drop-shadow(0 0 6px ${accent}55)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[15px] font-semibold text-[var(--axiom-text-primary)] leading-none tabular-nums">{label ?? `${Math.round(value)}%`}</span>
      </div>
    </div>
  );
}

// ── Sparkline (trend) ───────────────────────────────────────────────────────
export function Sparkline({ series, width = 96, height = 36 }: { series: number[]; width?: number; height?: number }) {
  const { d, pts } = useMemo(() => buildPath(series, width, height), [series, width, height]);
  const lastX = pts[pts.length - 1].x;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-full" aria-hidden>
      <defs>
        <linearGradient id="personal-spark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={PERSONAL_ACCENT} stopOpacity="0.25" />
          <stop offset="100%" stopColor={PERSONAL_ACCENT} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path d={`${d} L ${lastX} ${height} L 0 ${height} Z`} fill="url(#personal-spark)" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }} />
      <motion.path d={d} fill="none" stroke={PERSONAL_ACCENT} strokeWidth="1.75" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8, ease: "easeOut" }} />
    </svg>
  );
}

// ── Bar chart (week / month trend) ──────────────────────────────────────────
export function TrendBars({ points, height = 120, color }: { points: TrendPoint[]; height?: number; color?: string }) {
  const accent = color ?? PERSONAL_ACCENT;
  return (
    <div className="flex items-end gap-2" style={{ height }}>
      {points.map((p, i) => (
        <div key={p.label} className="flex-1 flex flex-col items-center justify-end gap-1.5 min-w-0">
          <motion.div
            className="w-full rounded-t-[4px]"
            style={{ background: `linear-gradient(180deg, ${accent}, transparent)`, backgroundColor: accent }}
            initial={{ height: 0 }}
            animate={{ height: `${p.value}%` }}
            transition={{ duration: 0.6, delay: 0.1 + i * 0.05, ease: "easeOut" }}
          />
          <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{p.label}</span>
        </div>
      ))}
    </div>
  );
}

// ── Habit weekly consistency dots ───────────────────────────────────────────
export function ConsistencyDots({ weekly, small = false }: { weekly: boolean[]; small?: boolean }) {
  return (
    <div className="flex items-center gap-1">
      {weekly.map((on, i) => (
        <span
          key={i}
          className={cn("rounded-[3px]", small ? "w-2 h-2" : "w-2.5 h-2.5")}
          style={{ background: on ? PERSONAL_SUCCESS : "rgba(240,241,243,0.12)" }}
        />
      ))}
    </div>
  );
}

// ── Vertical progress meter (habits) ────────────────────────────────────────
export function ProgressMeter({ value, color }: { value: number; color?: string }) {
  const accent = color ?? PERSONAL_ACCENT;
  return (
    <div className="w-full h-[6px] rounded-full overflow-hidden" style={{ background: "rgba(240,241,243,0.07)" }}>
      <motion.div className="h-full rounded-full" style={{ background: accent, width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 0.7, ease: "easeOut" }} />
    </div>
  );
}

// ── Quick status bar (dashboard) ────────────────────────────────────────────
export function QuickStatusBar({ stat }: { stat: QuickStat }) {
  return (
    <div className="flex items-center gap-3 min-w-0">
      <span className="w-16 flex-shrink-0 text-[11px] font-medium text-[var(--axiom-text-secondary)]">{stat.label}</span>
      <div className="flex-1 min-w-0">
        <ProgressMeter value={stat.value} color={stat.value >= 80 ? PERSONAL_SUCCESS : stat.value >= 50 ? PERSONAL_ACCENT : PERSONAL_VIOLET} />
      </div>
      <span className="w-10 text-right text-[11px] font-semibold text-[var(--axiom-text-primary)] tabular-nums">{stat.display}</span>
    </div>
  );
}