"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAxiomStore } from "@/lib/store/axiom-store";
import { cn } from "@/lib/utils";
import { valtaData, type ValtaKPI, type Trade } from "./valta-data";
import { EquityChart, Sparkline } from "./valta-charts";

// House of Valta identity — refined gold. It sits inside the AXIOM dark-glass
// system but reads as a distinctly different (trading) environment.
const identity = "linear-gradient(135deg, #ffcf5c 0%, #ff9a3c 100%)";

const INSTRUMENT_HUE: Record<Trade["instrument"], string> = {
  GOLD: "linear-gradient(135deg, rgba(255,207,92,0.16), rgba(255,154,60,0.10))",
  US30: "linear-gradient(135deg, rgba(77,163,255,0.16), rgba(109,124,255,0.10))",
};
const INSTRUMENT_TEXT: Record<Trade["instrument"], string> = {
  GOLD: "text-[#ffcf5c]",
  US30: "text-[#4da3ff]",
};

function PanelTitle({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h4 className="text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)]">
        {title}
      </h4>
      {hint && (
        <span className="text-[10px] font-medium text-[var(--axiom-text-tertiary)]/70">{hint}</span>
      )}
    </div>
  );
}

function KpiCard({ kpi, index }: { kpi: ValtaKPI; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.22 + index * 0.08, ease: "easeOut" }}
      className="relative flex flex-col rounded-2xl p-3.5 overflow-hidden border"
      style={{
        background:
          "linear-gradient(145deg, rgba(255,207,92,0.05) 0%, rgba(255,154,60,0.04) 100%)",
        borderColor: "rgba(255,207,92,0.14)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.03)",
      }}
    >
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3"
        style={{ background: "linear-gradient(90deg, transparent, rgba(255,207,92,0.6), transparent)" }}
      />
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[9px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-text-tertiary)]">
          {kpi.label}
        </span>
        <span
          className={cn(
            "text-[10px] font-medium tabular-nums",
            kpi.trend === "up" ? "text-emerald-400/90" : "text-rose-400/90",
          )}
        >
          {kpi.delta}
        </span>
      </div>
      <p className="text-[22px] leading-none font-medium text-[var(--axiom-text-primary)] tabular-nums mb-2">
        {kpi.value}
      </p>
      <div className="h-9 -mx-1">
        <Sparkline series={kpi.series} height={36} width={96} />
      </div>
    </motion.div>
  );
}

function TradeRow({ trade, index }: { trade: Trade; index: number }) {
  const isWin = trade.pnl >= 0;
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: 0.35 + index * 0.06 }}
      className="flex items-center gap-2.5 rounded-xl px-2.5 py-2 transition-colors flex-shrink-0"
      style={{ border: "1px solid transparent" }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,207,92,0.14)";
        (e.currentTarget as HTMLElement).style.background = "rgba(255,207,92,0.04)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "transparent";
        (e.currentTarget as HTMLElement).style.background = "transparent";
      }}
    >
      {/* Instrument badge */}
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 border"
        style={{ background: INSTRUMENT_HUE[trade.instrument], borderColor: "rgba(240,241,243,0.06)" }}
      >
        <span className={cn("text-[10px] font-bold tracking-tight", INSTRUMENT_TEXT[trade.instrument])}>
          {trade.instrument === "GOLD" ? "Au" : "DJ"}
        </span>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{trade.instrument}</p>
          <svg
            width="9"
            height="9"
            viewBox="0 0 24 24"
            fill="none"
            stroke={isWin ? "#22d377" : "#ff4d6a"}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {isWin ? <path d="M12 19V5M5 12l7-7 7 7" /> : <path d="M12 5v14M5 12l7 7 7-7" />}
          </svg>
        </div>
        <p className="text-[10px] text-[var(--axiom-text-tertiary)]">Lot {trade.lot} · {trade.time}</p>
      </div>

      <span
        className={cn(
          "text-[12px] font-semibold tabular-nums flex-shrink-0",
          isWin ? "text-emerald-400/90" : "text-rose-400/90",
        )}
      >
        {isWin ? "+" : "−"}${Math.abs(trade.pnl).toLocaleString()}
      </span>
    </motion.div>
  );
}

export default function ValtaConsole() {
  const router = useRouter();
  const { setActiveWorkstation } = useAxiomStore();
  const d = valtaData;

  const openWorkstation = () => {
    setActiveWorkstation("valta");
    router.push("/valta");
  };

  return (
    <div
      className="relative w-full h-full min-h-0 rounded-3xl overflow-hidden backdrop-blur-xl flex flex-col"
      style={{
        background: `
          radial-gradient(ellipse at top left, rgba(255,207,92,0.09) 0%, transparent 55%),
          radial-gradient(ellipse at bottom right, rgba(255,154,60,0.07) 0%, transparent 50%),
          linear-gradient(150deg, rgba(12,12,14,0.6) 0%, rgba(18,16,13,0.6) 100%)
        `,
        border: "1px solid rgba(255,207,92,0.16)",
        boxShadow: `
          0 8px 40px -12px rgba(255,207,92,0.18),
          inset 0 1px 0 rgba(255,255,255,0.03)
        `,
      }}
    >
      {/* Scanline texture */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(240,241,243,0.6) 2px, rgba(240,241,243,0.6) 4px)",
        }}
      />

      {/* Header */}
      <div className="relative flex items-center justify-between px-5 pt-4 pb-3 border-b border-[rgba(255,207,92,0.12)] z-10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-[#201600] relative overflow-hidden"
            style={{ background: identity, boxShadow: "0 0 24px -4px rgba(255,207,92,0.5)" }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/25 to-transparent" />
            {/* Candlestick mark */}
            <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" className="relative" aria-hidden>
              <rect x="4" y="6" width="2.4" height="12" rx="0.8" opacity="0.5" />
              <rect x="4" y="8" width="2.4" height="2.4" />
              <rect x="10" y="3" width="2.4" height="18" rx="0.8" />
              <rect x="10" y="5" width="2.4" height="3" />
              <rect x="16" y="8" width="2.4" height="13" rx="0.8" opacity="0.5" />
              <rect x="16" y="10" width="2.4" height="2.4" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-tight text-[var(--axiom-text-primary)]">
              HOUSE OF VALTA
            </h3>
            <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">
              Trading Performance
            </p>
          </div>
        </div>

        <motion.button
          onClick={openWorkstation}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-[var(--axiom-text-secondary)] hover:text-[#ffcf5c] transition-colors flex-shrink-0"
          style={{ border: "1px solid rgba(255,207,92,0.15)", background: "rgba(255,207,92,0.05)" }}
          aria-label="Open House of Valta workstation"
        >
          <span>Workstation</span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17L17 7M7 7h10v10" />
          </svg>
        </motion.button>
      </div>

      {/* Content — self-scrolling safety net; on desktop everything fits without scroll */}
      <div className="relative flex-1 min-h-0 overflow-y-auto hide-scrollbar px-5 py-4 z-10 flex flex-col gap-4">
        {/* KPI Row */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 flex-shrink-0">
          {d.kpis.map((kpi, i) => (
            <KpiCard key={kpi.key} kpi={kpi} index={i} />
          ))}
        </div>

        {/* Lower section — Equity Curve takes the larger share */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.4fr)] gap-4 lg:h-[300px] min-h-0 flex-1">
          {/* TRADE PERFORMANCE — internally scrollable */}
          <section
            className="rounded-2xl p-4 border flex flex-col min-h-0"
            style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(14,16,20,0.4)" }}
          >
            <PanelTitle title="Trade Performance" hint={`${d.closedTotal} closed`} />
            <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar pr-1 -mr-1">
              <div className="flex flex-col gap-0.5">
                {d.trades.map((trade, i) => (
                  <TradeRow key={trade.id} trade={trade} index={i} />
                ))}
              </div>
            </div>
          </section>

          {/* EQUITY CURVE — primary visualization */}
          <section
            className="rounded-2xl p-4 border flex flex-col min-h-0"
            style={{
              borderColor: "rgba(255,207,92,0.12)",
              background:
                "linear-gradient(150deg, rgba(255,207,92,0.04) 0%, rgba(14,16,20,0.4) 100%)",
            }}
          >
            <PanelTitle title="Equity Curve" hint={d.equityDelta} />
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-xl font-semibold text-[var(--axiom-text-primary)] tabular-nums">
                {d.equityEnd}
              </span>
              <span className="text-[11px] font-medium text-emerald-400/90">
                from {d.equityStart}
              </span>
            </div>
            <div className="flex-1 min-h-0 mt-1">
              <EquityChart series={d.equity} height={210} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}