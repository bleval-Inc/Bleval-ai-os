"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { BLEVAL_ACCENT, BLEVAL_VIOLET, BLEVAL_CYAN } from "./types";
import type { PerformancePoint } from "./bleval-ws-data";

// Recessed gridlines + thin marks, per the AXIOM chart discipline. No dual axis —
// revenue and net profit share one Rand scale and a single legend carries identity.

interface BuildPathOpts {
  width: number;
  height: number;
  padX?: number;
  padY?: number;
}

function buildPath(values: number[], { width, height, padX = 4, padY = 8 }: BuildPathOpts) {
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

interface PerformanceChartProps {
  series: PerformancePoint[];
  height?: number;
}

export function PerformanceChart({ series, height = 220 }: PerformanceChartProps) {
  const width = 720;
  const revenue = series.map((p) => p.revenue);
  const profit = series.map((p) => p.profit);
  const all = [...revenue, ...profit];
  const maxAll = Math.max(...all);
  const top = useMemo(() => (Math.ceil(maxAll / 20) + 1) * 20, [maxAll]);

  const rev = useMemo(() => buildPath(revenue, { width, height }), [revenue, height]);
  const prof = useMemo(() => buildPath(profit, { width, height }), [profit, height]);

  const gridLabels = [top, top * 0.5, 0];

  const areaFor = (d: string, lastX: number, firstX: number) =>
    `${d} L ${lastX} ${height} L ${firstX} ${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full h-full"
      role="img"
      aria-label="Revenue and net profit trend over the last eight months"
    >
      <defs>
        <linearGradient id="ws-rev-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={BLEVAL_ACCENT} stopOpacity="0.28" />
          <stop offset="100%" stopColor={BLEVAL_ACCENT} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="ws-pro-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={BLEVAL_VIOLET} stopOpacity="0.18" />
          <stop offset="100%" stopColor={BLEVAL_VIOLET} stopOpacity="0" />
        </linearGradient>
      </defs>

      {gridLabels.map((g) => {
        // Map grid tick value to its y (proportional to the chart's min/max).
        const min = 0;
        const rangeH = top - min || 1;
        const y = height - ((g - min) / rangeH) * (height - 16) - 8;
        return (
          <g key={g}>
            <line x1={0} x2={width} y1={y} y2={y} stroke="rgba(240,241,243,0.05)" strokeWidth="1" />
            <text x={width} y={y - 3} textAnchor="end" fill="rgba(240,241,243,0.3)" fontSize="9" fontWeight="500">
              {g > 0 ? `R${g}k` : "R0"}
            </text>
          </g>
        );
      })}

      {/* Net profit underlay */}
      <motion.path
        d={areaFor(prof.d, prof.pts[prof.pts.length - 1].x, prof.pts[0].x)}
        fill="url(#ws-pro-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
      />
      <motion.path
        d={prof.d}
        fill="none"
        stroke={BLEVAL_VIOLET}
        strokeWidth="2"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.1, ease: "easeOut" }}
      />

      {/* Revenue foreground */}
      <motion.path
        d={areaFor(rev.d, rev.pts[rev.pts.length - 1].x, rev.pts[0].x)}
        fill="url(#ws-rev-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.6 }}
      />
      <motion.path
        d={rev.d}
        fill="none"
        stroke={BLEVAL_ACCENT}
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
      />

      {/* End caps */}
      <motion.circle
        cx={prof.pts[prof.pts.length - 1].x}
        cy={prof.pts[prof.pts.length - 1].y}
        r={3.5}
        fill={BLEVAL_VIOLET}
        initial={{ r: 0, opacity: 0 }}
        animate={{ r: 3.5, opacity: 1 }}
        transition={{ delay: 1.1, duration: 0.3 }}
      />
      <motion.circle
        cx={rev.pts[rev.pts.length - 1].x}
        cy={rev.pts[rev.pts.length - 1].y}
        r={4}
        fill={BLEVAL_CYAN}
        style={{ filter: "drop-shadow(0 0 6px rgba(0,212,255,0.7))" }}
        initial={{ r: 0, opacity: 0 }}
        animate={{ r: 4, opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.3 }}
      />
    </svg>
  );
}

export function WSSparkline({ series, height = 36, width = 96 }: { series: number[]; height?: number; width?: number }) {
  const { d, pts } = useMemo(() => buildPath(series, { width, height }), [series, height, width]);
  const lastX = pts[pts.length - 1].x;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-full" aria-hidden>
      <defs>
        <linearGradient id="ws-spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={BLEVAL_ACCENT} stopOpacity="0.25" />
          <stop offset="100%" stopColor={BLEVAL_ACCENT} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path
        d={`${d} L ${lastX} ${height} L 0 ${height} Z`}
        fill="url(#ws-spark-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      />
      <motion.path
        d={d}
        fill="none"
        stroke={BLEVAL_ACCENT}
        strokeWidth="1.75"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </svg>
  );
}