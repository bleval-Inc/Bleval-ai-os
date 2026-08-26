"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAxiomStore } from "@/lib/store/axiom-store";
import type { SpeakerId } from "@/lib/api-types";
import { requestSpeak } from "@/lib/voice/speech-arbiter";
import { formatDuration, getExecutive, uid, type BrMeeting, type BrVoiceState } from "./boardroom-data";
import { ExecutiveAvatar, IconButton, MonoLabel, StatusChip, Waveform } from "./boardroom-ui";
import BoardroomNotes from "./BoardroomNotes";
import BoardroomShare from "./BoardroomShare";

// ── Active meeting ────────────────────────────────────────────────────
// Three-region layout: LEFT participants · CENTER conversation · RIGHT notes.
// Voice states are driven by the AXIOM speech arbiter (one speaker at a time)
// and the live store — never fabricated.

interface MeetingProps {
  meeting: BrMeeting;
  patch: (updater: (m: BrMeeting) => BrMeeting) => void;
  onEnd: () => void;
}

export default function BoardroomMeeting({ meeting, patch, onEnd }: MeetingProps) {
  const activeSpeaker = useAxiomStore((s) => s.activeSpeaker);
  const listeningExecutive = useAxiomStore((s) => s.listeningExecutive);
  const isAwake = useAxiomStore((s) => s.isAwake);
  const setVoiceActive = useAxiomStore((s) => s.setVoiceActive);

  const [thinkingId, setThinkingId] = useState<SpeakerId | null>(null);
  const [connecting, setConnecting] = useState(true);
  const [elapsed, setElapsed] = useState("");
  const [shareOpen, setShareOpen] = useState(false);
  const [notesOpen, setNotesOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [voiceOn, setVoiceOn] = useState(isAwake);
  const [micMuted, setMicMuted] = useState(false);

  const briefIdx = useRef<Record<string, number>>({});

  // CONNECTING → ready window as the session initialises
  useEffect(() => {
    const t = setTimeout(() => setConnecting(false), 900);
    return () => clearTimeout(t);
  }, []);

  // Live duration ticker
  useEffect(() => {
    const tick = () => setElapsed(formatDuration(meeting.startedAt, Date.now()));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [meeting.startedAt]);

  const voiceState = (id: SpeakerId): BrVoiceState => {
    if (connecting) return "CONNECTING";
    if (activeSpeaker === id) return "SPEAKING";
    if (listeningExecutive === id) return "LISTENING";
    if (thinkingId === id) return "THINKING";
    return "IDLE";
  };

  // Founder prompts an executive to speak (real TTS through the arbiter).
  const askExecutive = async (id: SpeakerId) => {
    if (!voiceOn || thinkingId) return;
    const exec = getExecutive(id);
    const i = briefIdx.current[id] ?? 0;
    const line = exec.briefings[i % exec.briefings.length];
    briefIdx.current[id] = i + 1;
    setThinkingId(id);
    patch((m) => ({ ...m, turns: [...m.turns, { id: uid("turn"), speaker: id, text: line, at: Date.now() }] }));
    try {
      await requestSpeak(id, line, "normal");
    } finally {
      setThinkingId(null);
    }
  };

  const toggleVoice = () => {
    const next = !voiceOn;
    setVoiceOn(next);
    setVoiceActive(next);
  };

  const focusId: SpeakerId = activeSpeaker ?? meeting.turns[meeting.turns.length - 1]?.speaker ?? meeting.participants[0] ?? "jenson";
  const focus = getExecutive(focusId);

  return (
    <div className="relative flex-1 min-h-0 flex flex-col">
      {/* Control bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--axiom-border)] flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <MonoLabel>BOARDROOM</MonoLabel>
          <span className="text-[10px] text-[var(--axiom-accent)] font-mono">{elapsed}</span>
          <span className="hidden sm:inline text-[10px] text-[var(--axiom-text-tertiary)] truncate">
            {meeting.participants.length} in session
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <IconButton label={micMuted ? "Unmute" : "Mute"} active={!micMuted} onClick={() => setMicMuted((m) => !m)}>
            <MicIcon off={micMuted} />
            <span className="text-[8px] font-medium tracking-wide">{micMuted ? "MUTED" : "MIC"}</span>
          </IconButton>
          <IconButton label={voiceOn ? "Voice off" : "Voice on"} active={voiceOn} onClick={toggleVoice}>
            <VoiceIcon off={!voiceOn} />
            <span className="text-[8px] font-medium tracking-wide">VOICE</span>
          </IconButton>
          <IconButton label="Share" active={shareOpen} onClick={() => setShareOpen((s) => !s)}>
            <ShareIcon />
            <span className="text-[8px] font-medium tracking-wide">SHARE</span>
          </IconButton>
          <IconButton label="Notes" active={notesOpen} onClick={() => setNotesOpen((n) => !n)}>
            <NotesIcon />
            <span className="text-[8px] font-medium tracking-wide">NOTES</span>
          </IconButton>
          <IconButton label="More" active={moreOpen} onClick={() => setMoreOpen((m) => !m)}>
            <MoreIcon />
            <span className="text-[8px] font-medium tracking-wide">MORE</span>
          </IconButton>
        </div>
      </div>

      {/* Three-region body */}
      <div className="flex-1 min-h-0 flex">
        {/* LEFT — participants */}
        <aside className="hidden md:flex w-56 flex-shrink-0 border-r border-[var(--axiom-border)] flex-col min-h-0">
          <div className="px-4 py-3 border-b border-[var(--axiom-border)] flex-shrink-0">
            <MonoLabel>PARTICIPANTS</MonoLabel>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar p-2 space-y-1">
            <ParticipantRow id="axiom" state={activeSpeaker === "axiom" ? "SPEAKING" : isAwake ? "LISTENING" : "IDLE"} isHost />
            {meeting.participants.map((id) => (
              <ParticipantRow key={id} id={id} state={voiceState(id)} />
            ))}
          </div>
          <MoreMenu open={moreOpen} onEnd={onEnd} onDismiss={() => setMoreOpen(false)} />
        </aside>

        {/* CENTER — conversation */}
        <main className="flex-1 min-w-0 flex flex-col min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar flex flex-col items-center justify-center px-6 py-6">
            {/* Focused executive */}
            <motion.div key={focusId} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.25, ease: "easeOut" }} className="flex flex-col items-center text-center">
              <ExecutiveAvatar exec={focus} active={voiceState(focusId) === "SPEAKING"} size="lg" />
              <h2 className="mt-3 text-lg font-light text-[var(--axiom-text-primary)] tracking-wide">{focus.name}</h2>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)]">
                {focus.role} · {focus.org}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <StatusChip state={voiceState(focusId)} />
              </div>
              <div className="mt-4">
                <Waveform active={voiceState(focusId) === "SPEAKING"} color="var(--axiom-accent)" />
              </div>
            </motion.div>

            {/* Prompt controls */}
            <div className="mt-8 flex items-center gap-2 flex-wrap justify-center">
              {meeting.participants.map((id) => (
                <button
                  key={id}
                  onClick={() => askExecutive(id)}
                  disabled={!voiceOn || !!thinkingId}
                  className="px-3 py-1.5 rounded-lg border border-[var(--axiom-border-hover)] text-[10px] text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-text-primary)] hover:bg-white/5 disabled:opacity-35 transition-colors"
                >
                  ASK {getExecutive(id).name.toUpperCase()}
                </button>
              ))}
              {!voiceOn && <span className="text-[9px] text-[var(--axiom-text-tertiary)]">Voice is off</span>}
            </div>
          </div>

          {/* Transcript */}
          <div className="flex-shrink-0 border-t border-[var(--axiom-border)] px-5 py-3 max-h-40 overflow-y-auto hide-scrollbar space-y-1.5">
            {meeting.turns.length === 0 ? (
              <p className="text-[10px] text-[var(--axiom-text-tertiary)]/70 text-center py-2">
                The Founder speaks; executives respond one at a time. Use ASK to bring an executive into the conversation.
              </p>
            ) : (
              meeting.turns.map((t) => {
                const e = getExecutive(t.speaker);
                return (
                  <div key={t.id} className="flex items-start gap-2.5">
                    <ExecutiveAvatar exec={e} size="sm" active={activeSpeaker === t.speaker} />
                    <div className="min-w-0">
                      <p className={cn("text-[10px] font-medium", e.text)}>{e.name}</p>
                      <p className="text-[11px] text-[var(--axiom-text-secondary)] leading-snug">{t.text}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </main>

        {/* RIGHT — context / notes */}
        <aside className="hidden lg:flex w-80 flex-shrink-0 border-l border-[var(--axiom-border)] flex-col min-h-0">
          <BoardroomNotes meeting={meeting} patch={patch} />
        </aside>
      </div>

      {/* Notes drawer — tablet/mobile (overlays the right edge) */}
      <AnimatePresence>
        {notesOpen && (
          <motion.div
            initial={{ x: 280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 280, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute inset-y-0 right-0 z-20 w-80 lg:hidden flex flex-col bg-[var(--axiom-bg-surface)]/95 backdrop-blur-xl border-l border-[var(--axiom-border)]"
          >
            <BoardroomNotes meeting={meeting} patch={patch} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Share canvas overlay */}
      <AnimatePresence>{shareOpen && <BoardroomShare onClose={() => setShareOpen(false)} />}</AnimatePresence>
    </div>
  );
}

function ParticipantRow({ id, state, isHost }: { id: SpeakerId; state: BrVoiceState; isHost?: boolean }) {
  const exec = getExecutive(id);
  return (
    <div className={cn("flex items-center gap-2.5 px-2 py-2 rounded-lg", state === "SPEAKING" && "bg-white/[0.03]")}>
      <ExecutiveAvatar exec={exec} active={state === "SPEAKING"} size="sm" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-[var(--axiom-text-primary)] truncate">{exec.name}</span>
          {isHost && <span className="text-[8px] text-[var(--axiom-text-tertiary)]">HOST</span>}
        </div>
        <p className="text-[9px] text-[var(--axiom-text-tertiary)] truncate">{exec.role}</p>
      </div>
      <StatusChip state={state} />
      <Waveform active={state === "SPEAKING"} color="var(--axiom-accent)" bars={5} />
    </div>
  );
}

function MoreMenu({ open, onEnd, onDismiss }: { open: boolean; onEnd: () => void; onDismiss: () => void }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.15 }} className="mx-3 mb-3 rounded-xl border border-[var(--axiom-border-hover)] bg-[var(--axiom-bg-surface)] p-2 flex flex-col gap-1">
          <button onClick={onEnd} onMouseLeave={onDismiss} className="px-3 py-2 rounded-lg text-[11px] text-left text-[var(--axiom-error)] hover:bg-[var(--axiom-error)]/10">
            End meeting
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Control bar icons ─────────────────────────────────────────────────
const IconSvg = ({ children }: { children: React.ReactNode }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{children}</svg>
);
function MicIcon({ off }: { off: boolean }) {
  return (
    <IconSvg>
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4" />
      {off && <line x1="3" y1="3" x2="21" y2="21" />}
    </IconSvg>
  );
}
function VoiceIcon({ off }: { off: boolean }) {
  return (
    <IconSvg>
      <path d="M11 5 6 9H2v6h4l5 4z" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      {off && <line x1="3" y1="3" x2="21" y2="21" />}
    </IconSvg>
  );
}
function ShareIcon() {
  return (
    <IconSvg>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <path d="M21 15l-5-5L5 21" />
    </IconSvg>
  );
}
function NotesIcon() {
  return (
    <IconSvg>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
    </IconSvg>
  );
}
function MoreIcon() {
  return (
    <IconSvg>
      <circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /><circle cx="5" cy="12" r="1" />
    </IconSvg>
  );
}