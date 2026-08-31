"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import type { ValtaPoint } from "./valta-data";

// House of Valta accent palette — refined gold/amber, stays inside the AXIOM
// dark-glass system while reading as a distinct trading environment.
const GOLD = "#ffcf5c";
const AMBER = "#ff9a3c";

interface Pt {
  x: number;
  y: number;
}

/** Build a smooth cubic path + point coordinates for a numeric series. */
function buildSmooth(
  series: number[],
  W: number,
  H: number,
  padX: number,
  padY: number,
  padBottom: number,
): { d: string; pts: Pt[]; min: number; max: number } {
  // Handle empty array
  if (series.length === 0) {
    return { d: "", pts: [], min: 0, max: 0 };
  }
  const n = series.length;
  const max = Math.max(...series);
  const min = Math.min(...series);
  const range = max - min || 1;
  const innerW = W - padX * 2;
  const innerH = H - padY - padBottom;
  const step = n > 1 ? innerW / (n - 1) : 0;

  const pts: Pt[] = series.map((v, i) => ({
    x: padX + i * step,
    y: padY + innerH - ((v - min) / range) * innerH,
  }));

  let d = "";
  for (let i = 0; i < pts.length; i++) {
    if (i === 0) {
      d += `M ${pts[i].x} ${pts[i].y}`;
    } else {
      const p = pts[i - 1];
      const c = pts[i];
      const cx = (p.x + c.x) / 2;
      d += ` C ${cx} ${p.y}, ${cx} ${c.y}, ${c.x} ${c.y}`;
    }
  }
  return { d, pts, min, max };
}

const currency = (v: number) => `$${Math.round(v).toLocaleString()}`;

interface EquityChartProps {
  series: ValtaPoint[];
  height?: number;
}

/**
 * Large animated equity/area chart with hover crosshair + tooltip.
 * Width is measured from its container (ResizeObserver) so tooltip text stays
 * crisp and the chart always fills its responsive parent.
 */
export function EquityChart({ series, height = 220 }: EquityChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [active, setActive] = useState<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect?.width;
      if (w > 0) setWidth(w);
    });
    ro.observe(el);
    setWidth(el.clientWidth);
    return () => ro.disconnect();
  }, []);

  const padX = 14;
  const padY = 20;
  const padBottom = 24;
  const W = width;
  const H = height;
  const values = series.map((p) => p.value);

  const { d, pts, min, max } = useMemo(
    () => buildSmooth(values, W, H, padX, padY, padBottom),
    // Rebuild only when W changes; values are a stable placeholder array.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [W, H, series],
  );

  if (W < 40) {
    return <div ref={wrapRef} style={{ height }} className="w-full" aria-hidden />;
  }

  const areaD = `${d} L ${pts[pts.length - 1].x} ${H - padBottom} L ${pts[0].x} ${H - padBottom} Z`;
  const plotTop = padY;
  const plotBottom = H - padBottom;
  const midIdx = Math.floor(pts.length / 2);

  const handleMove = (e: React.MouseEvent<SVGRectElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    let best = 0;
    let bd = Infinity;
    pts.forEach((p, i) => {
      const dist = Math.abs(p.x - x);
      if (dist < bd) {
        bd = dist;
        best = i;
      }
    });
    setActive(best);
  };

  const tip =
    active !== null
      ? {
          label: series[active].label,
          value: currency(series[active].value),
          x: pts[active].x,
          y: pts[active].y,
        }
      : null;

  // Clamp tooltip horizontally so it never escapes the drawing box.
  const tipW = 86;
  const tipX = tip ? Math.min(Math.max(tip.x + 12, 4), W - tipW - 4) : 0;

  return (
    <div ref={wrapRef} className="relative" style={{ height }}>
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Equity curve over time"
        className="block"
      >
        <defs>
          <linearGradient id="vlt-line" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={GOLD} />
            <stop offset="100%" stopColor={AMBER} />
          </linearGradient>
          <linearGradient id="vlt-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={GOLD} stopOpacity="0.32" />
            <stop offset="100%" stopColor={GOLD} stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Horizontal gridlines + y labels */}
        {[0, 0.5, 1].map((t, i) => {
          const y = plotTop + (plotBottom - plotTop) * t;
          const label = currency(i === 0 ? max : i === 2 ? min : (max + min) / 2);
          return (
            <g key={t}>
              <line x1={padX} x2={W - padX} y1={y} y2={y} stroke="rgba(240,241,243,0.06)" strokeWidth="1" />
              <text x={W - padX} y={y + 3} textAnchor="end" fill="rgba(240,241,243,0.32)" fontSize="9" fontWeight="500">
                {label}
              </text>
            </g>
          );
        })}

        {/* X labels — first, middle, last */}
        {[0, midIdx, pts.length - 1].map((i) => (
          <text key={i} x={pts[i].x} y={H - 6} textAnchor="middle" fill="rgba(240,241,243,0.3)" fontSize="9" fontWeight="500">
            {series[i].label}
          </text>
        ))}

        {/* Fill + animated line */}
        <motion.path d={areaD} fill="url(#vlt-fill)" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.6 }} />
        <motion.path
          d={d}
          fill="none"
          stroke="url(#vlt-line)"
          strokeWidth="2.25"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.3, ease: "easeOut" }}
        />

        {/* Hover crosshair */}
        {tip && (
          <g>
            <line x1={tip.x} x2={tip.x} y1={plotTop} y2={plotBottom} stroke="rgba(255,207,92,0.35)" strokeWidth="1" strokeDasharray="3 3" />
            <circle cx={tip.x} cy={tip.y} r={7} fill={GOLD} opacity={0.18} />
            <circle cx={tip.x} cy={tip.y} r={3.5} fill={GOLD} style={{ filter: "drop-shadow(0 0 6px rgba(255,207,92,0.85))" }} />
          </g>
        )}

        {/* Hover hit area (nearest-point detection) */}
        <rect
          x={padX}
          y={plotTop}
          width={W - padX * 2}
          height={plotBottom - plotTop}
          fill="transparent"
          onMouseMove={handleMove}
          onMouseLeave={() => setActive(null)}
        />
      </svg>

      {/* Tooltip — HTML so text stays crisp */}
      {tip && (
        <div
          className="absolute pointer-events-none px-2.5 py-1.5 rounded-lg"
          style={{
            left: tipX,
            top: Math.max(0, tip.y - 40),
            background: "rgba(12,15,20,0.92)",
            border: "1px solid rgba(255,207,92,0.22)",
            boxShadow: "0 8px 24px -6px rgba(0,0,0,0.6)",
          }}
        >
          <p className="text-[9px] uppercase tracking-wide text-[var(--axiom-text-tertiary)]">{tip.label}</p>
          <p className="text-[12px] font-semibold tabular-nums text-[#ffcf5c]">{tip.value}</p>
        </div>
      )}
    </div>
  );
}

interface SparklineProps {
  series: number[];
  height?: number;
  width?: number;
}

export function Sparkline({ series, height = 36, width = 96 }: SparklineProps) {
  const { d } = useMemo(() => buildSmooth(series, width, height, 3, 5, 5), [series, width, height]);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-full" aria-hidden>
      <defs>
        <linearGradient id="vlt-spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={GOLD} stopOpacity="0.22" />
          <stop offset="100%" stopColor={GOLD} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="vlt-spark-line" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={GOLD} />
          <stop offset="100%" stopColor={AMBER} />
        </linearGradient>
      </defs>
      <motion.path
        d={`${d} L ${width} ${height} L 0 ${height} Z`}
        fill="url(#vlt-spark-fill)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      />
      <motion.path
        d={d}
        fill="none"
        stroke="url(#vlt-spark-line)"
        strokeWidth="1.75"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.9, ease: "easeOut" }}
      />
    </svg>
  );
}