"use client";

import { useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAxiomStore } from "@/lib/store/axiom-store";
import { cn } from "@/lib/utils";
import { personalData, type Habit } from "./personal-data";

// PERSONAL identity — calm emerald/teal. Inside the AXIOM dark-glass system
// but reads as a quiet, wellness-driven environment (Yamako's personal ops).
const identity = "linear-gradient(135deg, #34d399 0%, #2dd4bf 100%)";
const ACCENT = "#34d399";

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const WEEKDAY = ["M", "T", "W", "T", "F", "S", "S"];

function PanelTitle({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex items-center justify-between mb-2 flex-shrink-0">
      <h4 className="text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)]">
        {title}
      </h4>
      {hint && <span className="text-[10px] text-[var(--axiom-text-tertiary)]/70 font-medium">{hint}</span>}
    </div>
  );
}

const panelShell = {
  borderColor: "rgba(240,241,243,0.06)",
  background: "rgba(13,16,20,0.4)",
};

/* ---------- CALENDAR ---------- */
function CalendarPanel() {
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const { baseYear, baseMonth } = personalData;

  // The month currently on screen (handles prev/next navigation).
  const year = useMemo(() => {
    const y = new Date(baseYear, baseMonth, 1);
    const shifted = new Date(y.getFullYear(), y.getMonth() + offset, 1);
    return shifted;
  }, [baseYear, baseMonth, offset]);

  const yearNum = year.getFullYear();
  const monthNum = year.getMonth();
  const daysInMonth = new Date(yearNum, monthNum + 1, 0).getDate();
  const firstDow = (new Date(yearNum, monthNum, 1).getDay() + 6) % 7; // Mon=0
  const isCurrent = offset === 0;
  const todayReal = (() => {
    const t = new Date();
    return { y: t.getFullYear(), m: t.getMonth(), d: t.getDate() };
  })();
  const isTodayVisible = isCurrent && todayReal.y === baseYear && todayReal.m === baseMonth;

  const cells: (number | null)[] = [
    ...Array.from({ length: firstDow }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const dot = (d: number) =>
    isTodayVisible && d === todayReal.d ? "bg-emerald-400 text-[#04120a]" : "text-[var(--axiom-text-secondary)]";

  return (
    <section className="rounded-2xl p-3.5 border flex flex-col min-h-0" style={panelShell}>
      <PanelTitle title="Calendar" hint={`${MONTHS[monthNum]} ${yearNum}`} />

      {/* Month nav */}
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <div className="flex items-center gap-0.5">
          <IconBtn label="Previous month" onClick={() => setOffset((o) => o - 1)} path="M15 18l-6-6 6-6" />
          <IconBtn label="Next month" onClick={() => setOffset((o) => o + 1)} path="M9 18l6-6-6-6" />
        </div>
        <button
          onClick={() => { setOffset(0); setSelected(null); }}
          className="px-2 py-0.5 rounded-md text-[10px] font-semibold text-[var(--axiom-text-secondary)] hover:text-emerald-300 transition-colors"
          style={{ border: "1px solid rgba(52,211,153,0.18)", background: "rgba(52,211,153,0.06)" }}
        >
          Today
        </button>
      </div>

      {/* Weekday header */}
      <div className="grid grid-cols-7 gap-0.5 mb-1 flex-shrink-0">
        {WEEKDAY.map((w, i) => (
          <span key={i} className="text-center text-[9px] font-semibold uppercase tracking-wide text-[var(--axiom-text-tertiary)]/80">
            {w}
          </span>
        ))}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 gap-0.5 flex-1 min-h-0 auto-rows-fr">
        {cells.map((d, i) => {
          if (d === null) {
            return <span key={`b-${i}`} />;
          }
          const active = selected === d;
          const hmm = `${monthNum}${yearNum}${d}`;
          const effective =
            isTodayVisible && d === todayReal.d && selected === null
              ? todayReal.d
              : selected;
          const isEffective = effective === d;
          return (
            <button
              key={d}
              onClick={() => setSelected(d)}
              aria-label={hmm}
              className={cn(
                "flex items-center justify-center rounded-md text-[11px] font-medium transition-colors",
                !isEffective && "text-[var(--axiom-text-secondary)] hover:bg-white/5",
                "min-w-0",
                active && "outline outline-1 outline-emerald-400/40",
              )}
              style={isEffective ? { background: identity, color: "#04120a", boxShadow: "0 0 10px -2px rgba(52,211,153,0.6)" } : undefined}
            >
              <span className={cn(!isEffective && dot(d))}>{d}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function IconBtn({ label, onClick, path }: { label: string; onClick: () => void; path: string }) {
  return (
    <motion.button
      whileHover={{ scale: 1.08 }}
      whileTap={{ scale: 0.94 }}
      onClick={onClick}
      aria-label={label}
      className="w-6 h-6 flex items-center justify-center rounded-md text-[var(--axiom-text-tertiary)] hover:text-emerald-300 hover:bg-white/5 transition-colors"
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d={path} />
      </svg>
    </motion.button>
  );
}

/* ---------- TODAY'S SCHEDULE ---------- */
function SchedulePanel() {
  const { schedule, now } = personalData;
  // Last item whose start <= now is the "current" one.
  const activeIdx = schedule.reduce((acc, item, i) => (item.time <= now ? i : acc), -1);

  return (
    <section className="rounded-2xl p-3.5 border flex flex-col min-h-0" style={panelShell}>
      <PanelTitle title="Today's Schedule" hint={`Now ${now}`} />

      <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar pr-1 -mr-1">
        <div className="relative flex flex-col">
          {/* Timeline rail */}
          <div className="absolute left-[52px] top-1 bottom-1 w-px bg-white/6" />
          {schedule.map((item, i) => {
            const past = i < activeIdx;
            const current = i === activeIdx;
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 + i * 0.06, ease: "easeOut" }}
                className="relative flex items-center gap-2.5 py-1.5"
              >
                <span
                  className={cn(
                    "w-[38px] text-right text-[11px] font-medium tabular-nums flex-shrink-0",
                    current ? "text-emerald-300" : past ? "text-[var(--axiom-text-tertiary)]/60" : "text-[var(--axiom-text-secondary)]",
                  )}
                >
                  {item.time}
                </span>
                {/* Dot */}
                <span
                  className={cn(
                    "w-2 h-2 rounded-full flex-shrink-0",
                    current ? "bg-emerald-400" : past ? "bg-emerald-400/40" : "bg-white/25",
                  )}
                  style={current ? { boxShadow: "0 0 8px rgba(52,211,153,0.9)" } : undefined}
                />
                <span
                  className={cn(
                    "text-[12px] min-w-0 truncate",
                    current ? "text-[var(--axiom-text-primary)] font-semibold" : past ? "text-[var(--axiom-text-tertiary)]/70" : "text-[var(--axiom-text-secondary)]",
                  )}
                >
                  {item.label}
                </span>
                {current && (
                  <span className="ml-auto flex-shrink-0 text-[9px] font-bold tracking-widest text-emerald-300 uppercase bg-emerald-400/10 rounded px-1.5 py-0.5">
                    Now
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ---------- HABIT TRACKER ---------- */
const WEEK_SHORT = ["M", "T", "W", "T", "F", "S", "S"];

function HabitRow({ habit, index }: { habit: Habit; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: 0.35 + index * 0.05, ease: "easeOut" }}
      className="flex items-center gap-2.5 py-1"
    >
      {/* Toggle */}
      <span
        className={cn(
          "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 border",
          habit.done ? "border-transparent" : "border-white/15",
        )}
        style={habit.done ? { background: identity } : undefined}
      >
        {habit.done && (
          <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#04120a" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6L9 17l-5-5" />
          </svg>
        )}
      </span>
      <span className="text-[12px] min-w-0 flex-1 truncate text-[var(--axiom-text-secondary)]">{habit.label}</span>
      <span className="text-[10px] font-medium tabular-nums text-emerald-400/90 flex-shrink-0">{habit.streak}d</span>
      {/* Mon–Sun progress */}
      <span className="flex items-center gap-1 flex-shrink-0">
        {WEEK_SHORT.map((w, i) => (
          <span key={i} className="flex flex-col items-center gap-1">
            <span
              className="w-2.5 h-2.5 rounded-sm"
              style={{ background: habit.week[i] ? ACCENT : "rgba(240,241,243,0.12)" }}
            />
            <span className="text-[8px] text-[var(--axiom-text-tertiary)]/70">{w}</span>
          </span>
        ))}
      </span>
    </motion.div>
  );
}

function HabitPanel() {
  return (
    <section className="rounded-2xl p-3.5 border flex flex-col min-h-0" style={panelShell}>
      <PanelTitle title="Habit Tracker" hint={`${personalData.habits.filter((h) => h.done).length}/${personalData.habits.length} done`} />
      <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar pr-1 -mr-1 flex flex-col justify-center">
        {personalData.habits.map((h, i) => (
          <HabitRow key={h.id} habit={h} index={i} />
        ))}
      </div>
    </section>
  );
}

/* ---------- WEATHER ---------- */
function WeatherIcon() {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className="relative w-16 h-16 flex-shrink-0"
      animate={reduce ? undefined : { y: [0, -3, 0] }}
      transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
      aria-hidden
    >
      <span className="absolute top-0 right-0 w-6 h-6 rounded-full" style={{ background: "radial-gradient(circle at 35% 35%, #ffd76a, #ffb347)", boxShadow: "0 0 18px rgba(255,200,90,0.8)" }} />
      <svg width="44" height="44" viewBox="0 0 24 24" fill="white" className="absolute bottom-0 left-0 opacity-90" aria-hidden>
        <path d="M6 17h11a4 4 0 0 0 .9-7.9 5.5 5.5 0 0 0-10.7-1.4A4.6 4.6 0 0 0 6 17z" />
      </svg>
    </motion.div>
  );
}

function WeatherPanel() {
  const { location, temperature, condition, high, low } = personalData;
  return (
    <section
      className="rounded-2xl p-3.5 border flex flex-col min-h-0 overflow-hidden relative"
      style={{
        borderColor: "rgba(52,211,153,0.14)",
        background: "linear-gradient(145deg, rgba(52,211,153,0.05) 0%, rgba(13,16,20,0.4) 100%)",
      }}
    >
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-2/3"
        style={{ background: "linear-gradient(90deg, transparent, rgba(52,211,153,0.6), transparent)" }}
      />
      <PanelTitle title="Weather" hint={location} />

      <div className="flex-1 flex items-center gap-3 min-h-0">
        <WeatherIcon />
        <div className="min-w-0">
          <div className="flex items-baseline gap-1.5">
            <span className="text-[34px] leading-none font-semibold text-[var(--axiom-text-primary)] tabular-nums">
              {temperature}
            </span>
            <span className="text-[16px] font-medium text-[var(--axiom-text-tertiary)]">°C</span>
          </div>
          <p className="text-[12px] font-medium text-[var(--axiom-text-secondary)]">{condition}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-[11px] font-medium tabular-nums text-amber-300/90">H {high}°</span>
            <span className="text-[var(--axiom-text-tertiary)]/50">·</span>
            <span className="text-[11px] font-medium tabular-nums text-sky-300/80">L {low}°</span>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------- CONSOLE SHELL ---------- */
export default function PersonalConsole() {
  const router = useRouter();
  const { setActiveWorkstation } = useAxiomStore();

  const openWorkstation = () => {
    setActiveWorkstation("personal");
    router.push("/personal");
  };

  return (
    <div
      className="relative w-full h-full min-h-0 rounded-3xl overflow-hidden backdrop-blur-xl flex flex-col"
      style={{
        background: `
          radial-gradient(ellipse at top left, rgba(52,211,153,0.08) 0%, transparent 55%),
          radial-gradient(ellipse at bottom right, rgba(45,212,191,0.06) 0%, transparent 50%),
          linear-gradient(150deg, rgba(10,14,12,0.6) 0%, rgba(13,18,16,0.6) 100%)
        `,
        border: "1px solid rgba(52,211,153,0.15)",
        boxShadow: `
          0 8px 40px -12px rgba(52,211,153,0.16),
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
      <div className="relative flex items-center justify-between px-5 pt-4 pb-3 border-b border-[rgba(52,211,153,0.12)] z-10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-[#04120a] relative overflow-hidden"
            style={{ background: identity, boxShadow: "0 0 24px -4px rgba(52,211,153,0.5)" }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/25 to-transparent" />
            {/* Personal mark */}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="relative">
              <circle cx="12" cy="8" r="3.5" />
              <path d="M5 20v-1a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v1" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-tight text-[var(--axiom-text-primary)]">
              {personalData.identity}
            </h3>
            <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">
              Personal Operations
            </p>
          </div>
        </div>

        <motion.button
          onClick={openWorkstation}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-[var(--axiom-text-secondary)] hover:text-emerald-300 transition-colors flex-shrink-0"
          style={{ border: "1px solid rgba(52,211,153,0.15)", background: "rgba(52,211,153,0.05)" }}
          aria-label="Open Personal workstation"
        >
          <span>Workstation</span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17L17 7M7 7h10v10" />
          </svg>
        </motion.button>
      </div>

      {/* Content — 2×2 panel grid; self-scrolls as a safety net on short viewports */}
      <div className="relative flex-1 min-h-0 overflow-y-auto hide-scrollbar px-5 py-4 z-10">
        <div className="h-full min-h-0 grid grid-cols-1 md:grid-cols-2 md:grid-rows-2 gap-3">
          <CalendarPanel />
          <SchedulePanel />
          <HabitPanel />
          <WeatherPanel />
        </div>
      </div>
    </div>
  );
}