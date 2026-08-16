"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import type { Point, BreakdownSlice } from "./bleval-data";

const ACCENT = "#6d7cff";
const VIOLET = "#a88cff";
const CYAN = "#00d4ff";

interface BuildPathOpts {
  width: number;
  height: number;
  padX?: number;
  padY?: number;
}

/** Build a smooth cubic path + point coordinates for an area chart. */
function buildPath(series: number[], { width, height, padX = 4, padY = 8 }: BuildPathOpts) {
  const n = series.length;
  const max = Math.max(...series);
  const min = Math.min(...series);
  const range = max - min || 1;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const step = n > 1 ? innerW / (n - 1) : 0;

  const pts = series.map((v, i) => {
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

interface RevenueAreaChartProps {
  series: Point[];
  height?: number;
}

export function RevenueAreaChart({ series: points, height = 180 }: RevenueAreaChartProps) {
  const width = 640;
  const values = points.map((p) => p.value);
  const { d, pts, areaStartY } = useMemo(
    () => buildPath(values, { width, height }),
    [values, height],
  );
  const areaD = `${d} L ${pts[pts.length - 1].x} ${areaStartY} L ${pts[0].x} ${areaStartY} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full h-full"
      role="img"
      aria-label="Revenue trend over time"
    >
      <defs>
        <linearGradient id="rev-line" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={ACCENT} />
          <stop offset="60%" stopColor={VIOLET} />
          <stop offset="100%" stopColor={CYAN} />
        </linearGradient>
        <linearGradient id="rev-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={ACCENT} stopOpacity="0.35" />
          <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Horizontal gridlines */}
      {[0.25, 0.5, 0.75].map((t) => (
        <line
          key={t}
          x1={0}
          x2={width}
          y1={height * t}
          y2={height * t}
          stroke="rgba(240,241,243,0.06)"
          strokeWidth="1"
        />
      ))}

      <motion.path
        d={areaD}
        fill="url(#rev-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
      />
      <motion.path
        d={d}
        fill="none"
        stroke="url(#rev-line)"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.1, ease: "easeOut" }}
      />

      {/* Animated end dot */}
      <motion.circle
        cx={pts[pts.length - 1].x}
        cy={pts[pts.length - 1].y}
        r={3.5}
        fill={CYAN}
        style={{ filter: "drop-shadow(0 0 6px rgba(0,212,255,0.8))" }}
        initial={{ r: 0, opacity: 0 }}
        animate={{ r: 3.5, opacity: 1 }}
        transition={{ delay: 1.1, duration: 0.3 }}
      />
    </svg>
  );
}

interface SparklineProps {
  series: number[];
  height?: number;
  width?: number;
}

export function Sparkline({ series, height = 36, width = 96 }: SparklineProps) {
  const { d } = useMemo(() => buildPath(series, { width, height }), [series, height, width]);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-full" aria-hidden>
      <defs>
        <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={ACCENT} stopOpacity="0.25" />
          <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="spark-line-grad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={ACCENT} />
          <stop offset="100%" stopColor={CYAN} />
        </linearGradient>
      </defs>
      <motion.path
        d={`${d} L ${width} ${height} L 0 ${height} Z`}
        fill="url(#spark-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      />
      <motion.path
        d={d}
        fill="none"
        stroke="url(#spark-line-grad)"
        strokeWidth="1.75"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </svg>
  );
}

interface DonutChartProps {
  slices: BreakdownSlice[];
  size?: number;
}

export function DonutChart({ slices, size = 150 }: DonutChartProps) {
  const stroke = 16;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const total = slices.reduce((s, x) => s + x.value, 0);
  // Cumulative dash offset per slice so segments sit end-to-end around the ring.
  const offsets = slices.reduce<number[]>((acc, s, i) => {
    acc.push(i === 0 ? 0 : acc[i - 1] - (slices[i - 1].value / total) * c);
    return acc;
  }, []);

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label="Revenue breakdown donut">
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(240,241,243,0.05)" strokeWidth={stroke} />
        {slices.map((s, i) => {
          const dash = (s.value / total) * c;
          return (
            <motion.circle
              key={s.id}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeLinecap="butt"
              strokeDasharray={`${dash} ${c - dash}`}
              strokeDashoffset={offsets[i]}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 + i * 0.15, duration: 0.4 }}
            />
          );
        })}
      </g>
      <text
        x="50%"
        y="47%"
        textAnchor="middle"
        fill="rgba(240,241,243,0.9)"
        fontSize="15"
        fontWeight="500"
      >
        {`$${(total / 1000).toFixed(1)}k`}
      </text>
      <text x="50%" y="58%" textAnchor="middle" fill="rgba(240,241,243,0.35)" fontSize="9" fontWeight="500" letterSpacing="1">
        TOTAL
      </text>
    </svg>
  );
}