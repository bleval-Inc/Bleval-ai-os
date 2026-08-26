"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  VALTA_ACCENT,
  VALTA_VIOLET,
  VALTA_GOLD,
  VALTA_SUCCESS,
  VALTA_LOSS,
  VALTA_NEUTRAL,
} from "./types";
import type { EquityPoint, DistributionSlice, MonthResult } from "./valta-data";

// House of Valta charts — hand-built SVG, matching the AXIOM chart discipline.
// No third-party charting dependency; everything animates via framer-motion.

interface BuildPathOpts {
  width: number;
  height: number;
  padX?: number;
  padY?: number;
}

function buildPath(values: number[], { width, height, padX = 4, padY = 10 }: BuildPathOpts) {
  const n = values.length;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const step = n > 1 ? innerW / (n - 1) : 0;

  const pts = values.map((v, i) => {
    const x = padX + i * step;
    const y = padY + innerH - ((v - min) / range) * innerH;
    return { x, y };
  });

  let d = "";
  for (let i = 0; i < pts.length; i++) {
    if (i === 0) {
      d += `M ${pts[i].x} ${pts[i].y}`;
    } else {
      const prev = pts[i - 1];
      const cx = (prev.x + pts[i].x) / 2;
      d += ` C ${cx} ${prev.y}, ${cx} ${pts[i].y}, ${pts[i].x} ${pts[i].y}`;
    }
  }
  return { d, pts, areaStartY: height - padY };
}

function formatMoney(n: number) {
  return `$${n.toLocaleString("en-US")}`;
}

// ── Primary equity / profit-growth chart ────────────────────────────────────
export function EquityChart({ series, height = 260 }: { series: EquityPoint[]; height?: number }) {
  const width = 760;
  const values = series.map((p) => p.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const top = useMemo(() => (Math.ceil(max / 2000) + 1) * 2000, [max]);
  const base = useMemo(() => (Math.floor(min / 2000)) * 2000, [min]);

  const { d, pts } = useMemo(() => buildPath(values, { width, height }), [values, width, height]);

  const gridTicks = useMemo(() => {
    const ticks: number[] = [];
    for (let v = base; v <= top; v += 2000) ticks.push(v);
    return ticks;
  }, [base, top]);

  const yFor = (v: number) => height - ((v - base) / (top - base || 1)) * (height - 20) - 10;

  const area = `${d} L ${pts[pts.length - 1].x} ${height} L ${pts[0].x} ${height} Z`;
  const startY = yFor(series[0].equity);
  const startLine = `M ${pts[0].x} ${startY} L ${pts[0].x} ${yFor(series[0].equity)}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full h-full"
      role="img"
      aria-label="Equity and cumulative profit growth over the last 24 weeks"
    >
      <defs>
        <linearGradient id="valta-equity-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={VALTA_ACCENT} stopOpacity="0.28" />
          <stop offset="60%" stopColor={VALTA_ACCENT} stopOpacity="0.05" />
          <stop offset="100%" stopColor={VALTA_ACCENT} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="valta-equity-line" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={VALTA_ACCENT} />
          <stop offset="70%" stopColor={VALTA_VIOLET} />
          <stop offset="100%" stopColor={VALTA_GOLD} />
        </linearGradient>
      </defs>

      {/* Recessed horizontal gridlines + axis labels */}
      {gridTicks.map((g) => {
        const y = yFor(g);
        return (
          <g key={g}>
            <line x1={0} x2={width} y1={y} y2={y} stroke="rgba(240,241,243,0.05)" strokeWidth="1" />
            <text x={width - 4} y={y - 4} textAnchor="end" fill="rgba(240,241,243,0.3)" fontSize="9" fontWeight="500" fontFamily="var(--axiom-font-mono)">
              ${(g / 1000).toFixed(0)}k
            </text>
          </g>
        );
      })}

      {/* Area fill */}
      <motion.path
        d={area}
        fill="url(#valta-equity-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.9, delay: 0.4 }}
      />
      {/* Baseline start tick */}
      <motion.path
        d={startLine}
        stroke="url(#valta-equity-line)"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
      />
      {/* Main smooth line */}
      <motion.path
        d={d}
        fill="none"
        stroke="url(#valta-equity-line)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
      />
      {/* End point */}
      <motion.circle
        cx={pts[pts.length - 1].x}
        cy={pts[pts.length - 1].y}
        r={4.5}
        fill={VALTA_GOLD}
        style={{ filter: "drop-shadow(0 0 8px rgba(232,198,106,0.8))" }}
        initial={{ r: 0, opacity: 0 }}
        animate={{ r: 4.5, opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.3 }}
      />
      <motion.circle
        cx={pts[pts.length - 1].x}
        cy={pts[pts.length - 1].y}
        r={8}
        fill="none"
        stroke="rgba(232,198,106,0.35)"
        strokeWidth="1"
        initial={{ r: 0, opacity: 0 }}
        animate={{ r: 8, opacity: 1 }}
        transition={{ delay: 1.3, duration: 0.3 }}
      />
    </svg>
  );
}

// ── Profit distribution donut ───────────────────────────────────────────────
const SLICE_COLORS = { win: VALTA_SUCCESS, loss: VALTA_LOSS, breakeven: VALTA_NEUTRAL };

export function DonutChart({ slices, size = 168 }: { slices: DistributionSlice[]; size?: number }) {
  const total = slices.reduce((acc, s) => acc + s.count, 0);
  const stroke = size * 0.13;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  // Each slice's dash/offset depends on the cumulative share before it — derived
  // up front so nothing is mutated during render.
  const segments = slices.map((s, i) => {
    const frac = s.count / total;
    const dash = frac * c;
    const offset = -slices.slice(0, i).reduce((a, x) => a + x.count, 0) / total * c;
    return { s, frac, dash, offset };
  });

  return (
    <div className="flex items-center gap-6">
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(240,241,243,0.05)" strokeWidth={stroke} />
          {segments.map(({ s, dash, offset }) => (
              <motion.circle
                key={s.key}
                cx={size / 2}
                cy={size / 2}
                r={r}
                fill="none"
                stroke={SLICE_COLORS[s.tone]}
                strokeWidth={stroke}
                strokeLinecap="butt"
                strokeDasharray={`${dash} ${c - dash}`}
                strokeDashoffset={offset}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1, strokeDasharray: `${dash} ${c - dash}`, strokeDashoffset: offset }}
                transition={{ duration: 0.8, delay: 0.3 }}
              />
            ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[22px] font-semibold leading-none text-[var(--axiom-text-primary)] tabular-nums">{total}</span>
          <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)] mt-1">Trades</span>
        </div>
      </div>

      <div className="flex flex-col gap-2.5 min-w-0">
        {slices.map((s) => (
          <div key={s.key} className="flex items-center gap-2 min-w-0">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: SLICE_COLORS[s.tone] }} />
            <div className="min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{s.label}</span>
                <span className="text-[10px] text-[var(--axiom-text-tertiary)] tabular-nums">
                  {((s.count / total) * 100).toFixed(1)}%
                </span>
              </div>
              <span className="block text-[11px] text-[var(--axiom-text-secondary)] tabular-nums">
                {s.value === 0 ? "$0" : formatMoney(s.value)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Monthly performance bars ────────────────────────────────────────────────
export function MonthlyBarChart({ series, height = 180 }: { series: MonthResult[]; height?: number }) {
  const width = 440;
  const maxAbs = Math.max(...series.map((s) => Math.max(s.profit, s.loss, Math.abs(s.net))));
  const top = (Math.ceil(maxAbs / 500) + 1) * 500;
  const padX = 28;
  const padY = 14;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const zeroY = padY + innerH; // results anchored at bottom; scale to top
  const slotW = innerW / series.length;
  const barW = Math.min(34, slotW * 0.42);
  const groupW = slotW * 0.8;

  const gridTicks = [top, top / 2, 0];

  const toH = (v: number) => (v / top) * innerH;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" role="img" aria-label="Monthly profit, loss and net performance">
      {gridTicks.map((g) => {
        const y = padY + innerH - toH(g);
        return (
          <g key={g}>
            <line x1={0} x2={width} y1={y} y2={y} stroke="rgba(240,241,243,0.05)" strokeWidth="1" />
            <text x={padX - 6} y={y + 3} textAnchor="end" fill="rgba(240,241,243,0.3)" fontSize="9" fontWeight="500" fontFamily="var(--axiom-font-mono)">
              ${g}
            </text>
          </g>
        );
      })}

      {series.map((s, i) => {
        const cx = padX + slotW * i + slotW / 2;
        const profitH = toH(s.profit);
        const lossH = toH(s.loss);
        const netH = toH(Math.abs(s.net));

        return (
          <g key={s.month}>
            {/* Profit */}
            <motion.rect
              x={cx - barW * 1.5 - 2}
              y={zeroY - profitH}
              width={barW}
              height={profitH}
              rx={2.5}
              fill={VALTA_SUCCESS}
              opacity={0.85}
              initial={{ height: 0, y: zeroY }}
              animate={{ height: profitH, y: zeroY - profitH }}
              transition={{ duration: 0.7, delay: 0.2 + i * 0.08, ease: "easeOut" }}
            />
            {/* Loss */}
            <motion.rect
              x={cx - barW / 2}
              y={zeroY - lossH}
              width={barW}
              height={lossH}
              rx={2.5}
              fill={VALTA_LOSS}
              opacity={0.85}
              initial={{ height: 0, y: zeroY }}
              animate={{ height: lossH, y: zeroY - lossH }}
              transition={{ duration: 0.7, delay: 0.28 + i * 0.08, ease: "easeOut" }}
            />
            {/* Net */}
            <motion.rect
              x={cx + barW / 2 + 2}
              y={zeroY - netH}
              width={barW}
              height={netH}
              rx={2.5}
              fill={s.net >= 0 ? VALTA_ACCENT : VALTA_VIOLET}
              style={{ filter: "drop-shadow(0 0 6px rgba(109,124,255,0.4))" }}
              initial={{ height: 0, y: zeroY }}
              animate={{ height: netH, y: zeroY - netH }}
              transition={{ duration: 0.7, delay: 0.36 + i * 0.08, ease: "easeOut" }}
            />
            <text x={cx + groupW / 2 - 14} y={height - 2} textAnchor="middle" fill="rgba(240,241,243,0.4)" fontSize="9" fontWeight="500">
              {s.month}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── KPI sparkline ───────────────────────────────────────────────────────────
export function Sparkline({ series, height = 36, width = 64 }: { series: number[]; height?: number; width?: number }) {
  const { d, pts } = useMemo(() => buildPath(series, { width, height }), [series, height, width]);
  const lastX = pts[pts.length - 1].x;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-full" aria-hidden>
      <defs>
        <linearGradient id="valta-spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={VALTA_ACCENT} stopOpacity="0.25" />
          <stop offset="100%" stopColor={VALTA_ACCENT} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path
        d={`${d} L ${lastX} ${height} L 0 ${height} Z`}
        fill="url(#valta-spark-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      />
      <motion.path
        d={d}
        fill="none"
        stroke={VALTA_ACCENT}
        strokeWidth="1.75"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </svg>
  );
}

// ── Small horizontal P/L bar (calendar / activity) ──────────────────────────
export function PlBar({ value, max }: { value: number; max?: number }) {
  const cap = max ?? Math.max(Math.abs(value), 100);
  const widthPct = Math.min(100, (Math.abs(value) / cap) * 100);
  const positive = value >= 0;
  return (
    <div className="w-full h-[5px] rounded-full overflow-hidden" style={{ background: "rgba(240,241,243,0.06)" }}>
      <motion.div
        className="h-full rounded-full"
        style={{ background: positive ? VALTA_SUCCESS : VALTA_LOSS, width: 0 }}
        animate={{ width: `${widthPct}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  );
}