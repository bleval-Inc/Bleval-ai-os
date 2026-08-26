"use client";

import { motion } from "framer-motion";
import { learningSubjects, learningGoals } from "./personal-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip } from "./personal-ui";
import { ProgressRing, ProgressMeter } from "./personal-charts";
import { PERSONAL_VIOLET, PERSONAL_TEAL } from "./types";

const BOOKS = [
  { title: "Deep Work", author: "Cal Newport", progress: 70, note: "Strongest method resource" },
  { title: "The Mental Game of Trading", author: "Jared Tendler", progress: 45, note: "Stage: performance reviewing" },
  { title: "Make It Stick", author: "Brown · Roediger", progress: 30, note: "Retrieval practice" },
];

export default function Learning() {
  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="Learning"
        subtitle="Personal learning environment · Yamako guided"
        right={<StatusChip label="Path on track" tone="active" />}
      />

      {/* The four questions learning must answer */}
      <Panel className="min-w-0">
        <SectionTitle title="Your learning core" />
        <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {[
            { q: "What am I learning?", a: "Trading psychology, deep work, learning science, leadership systems" },
            { q: "Why am I learning it?", a: "To execute without bias, produce deep output, and scale decisions" },
            { q: "What am I weak at?", a: "Riding winners, spaced retrieval, delegation" },
            { q: "What should I learn next?", a: "Synthesising evidence into operating principles" },
          ].map((c) => (
            <div key={c.q} className="rounded-xl border p-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(10,12,16,0.4)" }}>
              <div className="text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-violet)] mb-1.5" style={{ color: PERSONAL_VIOLET }}>{c.q}</div>
              <p className="text-[11px] text-[var(--axiom-text-secondary)] leading-snug">{c.a}</p>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(280px,32%)_1fr] gap-5 items-start">
        {/* Subjects */}
        <div className="flex flex-col gap-5 min-w-0">
          <SectionTitle title="Subjects" className="px-0 mb-2" />
          <div className="flex flex-col gap-3">
            {learningSubjects.map((s, i) => (
              <motion.div key={s.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.05 }} className="rounded-2xl border p-3.5" style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(15,18,24,0.42)" }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] font-semibold text-[var(--axiom-text-primary)]">{s.name}</span>
                  <span className="text-[10px] font-semibold text-[var(--axiom-text-secondary)] tabular-nums">{s.progress}%</span>
                </div>
                <p className="text-[10px] text-[var(--axiom-text-tertiary)] mb-2">{s.why}</p>
                <ProgressMeter value={s.progress} color={PERSONAL_TEAL} />
                <div className="mt-2.5 text-[10px] text-[var(--axiom-text-secondary)]">
                  <span className="text-[var(--axiom-text-tertiary)]">Latest: </span>{s.resource}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-5 min-w-0">
          <Panel className="min-w-0">
            <SectionTitle title="Next up" hint="Yamako recommendation" />
            <div className="px-4 pb-4 space-y-3">
              {learningSubjects.slice(0, 2).map((s) => (
                <div key={s.id} className="rounded-xl border p-3" style={{ borderColor: "rgba(45,212,191,0.14)", background: "rgba(45,212,191,0.04)" }}>
                  <div className="text-[10px] font-semibold text-[var(--axiom-text-primary)] mb-1" style={{ color: PERSONAL_TEAL }}>Weakness: {s.weakAt}</div>
                  <p className="text-[11px] text-[var(--axiom-text-secondary)]">Next: {s.next}</p>
                </div>
              ))}
            </div>
          </Panel>

          <Panel className="min-w-0">
            <SectionTitle title="Books" hint="Reading" />
            <div className="px-4 pb-4 space-y-3">
              {BOOKS.map((b) => (
                <div key={b.title} className="flex items-center gap-3">
                  <ProgressRing value={b.progress} size={48} label={`${b.progress}%`} />
                  <div className="min-w-0 flex-1">
                    <span className="block text-[12px] text-[var(--axiom-text-primary)] truncate">{b.title}</span>
                    <span className="block text-[10px] text-[var(--axiom-text-tertiary)]">{b.author} · {b.note}</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel className="min-w-0">
            <SectionTitle title="Learning goals" hint="Progress" />
            <div className="px-4 pb-4 space-y-3">
              {learningGoals.map((g) => (
                <div key={g.id}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[12px] text-[var(--axiom-text-primary)]">{g.label}</span>
                    <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{g.progress}%</span>
                  </div>
                  <ProgressMeter value={g.progress} color={PERSONAL_VIOLET} />
                  <span className="text-[9px] text-[var(--axiom-text-tertiary)]">Due {g.due}</span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}