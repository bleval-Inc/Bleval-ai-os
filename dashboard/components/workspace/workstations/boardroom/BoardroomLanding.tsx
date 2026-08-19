"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAxiomStore } from "@/lib/store/axiom-store";
import type { SpeakerId } from "@/lib/api-types";
import { EXECUTIVES, formatDate, type BrExecutive, type BrMeeting, type BrVoiceState } from "./boardroom-data";
import { ExecutiveAvatar, MonoLabel, StatusChip } from "./boardroom-ui";

// ── Landing: pick one-or-many executives, then START MEETING ──────────
// Availability is taken from the live AXIOM store (executive board runtime
// status + real voice state). It is never fabricated.

function useLandingVoiceState(): Record<string, BrVoiceState> {
  const activeSpeaker = useAxiomStore((s) => s.activeSpeaker);
  const listeningExecutive = useAxiomStore((s) => s.listeningExecutive);
  const isSpeaking = useAxiomStore((s) => s.isSpeaking);

  const states = {} as Record<string, BrVoiceState>;
  for (const e of EXECUTIVES) {
    if (activeSpeaker === e.id) states[e.id] = "SPEAKING";
    else if (listeningExecutive === e.id) states[e.id] = "LISTENING";
    else if (isSpeaking) states[e.id] = "IDLE";
    else states[e.id] = "IDLE";
  }
  return states;
}

export default function BoardroomLanding({
  selected,
  onToggle,
  onStart,
  pastMeetings,
}: {
  selected: SpeakerId[];
  onToggle: (id: SpeakerId) => void;
  onStart: () => void;
  pastMeetings: BrMeeting[];
}) {
  const executiveBoard = useAxiomStore((s) => s.executiveBoard);
  const voiceStates = useLandingVoiceState();

  return (
    <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar">
      <div className="max-w-5xl mx-auto px-5 md:px-8 py-10 md:py-14">
        {/* Identity */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: "easeOut" }}>
          <MonoLabel>AXIOM // COMMAND</MonoLabel>
          <h1 className="mt-3 text-3xl md:text-4xl font-light tracking-tight text-[var(--axiom-text-primary)]">
            Boardroom
          </h1>
          <p className="mt-1.5 text-[13px] text-[var(--axiom-text-tertiary)]">
            Executive command &amp; collaboration — meet with your executives, review decisions, delegate work.
          </p>
        </motion.div>

        {/* Executive selection */}
        <div className="mt-9">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] font-semibold tracking-[0.16em] text-[var(--axiom-text-secondary)] uppercase">
              Select executives
            </h2>
            <span className="font-mono text-[9px] text-[var(--axiom-text-tertiary)]">{selected.length} / {EXECUTIVES.length}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {EXECUTIVES.map((exec, i) => (
              <ExecutiveCard
                key={exec.id}
                exec={exec}
                index={i}
                selected={selected.includes(exec.id)}
                onToggle={() => onToggle(exec.id)}
                voiceState={voiceStates[exec.id] ?? "IDLE"}
                runtimeStatus={executiveBoard?.[exec.id]?.status}
              />
            ))}
          </div>
        </div>

        {/* Past meetings */}
        {pastMeetings.length > 0 && (
          <div className="mt-10">
            <h2 className="text-[11px] font-semibold tracking-[0.16em] text-[var(--axiom-text-secondary)] uppercase mb-3">
              Past meetings
            </h2>
            <div className="flex flex-wrap gap-2">
              {pastMeetings.slice(0, 5).map((m) => (
                <div key={m.id} className="px-3 py-1.5 rounded-lg border border-[var(--axiom-border-hover)] bg-white/[0.02] text-[10px] text-[var(--axiom-text-secondary)]">
                  <span className="text-[var(--axiom-text-primary)]">{m.title}</span> · {formatDate(m.startedAt)} · {m.participants.length} exec
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Primary action */}
        <div className="mt-10 flex items-center justify-end gap-3">
          <span className="hidden md:block font-mono text-[9px] text-[var(--axiom-text-tertiary)]">
            {selected.length === 0 ? "Select at least one executive" : selected.length === 1 ? "One-on-one session" : `${selected.length}-executive session`}
          </span>
          <button
            onClick={onStart}
            disabled={selected.length === 0}
            className={cn(
              "inline-flex items-center gap-2.5 px-6 py-3 rounded-xl text-[12px] font-semibold text-white tracking-wide transition-all duration-150",
              "disabled:opacity-35 disabled:cursor-not-allowed active:scale-[0.98]",
            )}
            style={{
              background: selected.length ? "linear-gradient(135deg, var(--axiom-accent), var(--axiom-violet))" : "var(--axiom-bg-elevated)",
              boxShadow: selected.length ? "0 8px 28px -8px var(--axiom-accent-glow)" : undefined,
            }}
          >
            <EntranceIcon />
            START MEETING
          </button>
        </div>
      </div>
    </div>
  );
}

function ExecutiveCard({
  exec,
  index,
  selected,
  onToggle,
  voiceState,
  runtimeStatus,
}: {
  exec: BrExecutive;
  index: number;
  selected: boolean;
  onToggle: () => void;
  voiceState: BrVoiceState;
  runtimeStatus?: "running" | "stopped" | "error";
}) {
  const availability =
    runtimeStatus === "running" ? "RUNNING" : runtimeStatus === "error" ? "ERROR" : runtimeStatus === "stopped" ? "STOPPED" : "STANDBY";

  return (
    <motion.button
      onClick={onToggle}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut", delay: index * 0.05 }}
      role="checkbox"
      aria-checked={selected}
      className={cn(
        "relative min-w-0 text-left p-4 rounded-2xl border transition-all duration-200",
        selected
          ? "border-[#6d7cff]/35 bg-[#6d7cff]/[0.05]"
          : "border-[var(--axiom-border-hover)] hover:bg-white/[0.02] hover:border-[var(--axiom-border)]",
      )}
    >
      {/* Select indicator */}
      <span
        className={cn(
          "absolute top-3.5 right-3.5 w-4 h-4 rounded-full border transition-colors",
          selected ? "border-[var(--axiom-accent)] bg-[var(--axiom-accent)]" : "border-[var(--axiom-border-hover)]",
        )}
      >
        {selected && (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="absolute inset-0 m-auto">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </span>

      <div className="flex items-center gap-3">
        <ExecutiveAvatar exec={exec} active={selected} size="lg" />
        <div className="min-w-0">
          <div className="text-sm font-medium text-[var(--axiom-text-primary)] tracking-wide">{exec.name}</div>
          <div className="text-[10px] text-[var(--axiom-text-tertiary)] leading-tight mt-0.5">
            {exec.role}
          </div>
          <div className="text-[9px] uppercase tracking-[0.14em] text-[var(--axiom-text-tertiary)]/80 mt-0.5">{exec.org}</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <StatusChip state={voiceState} label={voiceState === "IDLE" ? availability : voiceState} />
        <span className="flex items-center gap-1.5 font-mono text-[9px] text-[var(--axiom-text-tertiary)]">
          <span className={cn("w-1.5 h-1.5 rounded-full", selected ? exec.dot : "bg-[var(--axiom-text-tertiary)]/40", selected && "animate-pulse")} />
          {selected ? "IN SESSION" : "TAP TO ADD"}
        </span>
      </div>
    </motion.button>
  );
}

function EntranceIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}