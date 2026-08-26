"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { weekEvents, scheduleKindColor, todaysRoutine, routineTypeColor, type CalendarEvent } from "./personal-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip } from "./personal-ui";

const VIEWS = ["Day", "Week", "Month"] as const;
const KIND_LABELS: { kind: CalendarEvent["kind"]; label: string }[] = [
  { kind: "event", label: "Event" },
  { kind: "task", label: "Task" },
  { kind: "training", label: "Training" },
  { kind: "learning", label: "Learning" },
  { kind: "meeting", label: "Meeting" },
  { kind: "reminder", label: "Reminder" },
];
const scheduleKindLabel = (k: CalendarEvent["kind"]) => KIND_LABELS.find((x) => x.kind === k)?.label ?? k;

// Month grid — a compact executive overview. Focused around the current demo week.
function MonthView() {
  const dayMap = useMemo(() => new Map(weekEvents.map((e) => [e.day, e])), []);
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  return (
    <div>
      <div className="grid grid-cols-7 gap-1.5 mb-1.5">
        {["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"].map((h) => (
          <div key={h} className="text-center text-[9px] font-semibold tracking-[0.16em] text-[var(--axiom-text-tertiary)]">{h}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1.5">
        {Array.from({ length: 6 }, (_, i) => <div key={`b${i}`} className="h-12 rounded-lg border border-transparent" />)}
        {days.map((d) => {
          const ev = dayMap.get(d);
          return (
            <div
              key={d}
              className={cn("h-12 rounded-lg border p-1 flex flex-col items-start overflow-hidden", ev ? "" : "hover:bg-[var(--axiom-bg-glass-hover)]")}
              style={{
                borderColor: ev ? `${scheduleKindColor[ev.kind]}40` : "rgba(240,241,243,0.05)",
                background: ev ? `${scheduleKindColor[ev.kind]}14` : "rgba(10,12,16,0.35)",
              }}
            >
              <span className="text-[10px] text-[var(--axiom-text-secondary)] tabular-nums">{d}</span>
              {ev && (
                <span className="text-[8px] leading-tight text-[var(--axiom-text-primary)] truncate w-full mt-0.5">{ev.start} {ev.title}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function WeekView() {
  return (
    <div>
      <div className="grid grid-cols-7 gap-1.5 mb-1.5">
        {["MON 17", "TUE 18", "WED 19", "THU 20", "FRI 21", "SAT 22", "SUN 23"].map((h, i) => (
          <div key={h} className={cn("text-center text-[9px] font-semibold tracking-[0.1em]", i === 0 ? "text-[var(--axiom-teal)]" : "text-[var(--axiom-text-tertiary)]")} style={i === 0 ? { color: "#2dd4bf" } : {}}>{h}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1.5">
        {(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const).map((name) => {
          const dayNumbers: Record<string, number> = { Mon: 17, Tue: 18, Wed: 19, Thu: 20, Fri: 21, Sat: 22, Sun: 23 };
          const dayEvents = weekEvents.filter((e) => dayNumbers[name] === e.day);
          return (
            <div key={name} className="rounded-xl border border-[rgba(240,241,243,0.06)] bg-[rgba(10,12,16,0.35)] p-2 min-h-[180px] flex flex-col gap-1.5">
              {dayEvents.length === 0 && <span className="text-[9px] text-[var(--axiom-text-tertiary)]/50">No events</span>}
              {dayEvents.map((e) => (
                <div key={e.id} className="rounded-md px-2 py-1.5" style={{ background: `${scheduleKindColor[e.kind]}18`, border: `1px solid ${scheduleKindColor[e.kind]}33` }}>
                  <div className="text-[9px] font-semibold text-[var(--axiom-text-primary)] leading-tight">{e.title}</div>
                  <div className="text-[8px] text-[var(--axiom-text-secondary)]">{e.start} · {e.durationMin}m</div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DayView() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 min-w-0">
      <Panel className="min-w-0">
        <SectionTitle title="Today" hint="Mon 17 Aug · routine" />
        <div className="px-4 pb-4 relative pl-4 border-l ml-4 mr-0" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
          {todaysRoutine.map((b) => {
            const color = routineTypeColor[b.type];
            return (
              <div key={b.id} className="relative pb-4 last:pb-0">
                <span className="absolute -left-[21px] top-1 w-[7px] h-[7px] rounded-full border-2 border-[var(--axiom-bg-base)]" style={{ background: color }} />
                <div className="flex items-center gap-3">
                  <span className="w-10 text-[11px] font-semibold text-[var(--axiom-text-secondary)] tabular-nums flex-shrink-0">{b.time}</span>
                  <div className="min-w-0 flex-1">
                    <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{b.label}</span>
                    {b.note && <span className="block text-[10px] text-[var(--axiom-text-tertiary)] truncate">{b.note}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
      <Panel className="min-w-0">
        <SectionTitle title="Events & blocks" hint="Rest of week" />
        <div className="px-4 pb-4 space-y-2">
          {weekEvents.filter((e) => e.day !== 17).map((e) => (
            <div key={e.id} className="flex items-center gap-3 rounded-lg px-2.5 py-2 border" style={{ borderColor: `${scheduleKindColor[e.kind]}30`, background: "rgba(10,12,16,0.4)" }}>
              <span className="w-1.5 h-8 rounded-full flex-shrink-0" style={{ background: scheduleKindColor[e.kind] }} />
              <div className="min-w-0 flex-1">
                <span className="text-[12px] text-[var(--axiom-text-primary)] block truncate">{e.title}</span>
                <span className="text-[10px] text-[var(--axiom-text-secondary)]">{e.start} · {e.durationMin} min</span>
              </div>
              <span className="text-[9px] uppercase tracking-wider text-[var(--axiom-text-tertiary)] flex-shrink-0">{scheduleKindLabel(e.kind)}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

export default function Schedule() {
  const [view, setView] = useState<(typeof VIEWS)[number]>("Week");

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="Schedule"
        subtitle="Calendar & routine · coordinated by Yamako"
        right={
          <div className="flex items-center gap-1 rounded-full border border-[var(--axiom-border-hover)] p-1">
            {VIEWS.map((v) => (
              <button key={v} onClick={() => setView(v)} className={cn("rounded-full px-3 py-1 text-[10px] font-semibold transition-colors", view === v ? "text-white" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)]")} style={view === v ? { background: "linear-gradient(135deg,#6d7cff,#a88cff)" } : {}}>
                {v}
              </button>
            ))}
          </div>
        }
      />

      <div className="flex flex-wrap gap-3 text-[10px] text-[var(--axiom-text-secondary)]">
        {KIND_LABELS.map(({ kind, label }) => (
          <span key={kind} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: scheduleKindColor[kind] }} /> {label}
          </span>
        ))}
        <StatusChip label="Yamako monitoring" tone="active" />
      </div>

      <Panel className="min-w-0">
        <motion.div key={view} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="px-4 py-4">
          {view === "Day" && <DayView />}
          {view === "Week" && <WeekView />}
          {view === "Month" && <MonthView />}
        </motion.div>
      </Panel>
    </div>
  );
}