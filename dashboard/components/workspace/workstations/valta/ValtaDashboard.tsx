"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  kpis,
  equitySeries,
  profitDistribution,
  instrumentBreakdown,
  monthlySeries,
  recentTrades,
  newsFeed,
  newsCategories,
  institutionalIntel,
} from "./valta-data";
import { EquityChart, DonutChart, MonthlyBarChart } from "./valta-charts";
import { Panel, SectionTitle, StatusChip, MetricCard, AssetChip, PlText, ResolutionDot, AuthorityNote } from "./valta-ui";
import { VALTA_ACCENT, VALTA_VIOLET, VALTA_GOLD } from "./types";

// ── LEFT · Market Intelligence feed ─────────────────────────────────────────
const IMPORTANCE_STYLE: Record<string, { dot: string; label?: string; text: string; ring: string }> = {
  breaking: { dot: "rgba(255,77,106,1)", label: "Breaking", text: "text-rose-400", ring: "rgba(255,77,106,0.16)" },
  high: { dot: "rgba(255,184,48,1)", text: "text-amber-300/90", ring: "rgba(255,184,48,0.10)" },
  medium: { dot: "rgba(109,124,255,1)", text: "text-[var(--axiom-text-secondary)]", ring: "transparent" },
  low: { dot: "rgba(240,241,243,0.25)", text: "text-[var(--axiom-text-tertiary)]", ring: "transparent" },
};

function MarketIntelligence() {
  return (
    <Panel className="flex flex-col min-h-0 h-full">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
        <div className="flex items-center justify-between mb-1">
          <h4 className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)]">Market Intelligence</h4>
          <div className="flex items-center gap-1.5 rounded-full px-2 py-0.5 border" style={{ borderColor: "rgba(34,211,119,0.25)", background: "rgba(34,211,119,0.06)" }}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[9px] font-semibold tracking-widest text-emerald-400">LIVE</span>
          </div>
        </div>
        <div className="flex items-center justify-between text-[10px] text-[var(--axiom-text-secondary)]">
          <span>Updated 2 min ago</span>
          <span className="text-emerald-400/80">Feed connected · 7 sources</span>
        </div>
        {/* Categories */}
        <div className="flex flex-wrap gap-1.5 mt-3">
          {newsCategories.map((c) => (
            <span key={c} className="rounded-full px-2 py-0.5 text-[9px] font-medium text-[var(--axiom-text-secondary)] border" style={{ borderColor: "rgba(240,241,243,0.08)" }}>
              {c}
            </span>
          ))}
        </div>
      </div>

      {/* Scrollable feed */}
      <div className="flex-1 overflow-y-auto hide-scrollbar px-3 py-3 min-h-0 space-y-2.5">
        {newsFeed.map((item, i) => {
          const imp = IMPORTANCE_STYLE[item.importance];
          const breaking = item.importance === "breaking";
          return (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.05 }}
              className={cn("rounded-xl border p-3", breaking && "ring-1", !breaking && "hover:border-[var(--axiom-border-hover)]")}
              style={{ borderColor: imp.ring, background: breaking ? "rgba(255,77,106,0.04)" : "rgba(240,241,243,0.02)" }}
            >
              {breaking && (
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: imp.dot }} />
                  <span className="text-[9px] font-bold tracking-[0.16em] text-rose-400">BREAKING</span>
                </div>
              )}
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[9px] font-semibold tracking-wider uppercase text-[var(--axiom-violet)]">{item.category}</span>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{item.time}</span>
              </div>
              <p className="text-[12px] leading-snug text-[var(--axiom-text-primary)] font-medium">{item.headline}</p>
              <p className="text-[11px] leading-snug text-[var(--axiom-text-secondary)] mt-1 line-clamp-2">{item.summary}</p>
              <div className="flex items-center gap-1.5 mt-2">
                <span className="w-1 h-1 rounded-full" style={{ background: imp.dot }} />
                <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{item.source}</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Institutional intelligence */}
      <div className="border-t px-4 py-3" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
        <div className="text-[10px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)] mb-2.5">Institutional intelligence</div>
        <div className="space-y-2.5">
          {institutionalIntel.map((it) => (
            <div key={it.id} className="flex gap-2.5 text-[11px] leading-snug">
              <span className={cn("mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0", it.tone === "bullish" ? "bg-emerald-400" : it.tone === "bearish" ? "bg-rose-400" : "bg-[var(--axiom-text-tertiary)]")} />
              <div className="min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[9px] font-semibold tracking-wide uppercase text-[var(--axiom-text-secondary)]">{it.kind}</span>
                  <span className="text-[9px] text-[var(--axiom-text-tertiary)] flex-shrink-0">{it.time}</span>
                </div>
                <p className="text-[var(--axiom-text-secondary)]">{it.detail}</p>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{it.source}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}

// ── RIGHT · Trade breakdown table ──────────────────────────────────────────
function TradeBreakdown() {
  const totalPl = instrumentBreakdown.reduce((acc, x) => acc + x.pl, 0);
  return (
    <Panel className="min-w-0">
      <SectionTitle title="Trade Breakdown" hint="By instrument" />
      <div className="px-4 pb-4">
        <div className="grid grid-cols-[1.1fr_1fr_1fr_1.2fr] gap-2 text-[9px] font-semibold tracking-[0.14em] uppercase text-[var(--axiom-text-tertiary)] pb-2 border-b" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
          <span>Instrument</span><span className="text-right">Trades</span>
          <span className="text-right">W / L</span><span className="text-right">P/L</span>
        </div>
        <div className="divide-y" style={{ borderColor: "rgba(240,241,243,0.04)" }}>
          {instrumentBreakdown.map((row) => (
            <div key={row.key} className="grid grid-cols-[1.1fr_1fr_1fr_1.2fr] items-center gap-2 py-3">
              <div className="flex flex-col min-w-0">
                <AssetChip label={row.instrument} />
                <span className="text-[9px] text-[var(--axiom-text-tertiary)] mt-0.5 truncate">{row.name} · {row.winRate}%</span>
              </div>
              <span className="text-[12px] text-[var(--axiom-text-primary)] text-right tabular-nums">{row.trades}</span>
              <div className="flex items-center justify-end gap-1.5">
                <span className="text-[11px] text-emerald-400/90 tabular-nums">{row.wins}</span>
                <span className="text-[10px] text-[var(--axiom-text-tertiary)]">/</span>
                <span className="text-[11px] text-rose-400/90 tabular-nums">{row.losses}</span>
              </div>
              <PlText value={row.pl} className="text-right text-[12px] font-medium" />
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between pt-2.5 mt-1 border-t text-[11px]" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
          <span className="text-[var(--axiom-text-tertiary)] uppercase tracking-wider text-[9px] font-semibold">Total</span>
          <PlText value={totalPl} className="font-semibold text-[12px]" />
        </div>
      </div>
    </Panel>
  );
}

// ── Activity rows ──────────────────────────────────────────────────────────
function ActivityRow({ t }: { t: (typeof recentTrades)[number] }) {
  return (
    <div className="grid grid-cols-[1.2fr_0.7fr_0.7fr_1fr] items-center gap-2 py-2.5">
      <div className="flex items-center gap-2 min-w-0">
        <ResolutionDot tone={t.result} />
        <span className="text-[11px] font-medium text-[var(--axiom-text-primary)] flex-shrink-0">{t.instrument}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className={cn("text-[10px] font-semibold", t.direction === "BUY" ? "text-emerald-400" : "text-rose-400")}>{t.direction}</span>
        <span className="text-[9px] text-[var(--axiom-text-tertiary)] tabular-nums">{t.entry}</span>
      </div>
      <PlText value={t.pl} className="text-[11px]" />
      <span className="text-[9px] text-[var(--axiom-text-tertiary)] text-right tabular-nums">{t.lot} · {t.date}</span>
    </div>
  );
}

function TradingActivity() {
  return (
    <Panel className="min-w-0">
      <SectionTitle title="Trading Activity" hint="Recent" />
      <div className="px-4 pb-3 grid grid-cols-[1.2fr_0.7fr_0.7fr_1fr] gap-2 text-[9px] font-semibold tracking-[0.14em] uppercase text-[var(--axiom-text-tertiary)]">
        <span>Instrument</span><span>Direction</span><span>P/L</span><span className="text-right">Lot · Date</span>
      </div>
      <div className="px-4 divide-y" style={{ borderColor: "rgba(240,241,243,0.04)" }}>
        {recentTrades.map((t) => <ActivityRow key={t.id} t={t} />)}
      </div>
    </Panel>
  );
}

// ── Main dashboard ─────────────────────────────────────────────────────────
export default function ValtaDashboard() {
  const lastEquity = equitySeries[equitySeries.length - 1].equity;
  const startEquity = equitySeries[0].equity;
  const equityDelta = ((lastEquity - startEquity) / startEquity) * 100;

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      {/* Identity header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">
            <span className="text-[var(--axiom-violet)]">Valta Prime</span>
            <span>·</span>
            <span>Markets & Strategy</span>
          </div>
          <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">HOUSE OF VALTA — MAIN DASHBOARD</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip label="Markets Open" tone="active" />
          <StatusChip label="Analysis Mode" tone="neutral" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(290px,30%)_1fr] gap-5 items-start">
        {/* LEFT — Market intelligence */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="lg:sticky lg:top-0 min-w-0 h-[320px] lg:h-[calc(100vh-170px)]">
          <MarketIntelligence />
        </motion.div>

        {/* RIGHT — Trading analytics — the dominant area */}
        <div className="flex flex-col gap-5 min-w-0">
          {/* KPI row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
            {kpis.map((kpi, i) => (
              <MetricCard key={kpi.key} kpi={kpi} index={i} />
            ))}
          </div>

          {/* Profit growth — primary chart, largest portion */}
          <Panel className="min-w-0">
            <SectionTitle
              title="Profit Growth"
              hint="Equity · Last 24 weeks"
              right={
                <span className="flex items-center gap-1.5 text-[10px] text-emerald-400/90 font-medium">
                  {equityDelta >= 0 ? "▲" : "▼"} +{equityDelta.toFixed(1)}% net
                </span>
              }
            />
            <div className="flex flex-col md:flex-row md:items-end gap-4 px-4 pb-2">
              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-semibold text-[var(--axiom-text-primary)] tabular-nums">${lastEquity.toLocaleString("en-US")}</span>
                  <span className="text-[11px] font-medium text-emerald-400/90">+{Math.round(lastEquity - startEquity).toLocaleString("en-US")} all-time</span>
                </div>
                <div className="mt-1.5 flex items-center gap-4 text-[10px] text-[var(--axiom-text-secondary)]">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: VALTA_ACCENT }} /> Start</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: VALTA_VIOLET }} /> Growth</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: VALTA_GOLD }} /> Current</span>
                </div>
              </div>
              <div className="md:ml-auto flex items-center gap-2">
                {["1M", "3M", "6M", "ALL"].map((r) => (
                  <button key={r} className="rounded-md px-2 py-1 text-[10px] font-medium text-[var(--axiom-text-secondary)] border border-transparent hover:text-[var(--axiom-text-primary)] hover:border-[var(--axiom-border-hover)]">
                    {r}
                  </button>
                ))}
              </div>
            </div>
            <div className="px-3 h-[240px] min-w-0 mt-1">
              <EquityChart series={equitySeries} height={240} />
            </div>
          </Panel>

          {/* Distribution + Trade breakdown */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 min-w-0">
            <Panel className="min-w-0">
              <SectionTitle title="Profit Distribution" hint="214 trades" />
              <div className="px-4 pb-5 flex items-center">
                <DonutChart slices={profitDistribution} />
              </div>
            </Panel>
            <TradeBreakdown />
          </div>

          {/* Monthly performance + Trading activity */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 min-w-0">
            <Panel className="min-w-0">
              <SectionTitle title="Monthly Performance" hint="Profit · Loss · Net" />
              <div className="px-3 pb-4 h-[190px] min-w-0">
                <MonthlyBarChart series={monthlySeries} height={190} />
              </div>
              <div className="flex items-center gap-4 px-4 pb-3 text-[10px] text-[var(--axiom-text-secondary)]">
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Profit</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-400" /> Loss</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[var(--axiom-accent)]" /> Net</span>
              </div>
            </Panel>
            <TradingActivity />
          </div>

          {/* Authority boundary */}
          <AuthorityNote />
        </div>
      </div>
    </div>
  );
}