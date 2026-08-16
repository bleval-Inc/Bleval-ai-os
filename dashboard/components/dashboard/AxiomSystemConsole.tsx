"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAxiomStore } from "@/lib/store/axiom-store";
import { cn } from "@/lib/utils";
import { axiomData, type MetricPanel } from "./axiom-data";

// AXIOM SYSTEM identity — the machine itself. Restrained indigo/violet so it
// reads as the instrument panel underneath BLEVAL (money), VALTA (trading) and
// PERSONAL (life), not as a competing dashboard.
const identity = "linear-gradient(135deg, #6d7cff 0%, #a88cff 100%)";
const ACCENT = "#6d7cff";

const panelShell = {
  borderColor: "rgba(240,241,243,0.06)",
  background: "rgba(13,16,20,0.4)",
};

function PanelTitle({ title }: { title: string }) {
  return (
    <h4 className="text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)] mb-1.5 flex-shrink-0">
      {title}
    </h4>
  );
}

/* Minimal sparkline — indigo, no axes, animated draw-in. */
function Spark({ series, height = 30 }: { series: number[]; height?: number }) {
  const W = 100;
  const H = height;
  const max = Math.max(...series);
  const min = Math.min(...series);
  const range = max - min || 1;
  const step = (W - 8) / (series.length - 1 || 1);
  const pts = series
    .map((v, i) => `${4 + i * step},${H - 5 - ((v - min) / range) * (H - 10)}`)
    .join(" ");
  const fill = `${pts} ${4 + (series.length - 1) * step},${H} 4,${H}`;
  return (
    <svg viewBox={`-4 -4 ${W + 8} ${H + 8}`} preserveAspectRatio="none" className="w-full h-full" aria-hidden>
      <motion.polygon
        points={fill}
        fill={ACCENT}
        fillOpacity="0.10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      />
      <motion.polyline
        points={pts}
        fill="none"
        stroke={ACCENT}
        strokeOpacity="0.75"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1, ease: "easeOut", delay: 0.15 }}
      />
    </svg>
  );
}

/* Pulsing status dot — emerald for healthy, red when not. */
function StatusDot({ on }: { on: boolean }) {
  return (
    <span className="relative flex w-1.5 h-1.5 flex-shrink-0">
      {on && (
        <span
          className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50 animate-ping"
          style={{ animationDuration: "2.6s" }}
        />
      )}
      <span
        className={cn(
          "relative inline-flex rounded-full w-1.5 h-1.5",
          on ? "bg-emerald-400" : "bg-[var(--axiom-error)]",
        )}
        style={on ? { boxShadow: "0 0 6px rgba(52,211,153,0.7)" } : undefined}
      />
    </span>
  );
}

/* One of the four performance metrics (CPU / Memory / Storage / Network). */
function MetricPanel({ metric, index }: { metric: MetricPanel; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.18 + index * 0.06, ease: "easeOut" }}
      className="rounded-xl border p-2.5 flex flex-col min-w-0 min-h-[74px]"
      style={panelShell}
    >
      <span className="text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)] leading-none">
        {metric.label}
      </span>
      <div className="flex items-baseline gap-0.5 mt-1">
        <span className="text-[20px] leading-none font-semibold text-[var(--axiom-text-primary)] tabular-nums">
          {metric.value}
        </span>
        <span className="text-[10px] font-medium text-[var(--axiom-text-tertiary)]">{metric.unit}</span>
      </div>
      <div className="mt-auto h-[26px]">
        <Spark series={metric.series} />
      </div>
    </motion.div>
  );
}

/* Shared status row: label on the left, signal on the right. */
function StatusRow({
  label,
  right,
  delay,
}: {
  label: string;
  right: React.ReactNode;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay, ease: "easeOut" }}
      className="flex items-center justify-between gap-2 py-1.5 min-w-0"
    >
      <div className="flex items-center gap-2 min-w-0">
        <StatusDot on />
        <span className="text-[12px] text-[var(--axiom-text-secondary)] truncate">{label}</span>
      </div>
      {right}
    </motion.div>
  );
}

/* ---------- CONSOLE SHELL ---------- */
export default function AxiomSystemConsole() {
  const router = useRouter();
  const { setActiveWorkstation } = useAxiomStore();
  const { health, healthMessage, healthSeries, metrics, executives, services, uptime } = axiomData;

  const openWorkstation = () => {
    setActiveWorkstation("axiom");
    router.push("/axiom");
  };

  return (
    <div
      className="relative w-full h-full min-h-0 rounded-3xl overflow-hidden backdrop-blur-xl flex flex-col"
      style={{
        background: `
          radial-gradient(ellipse at top left, rgba(109,124,255,0.08) 0%, transparent 55%),
          radial-gradient(ellipse at bottom right, rgba(168,140,255,0.05) 0%, transparent 50%),
          linear-gradient(150deg, rgba(10,11,16,0.62) 0%, rgba(13,14,20,0.62) 100%)
        `,
        border: "1px solid rgba(109,124,255,0.15)",
        boxShadow: `
          0 8px 40px -12px rgba(109,124,255,0.16),
          inset 0 1px 0 rgba(255,255,255,0.03)
        `,
      }}
    >
      {/* Scanline texture */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(240,241,243,0.6) 2px, rgba(240,241,243,0.6) 4px)",
        }}
      />

      {/* Header */}
      <div className="relative flex items-center justify-between px-5 pt-4 pb-3 border-b border-[rgba(109,124,255,0.12)] z-10 flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-white relative overflow-hidden flex-shrink-0"
            style={{ background: identity, boxShadow: "0 0 24px -4px rgba(109,124,255,0.55)" }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/25 to-transparent" />
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="relative">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          <div className="min-w-0">
            <h3 className="text-base font-semibold tracking-tight text-[var(--axiom-text-primary)] truncate">
              AXIOM SYSTEM
            </h3>
            <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">
              Operating Status
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <div
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md"
            style={{ border: "1px solid rgba(52,211,153,0.18)", background: "rgba(52,211,153,0.05)" }}
          >
            <StatusDot on />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-300">Operational</span>
          </div>

          <motion.button
            onClick={openWorkstation}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-[var(--axiom-text-secondary)] hover:text-[#b8c0ff] transition-colors"
            style={{ border: "1px solid rgba(109,124,255,0.15)", background: "rgba(109,124,255,0.05)" }}
            aria-label="Open AXIOM System workstation"
          >
            <span>Workstation</span>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7 17L17 7M7 7h10v10" />
            </svg>
          </motion.button>
        </div>
      </div>

      {/* Content — scrolls only as a safety net on short viewports */}
      <div className="relative flex-1 min-h-0 overflow-y-auto hide-scrollbar px-5 py-4 z-10">
        <div className="h-full min-h-0 flex flex-col gap-3">
          {/* 1 · Overall system health */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05, ease: "easeOut" }}
            className="rounded-xl border p-3.5 flex items-center gap-4 flex-shrink-0"
            style={panelShell}
          >
            <div className="min-w-0">
              <PanelTitle title="System Health" />
              <div className="flex items-baseline gap-1.5">
                <span className="text-[36px] leading-none font-semibold text-[var(--axiom-text-primary)] tabular-nums">
                  {health}
                </span>
                <span className="text-[14px] font-semibold text-emerald-400">%</span>
              </div>
              <p className="text-[11px] font-medium text-[var(--axiom-text-secondary)] mt-1 truncate">
                {healthMessage}
              </p>
            </div>
            <div className="ml-auto w-28 h-14 flex-shrink-0">
              <Spark series={healthSeries} height={40} />
            </div>
          </motion.div>

          {/* 2 · Performance metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 flex-shrink-0">
            {metrics.map((m, i) => (
              <MetricPanel key={m.key} metric={m} index={i} />
            ))}
          </div>

          {/* 3 · Executives + 4 · Core services */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <motion.section
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="rounded-xl border p-3.5 flex flex-col min-h-0"
              style={panelShell}
            >
              <PanelTitle title="Executives" />
              <div className="flex-1 min-h-0 flex flex-col">
                {executives.map((e, i) => (
                  <StatusRow
                    key={e.key}
                    label={e.name}
                    delay={0.34 + i * 0.05}
                    right={
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-300/90 flex-shrink-0">
                        Online
                      </span>
                    }
                  />
                ))}
              </div>
            </motion.section>

            <motion.section
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.35 }}
              className="rounded-xl border p-3.5 flex flex-col min-h-0"
              style={panelShell}
            >
              <PanelTitle title="Core Services" />
              <div className="flex-1 min-h-0 flex flex-col">
                {services.map((s, i) => (
                  <StatusRow
                    key={s.key}
                    label={s.label}
                    delay={0.39 + i * 0.05}
                    right={
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-300/90 flex-shrink-0">
                        {s.status}
                      </span>
                    }
                  />
                ))}
              </div>
            </motion.section>
          </div>

          {/* 5 · Uptime */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.45 }}
            className="rounded-xl border px-3.5 py-2 flex items-center justify-between flex-shrink-0"
            style={panelShell}
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)]">
              Uptime
            </span>
            <span className="text-[12px] font-semibold text-[var(--axiom-text-primary)] tabular-nums">
              {uptime.days}d {uptime.hours}h {uptime.minutes}m
            </span>
          </motion.div>
        </div>
      </div>
    </div>
  );
}