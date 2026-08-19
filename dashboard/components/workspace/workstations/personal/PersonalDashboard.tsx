"use client";

import { cn } from "@/lib/utils";
import { quickStatus, todaysRoutine, routineTypeColor, upcomingEvents, dailyPriorities, reminders, dailyBrief, type UpcomingEvent } from "./personal-data";
import { Panel, SectionTitle, StatusChip } from "./personal-ui";
import { ProgressRing, QuickStatusBar, ProgressMeter } from "./personal-charts";
import { PERSONAL_TEAL, PERSONAL_VIOLET } from "./types";

const KIND_LABEL: Record<UpcomingEvent["kind"], string> = {
  meeting: "Meeting", training: "Training", learning: "Learning", work: "Work", review: "Review", personal: "Personal", reminder: "Reminder",
};

function RoutineTimeline() {
  return (
    <Panel className="min-w-0">
      <SectionTitle title="Today's schedule" hint="Routine" />
      <div className="px-4 pb-4">
        <div className="relative pl-4 border-l" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
          {todaysRoutine.map((b) => {
            const current = b.status === "current";
            const color = routineTypeColor[b.type];
            return (
              <div key={b.id} className="relative pb-4 last:pb-0">
                <span
                  className={cn("absolute -left-[21px] top-1 w-[7px] h-[7px] rounded-full border-2 border-[var(--axiom-bg-base)]", current && "animate-pulse")}
                  style={{ background: color, boxShadow: current ? `0 0 10px ${color}` : "none" }}
                />
                <div className={cn("flex items-center gap-3", current && "opacity-100")}>
                  <span className="w-10 text-[11px] font-semibold text-[var(--axiom-text-secondary)] tabular-nums flex-shrink-0">{b.time}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className={cn("text-[12px] font-medium", current ? "text-[var(--axiom-text-primary)]" : b.status === "done" ? "text-[var(--axiom-text-secondary)]" : "text-[var(--axiom-text-primary)]/80")}>
                        {b.label}
                      </span>
                      {b.status === "done" && <span className="w-1 h-1 rounded-full bg-emerald-400" />}
                      {current && (
                        <span className="rounded-full px-1.5 py-0.5 text-[8px] font-bold tracking-widest text-white" style={{ background: PERSONAL_TEAL }}>
                          NOW
                        </span>
                      )}
                    </div>
                    {b.note && <span className="block text-[10px] text-[var(--axiom-text-tertiary)] truncate">{b.note}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Panel>
  );
}

function UpcomingEvents({ compact = false }: { compact?: boolean }) {
  return (
    <Panel className="min-w-0">
      <SectionTitle title="Upcoming" hint="Today" />
      <div className="px-4 pb-4 space-y-1">
        {upcomingEvents.slice(0, compact ? 3 : 4).map((e) => (
          <div key={e.id} className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-[var(--axiom-bg-glass-hover)]">
            <span className="w-12 text-[10px] font-semibold text-[var(--axiom-text-primary)] tabular-nums flex-shrink-0">{e.time}</span>
            <div className="min-w-0 flex-1">
              <span className="text-[12px] text-[var(--axiom-text-primary)] block truncate">{e.title}</span>
              {e.note && <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{e.note}</span>}
            </div>
            <span className={cn("rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider")} style={{ color: "#8b8d93", background: "rgba(240,241,243,0.05)" }}>
              {KIND_LABEL[e.kind]}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function DailyPriorities() {
  const done = dailyPriorities.filter((p) => p.done).length;
  return (
    <Panel className="min-w-0">
      <SectionTitle title="Daily priorities" hint={`${done} / ${dailyPriorities.length}`} />
      <div className="px-4 pb-4 space-y-0.5">
        {dailyPriorities.map((p) => (
          <div key={p.id} className={cn("flex items-center gap-3 rounded-lg px-2 py-2", p.done && "opacity-60")}>
            <span className={cn("w-4 h-4 rounded-md border flex items-center justify-center flex-shrink-0", p.done && "border-emerald-400/50")} style={{ borderColor: p.done ? "rgba(34,211,119,0.5)" : "rgba(240,241,243,0.14)" }}>
              {p.done && (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#22d377" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
              )}
            </span>
            <span className={cn("text-[12px]", p.done ? "line-through text-[var(--axiom-text-secondary)]" : "text-[var(--axiom-text-primary)]")}>{p.label}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function HabitRings() {
  const rings = [
    { label: "Sleep", value: 86 },
    { label: "Learning", value: 95 },
    { label: "Training", value: 88 },
    { label: "Wake", value: 92 },
  ];
  return (
    <Panel className="min-w-0">
      <SectionTitle title="Habit progress" hint="Today" />
      <div className="px-4 pb-5 grid grid-cols-4 gap-2">
        {rings.map((r) => (
          <div key={r.label} className="flex flex-col items-center gap-2">
            <ProgressRing value={r.value} size={62} />
            <span className="text-[9px] text-[var(--axiom-text-secondary)]">{r.label}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

export default function PersonalDashboard() {
  const done = dailyPriorities.filter((p) => p.done).length;

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">
            <span className="text-[var(--axiom-teal)]" style={{ color: PERSONAL_TEAL }}>Yamako</span>
            <span>·</span>
            <span>Personal Operations</span>
          </div>
          <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">PERSONAL — TODAY</h1>
          <p className="text-[12px] text-[var(--axiom-text-secondary)] mt-0.5">{dailyBrief.date} · {dailyBrief.greeting}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {dailyBrief.trainingComplete && <StatusChip label="Training Complete" tone="healthy" icon={<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#22d377" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>} />}
          <StatusChip label="On Track" tone="active" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(270px,30%)_1fr] gap-5 items-start">
        {/* LEFT — quick status + reminders */}
        <div className="flex flex-col gap-5 min-w-0">
          <Panel className="min-w-0">
            <SectionTitle title="Quick status" hint="TODAY" />
            <div className="px-4 pb-4 space-y-3.5">
              {quickStatus.map((s) => <QuickStatusBar key={s.key} stat={s} />)}
              <div className="flex items-center gap-3 border-t pt-3.5" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
                <span className="w-16 flex-shrink-0 text-[11px] font-medium text-[var(--axiom-text-secondary)]">Training</span>
                <span className="text-[12px] font-semibold text-emerald-400 flex items-center gap-1.5">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
                  Complete
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-16 flex-shrink-0 text-[11px] font-medium text-[var(--axiom-text-secondary)]">Priorities</span>
                <div className="flex-1 min-w-0"><ProgressMeter value={(done / dailyPriorities.length) * 100} color={PERSONAL_TEAL} /></div>
                <span className="w-12 text-right text-[11px] font-semibold text-[var(--axiom-text-primary)] tabular-nums">{done} / {dailyPriorities.length}</span>
              </div>
            </div>
          </Panel>

          <Panel className="min-w-0">
            <SectionTitle title="Reminders" hint="3" />
            <div className="px-4 pb-4 space-y-2">
              {reminders.map((r) => (
                <div key={r.id} className="flex items-start gap-2.5">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: r.kind === "health" ? PERSONAL_TEAL : PERSONAL_VIOLET }} />
                  <div className="min-w-0">
                    <p className="text-[11px] text-[var(--axiom-text-primary)] leading-snug">{r.text}</p>
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{r.day}</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <HabitRings />
        </div>

        {/* RIGHT — routine + events + priorities */}
        <div className="flex flex-col gap-5 min-w-0">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 min-w-0">
            <RoutineTimeline />
            <div className="flex flex-col gap-5 min-w-0">
              <UpcomingEvents />
              <DailyPriorities />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}