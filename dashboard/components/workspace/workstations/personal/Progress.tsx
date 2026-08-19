"use client";

import { motion } from "framer-motion";
import { habits, weeklyTrend, monthlyTrend } from "./personal-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip } from "./personal-ui";
import { ProgressRing, TrendBars, ConsistencyDots } from "./personal-charts";
import { PERSONAL_SUCCESS, PERSONAL_TEAL, PERSONAL_VIOLET, PERSONAL_GOLD } from "./types";

const TREND_CARDS = [
  { label: "Daily completion", value: 88, color: PERSONAL_SUCCESS },
  { label: "Learning", value: 95, color: PERSONAL_TEAL },
  { label: "Sleep — 8h", value: 86, color: PERSONAL_VIOLET },
  { label: "Training", value: 88, color: PERSONAL_GOLD },
];

export default function Progress() {
  const avgConsistency = Math.round(habits.reduce((a, h) => a + h.consistency, 0) / habits.length);
  const totalStreak = Math.max(...habits.map((h) => h.streak));

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="Progress & Habits"
        subtitle="Development analytics · advanced & analytical, not gamified"
        right={<StatusChip label={`${avgConsistency}% avg consistency`} tone="active" />}
      />

      {/* Trend summary */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {TREND_CARDS.map((c, i) => (
          <motion.div key={c.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 + i * 0.05 }} className="rounded-2xl border p-4 flex items-center gap-3" style={{ borderColor: "rgba(109,124,255,0.12)", background: "rgba(15,18,24,0.42)" }}>
            <ProgressRing value={c.value} size={56} />
            <div className="min-w-0">
              <div className="text-[10px] text-[var(--axiom-text-secondary)]">{c.label}</div>
              <div className="text-lg font-semibold text-[var(--axiom-text-primary)] tabular-nums leading-none mt-1">{c.value}%</div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(300px,40%)_1fr] gap-5 items-start">
        {/* Habits table */}
        <Panel className="min-w-0">
          <SectionTitle title="Habit consistency" hint={`Best streak ${totalStreak} days`} />
          <div className="px-4 pb-4 space-y-3">
            <div className="grid grid-cols-[1.2fr_0.8fr_1fr] gap-2 text-[9px] font-semibold tracking-[0.14em] uppercase text-[var(--axiom-text-tertiary)] pb-1.5 border-b" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
              <span>Habit</span><span className="text-right">Streak</span><span className="text-right">Week</span>
            </div>
            {habits.map((h, i) => (
              <motion.div key={h.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 + i * 0.04 }} className="grid grid-cols-[1.2fr_0.8fr_1fr] items-center gap-2">
                <div className="min-w-0">
                  <span className="text-[12px] text-[var(--axiom-text-primary)] block truncate">{h.label}</span>
                  <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{h.consistency}%</span>
                </div>
                <div className="flex items-center justify-end gap-1.5">
                  <span className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold tabular-nums" style={{ color: "#22d377", background: "rgba(34,211,119,0.08)" }}>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M23 6l-9.5 9.5-5-5L1 18" /><path d="M17 6h6v6" /></svg>
                    {h.streak}
                  </span>
                </div>
                <div className="flex justify-end"><ConsistencyDots weekly={h.weekly} /></div>
              </motion.div>
            ))}
          </div>
        </Panel>

        {/* Trends */}
        <div className="flex flex-col gap-5 min-w-0">
          <Panel className="min-w-0">
            <SectionTitle title="Weekly trend" hint="Completion %" />
            <div className="px-4 pb-3 min-w-0">
              <div className="h-[140px] min-w-0"><TrendBars points={weeklyTrend} color={PERSONAL_SUCCESS} /></div>
            </div>
          </Panel>
          <Panel className="min-w-0">
            <SectionTitle title="Monthly trend" hint="Learning & development" />
            <div className="px-4 pb-3 min-w-0">
              <div className="h-[140px] min-w-0"><TrendBars points={monthlyTrend} color={PERSONAL_TEAL} /></div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}