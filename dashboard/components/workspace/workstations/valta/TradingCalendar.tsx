"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { calendarMonth, type TradingDay } from "./valta-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip, PlText, AssetChip } from "./valta-ui";
import { VALTA_SUCCESS, VALTA_LOSS } from "./types";

const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const MONTH_LEN = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function DayCell({ day, trade }: { day: number; trade?: TradingDay }) {
  const isTrading = !!trade && trade.status !== "none";
  const tone = isTrading ? trade!.status : "none";
  const today = day === 12;

  return (
    <div
      className={cn(
        "relative h-[84px] rounded-xl border p-2 flex flex-col justify-between overflow-hidden transition-colors duration-200",
        tone === "profit" && "hover:bg-emerald-400/[0.06]",
        tone === "loss" && "hover:bg-rose-400/[0.06]",
        tone === "none" && "hover:bg-[var(--axiom-bg-glass-hover)]",
        today && "ring-1",
      )}
      style={{
        borderColor: tone === "profit" ? "rgba(34,211,119,0.16)" : tone === "loss" ? "rgba(255,77,106,0.16)" : "rgba(240,241,243,0.06)",
        background: tone === "profit" ? "rgba(34,211,119,0.05)" : tone === "loss" ? "rgba(255,77,106,0.05)" : "rgba(10,12,16,0.4)",
        ...(today ? { outline: `1px solid ${VALTA_SUCCESS}`, outlineOffset: -1 } : {}),
      }}
    >
      <div className="flex items-center justify-between">
        <span className={cn("text-[11px] font-medium tabular-nums", today ? "text-emerald-400" : "text-[var(--axiom-text-secondary)]")}>{day}</span>
        {isTrading && (
          <span
            className="w-2 h-2 rounded-full"
            style={{ background: tone === "profit" ? VALTA_SUCCESS : VALTA_LOSS, boxShadow: `0 0 6px ${tone === "profit" ? VALTA_SUCCESS : VALTA_LOSS}66` }}
          />
        )}
      </div>

      {isTrading ? (
        <div className="min-w-0">
          <PlText value={trade!.pl!} className="text-[12px] font-semibold" />
          <div className="flex items-center gap-1 mt-0.5 overflow-hidden">
            {trade!.instruments!.slice(0, 2).map((inst) => (
              <span key={inst} className="text-[8px] font-semibold text-[var(--axiom-text-secondary)] rounded px-1 py-px bg-[var(--axiom-bg-elevated)] border border-[rgba(240,241,243,0.06)]">
                {inst}
              </span>
            ))}
            {trade!.instruments!.length > 2 && <span className="text-[8px] text-[var(--axiom-text-tertiary)]">+{trade!.instruments!.length - 2}</span>}
          </div>
          <div className="mt-0.5 text-[8px] text-[var(--axiom-text-tertiary)] tabular-nums">{trade!.trades} trades · {trade!.lots}</div>
        </div>
      ) : (
        <span className="text-[9px] text-[var(--axiom-text-tertiary)]/40">No trade</span>
      )}
    </div>
  );
}

export default function TradingCalendar() {
  const base = useMemo(() => {
    const monthIdx = calendarMonth.month;
    return { label: `${MONTH_NAMES[monthIdx]} ${calendarMonth.year}`, monthIdx, year: calendarMonth.year };
  }, []);
  const [offset, setOffset] = useState(0);

  const shown = useMemo(() => {
    const monthIdx = base.monthIdx + offset;
    const year = base.year + Math.floor(monthIdx / 12);
    const m = ((monthIdx % 12) + 12) % 12;
    return { label: `${MONTH_NAMES[m]} ${year}`, len: MONTH_LEN[m], m };
  }, [base, offset]);

  const dayMap = useMemo(() => new Map(calendarMonth.days.map((d) => [d.day, d])), []);
  const cells: (TradingDay | undefined)[] = Array.from({ length: shown.len }, (_, i) => dayMap.get(i + 1));

  const perks = useMemo(() => {
    const days = calendarMonth.days.filter((d) => d.status !== "none");
    const profit = days.filter((d) => d.status === "profit").length;
    const loss = days.filter((d) => d.status === "loss").length;
    const totalTrades = days.reduce((a, d) => a + (d.trades ?? 0), 0);
    return { profit, loss, totalTrades };
  }, []);

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="Trading Calendar"
        subtitle="Daily performance · Valta Prime"
        right={
          <>
            <StatusChip label={`${perks.profit} profitable`} tone="active" />
            <StatusChip label={`${perks.loss} losing`} tone="danger" />
            <StatusChip label={`${perks.totalTrades} trades`} tone="neutral" />
          </>
        }
      />

      {/* Legend */}
      <div className="flex items-center gap-4 text-[10px] text-[var(--axiom-text-secondary)]">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: VALTA_SUCCESS }} /> Profitable day</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: VALTA_LOSS }} /> Losing day</span>
        <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-text-tertiary)]" /> Non-trading day</span>
      </div>

      <Panel className="min-w-0">
        {/* Month nav */}
        <div className="flex items-center justify-between px-4 pt-4">
          <SectionTitle title={shown.label} className="mb-0 px-0 pt-0" />
          <div className="flex items-center gap-1.5">
            <button onClick={() => setOffset((o) => o - 1)} aria-label="Previous month" className="w-8 h-8 rounded-lg border hover:border-[var(--axiom-border-hover)] hover:bg-[var(--axiom-bg-glass-hover)] flex items-center justify-center text-[var(--axiom-text-secondary)]">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
            </button>
            <button onClick={() => setOffset((o) => o + 1)} aria-label="Next month" className="w-8 h-8 rounded-lg border hover:border-[var(--axiom-border-hover)] hover:bg-[var(--axiom-bg-glass-hover)] flex items-center justify-center text-[var(--axiom-text-secondary)]">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6" /></svg>
            </button>
          </div>
        </div>

        <div className="px-4 pb-4 mt-1">
          {/* Weekday headers */}
          <div className="grid grid-cols-7 gap-1.5 mb-1.5">
            {calendarMonth.weekdayHeaders.map((h) => (
              <div key={h} className="text-center text-[9px] font-semibold tracking-[0.16em] text-[var(--axiom-text-tertiary)]">{h}</div>
            ))}
          </div>
          {/* Day grid */}
          <AnimatePresence mode="popLayout">
            <motion.div key={shown.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }} className="grid grid-cols-7 gap-1.5">
              {Array.from({ length: calendarMonth.leadingBlanks }, (_, i) => (
                <div key={`blank-${i}`} className="h-[84px] rounded-xl border border-transparent" />
              ))}
              {cells.map((trade, i) => (
                <DayCell key={i} day={i + 1} trade={trade} />
              ))}
            </motion.div>
          </AnimatePresence>
        </div>
      </Panel>

      {/* Selected-day detail strip — shows richer info for a trading day */}
      <Panel className="min-w-0">
        <SectionTitle title="Day detail" hint="Demo · 12 Aug (today)" />
        <div className="px-4 pb-4">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
            <div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">Daily P/L</div>
              <PlText value={420} className="text-xl font-semibold" />
            </div>
            <div className="flex flex-col gap-1">
              <div className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">Instruments</div>
              <div className="flex items-center gap-1.5"><AssetChip label="XAUUSD" /><AssetChip label="US30" /></div>
            </div>
            <div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">Trades</div>
              <span className="text-sm text-[var(--axiom-text-primary)] font-medium tabular-nums">2</span>
            </div>
            <div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">Lot sizes</div>
              <span className="text-sm text-[var(--axiom-text-primary)] font-medium tabular-nums">0.20 / 0.10</span>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}