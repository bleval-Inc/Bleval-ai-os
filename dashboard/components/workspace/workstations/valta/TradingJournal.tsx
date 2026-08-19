"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { journalEntries, journalObservation } from "./valta-data";
import { Panel, SectionTitle, WorkspaceHeader, StatusChip, PlText, AssetChip } from "./valta-ui";

const SETUP_FIELDS: { key: string; label: string }[] = [
  { key: "entry", label: "Entry" },
  { key: "target", label: "Target" },
  { key: "stop", label: "Stop / Invalidations" },
  { key: "mgmt", label: "Trade management" },
  { key: "tp", label: "Take profit" },
  { key: "setup", label: "Setup criteria" },
  { key: "reason", label: "Reason for entry" },
  { key: "conditions", label: "Market conditions" },
  { key: "execution", label: "Execution" },
  { key: "result", label: "Result" },
  { key: "lessons", label: "Lessons" },
];

function VoiceControl() {
  // Structural placeholder. Future behaviour: speak naturally → transcribed &
  // organised into the entry. Uses existing AXIOM voice architecture; nothing
  // here modifies it.
  const [armed, setArmed] = useState(false);
  return (
    <button
      onClick={() => setArmed((a) => !a)}
      className={cn(
        "flex items-center gap-2 rounded-xl px-3.5 py-2 text-[11px] font-semibold border transition-all duration-200",
        armed
          ? "text-white border-transparent shadow-[0_0_18px_var(--axiom-accent-glow)]"
          : "text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-text-primary)]",
      )}
      style={armed ? { background: "linear-gradient(135deg,#6d7cff,#a88cff)" } : { background: "rgba(240,241,243,0.03)", borderColor: "rgba(240,241,243,0.08)" }}
      aria-pressed={armed}
      title="Voice dictation (placeholder)"
    >
      <span className="flex items-end gap-[2px] h-3.5">
        {[0, 1, 2, 3].map((b) => (
          <span
            key={b}
            className={cn("w-[2px] rounded-full", armed ? "bg-white animate-waveform" : "bg-current")}
            style={armed ? { animationDelay: `${b * 0.12}s` } : { height: 4 }}
          />
        ))}
      </span>
      <span>{armed ? "Listening…" : "Dictate entry"}</span>
    </button>
  );
}

export default function TradingJournal() {
  const [selectedId, setSelectedId] = useState(journalEntries[0].id);
  const selected = journalEntries.find((e) => e.id === selectedId) ?? journalEntries[0];

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0">
      <WorkspaceHeader
        title="Trading Journal"
        subtitle="Automated decision & activity record"
        right={<StatusChip label="Auto-record active" tone="healthy" />}
      />

      {/* Entry composer — voice/dictation entry point */}
      <Panel className="min-w-0">
        <SectionTitle title="New journal entry" hint="Speak or type — rescued automatically" />
        <div className="px-4 pb-4">
          <div className="flex items-center gap-3 rounded-xl border px-3.5 py-3" style={{ borderColor: "rgba(109,124,255,0.16)", background: "rgba(109,124,255,0.04)" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--axiom-accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><path d="M12 19v4" />
            </svg>
            <span className="flex-1 text-[12px] text-[var(--axiom-text-secondary)]">
              Describe the trade naturally — Valta Prime will transcribe and organise entry, target, stop, result and lessons.
            </span>
            <VoiceControl />
          </div>
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(280px,32%)_1fr] gap-5 items-start">
        {/* Recent trades + journal entries list */}
        <Panel className="min-w-0">
          <SectionTitle title="Recent trades" hint="Latest first" />
          <div className="px-3 pb-3 divide-y" style={{ borderColor: "rgba(240,241,243,0.04)" }}>
            {journalEntries.map((entry) => {
              const active = entry.id === selectedId;
              return (
                <button
                  key={entry.id}
                  onClick={() => setSelectedId(entry.id)}
                  className={cn("w-full text-left rounded-lg px-2.5 py-3 transition-colors", active && "bg-[var(--axiom-accent-subtle)]")}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-medium text-[var(--axiom-text-primary)]">{entry.symbol}</span>
                      <span className={cn("text-[9px] font-semibold", entry.direction === "BUY" ? "text-emerald-400" : "text-rose-400")}>{entry.direction}</span>
                    </div>
                    <PlText value={entry.pl} className="text-[11px] font-semibold" />
                  </div>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)] truncate">{entry.setup}</p>
                  <div className="flex items-center gap-2 mt-1 text-[9px] text-[var(--axiom-text-tertiary)]">
                    <span>{entry.date}</span>
                    <span>·</span>
                    <span>{entry.pl >= 0 ? "Won" : "Loss"}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Performance observation */}
          <div className="mx-3 mb-3 rounded-xl border p-3.5" style={{ borderColor: "rgba(168,140,255,0.16)", background: "rgba(168,140,255,0.05)" }}>
            <div className="text-[10px] font-semibold tracking-[0.16em] uppercase text-[var(--axiom-violet)] mb-1.5">Performance observation</div>
            <p className="text-[11px] leading-relaxed text-[var(--axiom-text-secondary)]">{journalObservation}</p>
          </div>
        </Panel>

        {/* Selected entry detail + setup information */}
        <Panel className="min-w-0">
          <SectionTitle title="Journal entry" hint={selected.date} />
          <AnimatePresence mode="wait">
            <motion.div key={selected.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18 }} className="px-4 pb-4">
              <div className="flex items-center gap-3 mb-4">
                <AssetChip label={selected.symbol} />
                <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full", selected.direction === "BUY" ? "text-emerald-400 bg-emerald-400/10" : "text-rose-400 bg-rose-400/10")}>{selected.direction}</span>
                <PlText value={selected.pl} className="text-sm font-semibold" />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mb-4">
                {SETUP_FIELDS.slice(0, 8).map((f) => (
                  <div key={f.key} className="rounded-lg border p-2.5 min-w-0" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(10,12,16,0.4)" }}>
                    <div className="text-[8px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1">{f.label}</div>
                    <div className="text-[11px] text-[var(--axiom-text-primary)] truncate">
                      {f.key === "entry" && selected.entry}
                      {f.key === "target" && selected.target}
                      {f.key === "stop" && selected.stop}
                      {f.key === "setup" && <span className="truncate-2">{selected.setup}</span>}
                      {!["entry", "target", "stop", "setup"].includes(f.key) && <span className="text-[var(--axiom-text-tertiary)]">Awaiting capture</span>}
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded-lg border p-3" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(10,12,16,0.4)" }}>
                <div className="text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)] mb-1.5">Trade notes · Lessons</div>
                <p className="text-[12px] leading-relaxed text-[var(--axiom-text-secondary)]">{selected.lessons}</p>
              </div>

              <div className="text-[10px] text-[var(--axiom-text-tertiary)] mt-4">
                Future capture: entry · target · stop · trade management · take profit · setup criteria · market conditions · execution · result · lessons
              </div>
            </motion.div>
          </AnimatePresence>
        </Panel>
      </div>
    </div>
  );
}