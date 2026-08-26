"use client";

import { motion } from "framer-motion";
import { weeklyReports, monthlyReports, reportAnalytics, equitySeries } from "./valta-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip, PlText, AuthorityNote } from "./valta-ui";
import { Sparkline, DonutChart } from "./valta-charts";
import { profitDistribution } from "./valta-data";

export default function Reports() {
  const latest = monthlyReports[monthlyReports.length - 1];

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="Reports"
        subtitle="Deep trading performance analysis"
        right={<StatusChip label="Demo data" tone="neutral" />}
      />

      {/* Monthly overview strip */}
      <Panel className="min-w-0">
        <SectionTitle title="Monthly Performance" hint={latest.month} />
        <div className="px-4 pb-4 grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-y-5 gap-x-2">
          {[
            { label: "Total profit", value: `$${latest.totalProfit.toLocaleString("en-US")}`, tone: "pos" },
            { label: "Net profit", value: `$${latest.netProfit.toLocaleString("en-US")}`, tone: "pos" },
            { label: "Profit factor", value: latest.profitFactor.toFixed(2), tone: "neutral" },
            { label: "Win rate", value: `${latest.winRate}%`, tone: "neutral" },
            { label: "Drawdown", value: `${latest.drawdown}%`, tone: "neg" },
            { label: "Total trades", value: `${latest.trades}`, tone: "neutral" },
          ].map((s, i) => (
            <motion.div key={s.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.05 }}>
              <div className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1.5">{s.label}</div>
              <div className={s.tone === "pos" ? "text-emerald-400/90" : s.tone === "neg" ? "text-rose-400/90" : "text-[var(--axiom-text-primary)]"}>
                <span className="text-lg font-semibold tabular-nums">{s.value}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </Panel>

      {/* Weekly performance */}
      <Panel className="min-w-0">
        <SectionTitle title="Weekly Performance" hint="Last 3 weeks" />
        <div className="px-4 pb-4 overflow-x-auto">
          <table className="w-full text-left border-separate" style={{ borderSpacing: "0 4px" }}>
            <thead>
              <tr className="text-[9px] font-semibold uppercase tracking-[0.14em] text-[var(--axiom-text-tertiary)]">
                <th className="pb-1.5 font-semibold">Week</th>
                <th className="pb-1.5 font-semibold text-right">Profit</th>
                <th className="pb-1.5 font-semibold text-right">Loss</th>
                <th className="pb-1.5 font-semibold text-right">Win rate</th>
                <th className="pb-1.5 font-semibold text-right">Trades</th>
                <th className="pb-1.5 font-semibold text-right">Avg win</th>
                <th className="pb-1.5 font-semibold text-right">Avg loss</th>
              </tr>
            </thead>
            <tbody>
              {weeklyReports.map((w) => (
                <tr key={w.week} className="text-[12px] text-[var(--axiom-text-primary)] rounded-lg" style={{ background: "rgba(10,12,16,0.4)" }}>
                  <td className="py-2.5 px-2.5 rounded-l-lg text-[var(--axiom-text-secondary)] font-medium">{w.week}</td>
                  <td className="py-2.5 px-2.5 text-right text-emerald-400/90 tabular-nums">${w.profit}</td>
                  <td className="py-2.5 px-2.5 text-right text-rose-400/90 tabular-nums">-${w.loss}</td>
                  <td className="py-2.5 px-2.5 text-right tabular-nums">{w.winRate}%</td>
                  <td className="py-2.5 px-2.5 text-right tabular-nums">{w.trades}</td>
                  <td className="py-2.5 px-2.5 text-right text-emerald-400/90 tabular-nums">${w.avgWin}</td>
                  <td className="py-2.5 px-2.5 text-right text-rose-400/90 tabular-nums rounded-r-lg">-${Math.abs(w.avgLoss)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Historical monthly rows */}
      <Panel className="min-w-0">
        <SectionTitle title="Historical Monthly" hint="Net results" />
        <div className="px-4 pb-4 space-y-2">
          {monthlyReports.map((m) => (
            <div key={m.month} className="flex items-center gap-4 rounded-lg border px-3 py-2.5" style={{ borderColor: "rgba(240,241,243,0.05)", background: "rgba(10,12,16,0.4)" }}>
              <span className="w-24 text-[12px] text-[var(--axiom-text-primary)] font-medium">{m.month}</span>
              <div className="flex-1 flex items-center gap-4 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)]">Net</span>
                  <PlText value={m.netProfit} className="text-[13px] font-semibold" />
                </div>
                <div className="hidden md:flex items-center gap-3 text-[10px] text-[var(--axiom-text-tertiary)]">
                  <span>PF {m.profitFactor.toFixed(2)}</span>
                  <span className={m.drawdown > 8 ? "text-rose-400/90" : "text-emerald-400/90"}>DD {m.drawdown}%</span>
                  <span>{m.winRate}% WR</span>
                  <span>{m.trades} trades</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Analytics visual areas — prepared, placeholder */}
      <div>
        <SectionTitle title="Analytics" hint="Visual areas prepared for the analytics engine" className="px-0 mb-3" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
          <Panel className="min-w-0">
            <SectionTitle title="Equity growth" />
            <div className="px-4 pb-4 h-[120px] min-w-0"><Sparkline series={equitySeries.map((p) => p.equity)} height={120} width={200} /></div>
          </Panel>
          <Panel className="min-w-0">
            <SectionTitle title="Profit distribution" />
            <div className="px-4 pb-4"><DonutChart slices={profitDistribution} size={120} /></div>
          </Panel>
          {reportAnalytics.filter((a) => a.id !== "a1" && a.id !== "a2").map((a) => (
            <Panel key={a.id} className="min-w-0">
              <SectionTitle title={a.label} />
              <div className="px-4 pb-5">
                {/* Placeholder bar-visual, ready for real data */}
                <div className="flex items-end gap-1.5 h-[72px]">
                  {[38, 54, 42, 66, 58, 74, 62].map((h, i) => (
                    <motion.div key={i} className="flex-1 rounded-t" style={{ background: "linear-gradient(180deg, rgba(109,124,255,0.7), rgba(109,124,255,0.12))" }} initial={{ height: 0 }} animate={{ height: `${h}%` }} transition={{ delay: 0.2 + i * 0.05 }} />
                  ))}
                </div>
                <div className="mt-3 text-[10px] text-[var(--axiom-text-tertiary)]">{a.description}</div>
              </div>
            </Panel>
          ))}
        </div>
      </div>

      <AuthorityNote />
    </div>
  );
}