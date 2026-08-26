"use client";

import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "@/lib/store/axiom-store";
import type { SpeakerId } from "@/lib/api-types";
import { emptyMeeting, loadMeetings, persistMeeting, type BrMeeting } from "./boardroom/boardroom-data";
import BoardroomLanding from "./boardroom/BoardroomLanding";
import BoardroomMeeting from "./boardroom/BoardroomMeeting";
import BoardroomComplete from "./boardroom/BoardroomComplete";

// ── BOARDROOM — a first-class standalone AXIOM workstation ─────────────
// Route + shell remain the global AXIOM OS. Everything inside this viewport
// belongs exclusively to Boardroom: landing (executive selection) → active
// meeting (three regions) → completion summary. No AXIOM Home content is
// rendered underneath (the router swaps the whole workstation).

type Phase = "landing" | "active" | "complete";

export default function BoardroomWS() {
  const addSystemNotification = useAxiomStore((s) => s.addSystemNotification);

  const [phase, setPhase] = useState<Phase>("landing");
  const [selected, setSelected] = useState<SpeakerId[]>([]);
  const [meeting, setMeeting] = useState<BrMeeting | null>(null);
  const [saved, setSaved] = useState(false);

  const [pastMeetings, setPastMeetings] = useState<BrMeeting[]>(() => loadMeetings());

  const patchMeeting = useCallback((updater: (m: BrMeeting) => BrMeeting) => {
    setMeeting((prev) => (prev ? updater(prev) : prev));
  }, []);

  const toggleExec = useCallback((id: SpeakerId) => {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  }, []);

  const startMeeting = useCallback(() => {
    if (selected.length === 0) return;
    setMeeting(emptyMeeting(selected));
    setSaved(false);
    setPhase("active");
    addSystemNotification({
      type: "success",
      category: "executive",
      priority: "normal",
      title: "Boardroom session started",
      message: `${selected.length} executive${selected.length > 1 ? "s" : ""} joined. Only one voice is active at a time.`,
      sourceWorkspace: "boardroom",
    });
  }, [selected, addSystemNotification]);

  const endMeeting = useCallback(() => {
    setMeeting((prev) => (prev ? { ...prev, completedAt: Date.now() } : prev));
    setPhase("complete");
  }, []);

  const saveMeeting = useCallback(() => {
    if (!meeting) return;
    persistMeeting(meeting);
    setPastMeetings(loadMeetings());
    setSaved(true);
    addSystemNotification({
      type: "success",
      category: "workflow",
      priority: "low",
      title: "Meeting saved",
      message: `"${meeting.title}" saved to AXIOM operational memory.`,
      sourceWorkspace: "boardroom",
    });
  }, [meeting, addSystemNotification]);

  const returnToBoardroom = useCallback(() => {
    setPhase("landing");
    setMeeting(null);
    setSaved(false);
    setPastMeetings(loadMeetings());
  }, []);

  return (
    <div
      className="relative flex-1 min-h-0 overflow-hidden flex flex-col bg-[var(--axiom-bg-base)]"
      style={{
        background:
          "radial-gradient(ellipse 60% 45% at 0% 0%, rgba(109,124,255,0.05), transparent 60%), radial-gradient(ellipse 45% 40% at 100% 100%, rgba(168,140,255,0.05), transparent 60%), var(--axiom-bg-base)",
      }}
    >
      <div className="relative flex-1 min-h-0 flex flex-col">
        <AnimatePresence mode="wait">
          {phase === "landing" && (
            <motion.div key="landing" className="flex-1 flex flex-col min-h-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
              <BoardroomLanding selected={selected} onToggle={toggleExec} onStart={startMeeting} pastMeetings={pastMeetings} />
            </motion.div>
          )}

          {phase === "active" && meeting && (
            <motion.div key="active" className="flex-1 flex flex-col min-h-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
              <BoardroomMeeting meeting={meeting} patch={patchMeeting} onEnd={endMeeting} />
            </motion.div>
          )}

          {phase === "complete" && meeting && (
            <motion.div key="complete" className="flex-1 flex flex-col min-h-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
              <BoardroomComplete meeting={meeting} saved={saved} onSave={saveMeeting} onReturn={returnToBoardroom} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}