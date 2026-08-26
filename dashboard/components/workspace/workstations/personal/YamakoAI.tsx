"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { yamakoInitialMessages, yamakoSuggestions, yamakoCapabilities, type YamakoMessage } from "./personal-data";
import { Panel, SectionTitle, StatusChip, YamakoAvatar } from "./personal-ui";
import { PERSONAL_TEAL } from "./types";

function YamakoBubble({ m }: { m: YamakoMessage }) {
  const isYamako = m.role === "yamako";
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={cn("flex gap-3", !isYamako && "flex-row-reverse")}>
      {isYamako ? (
        <YamakoAvatar size={30} />
      ) : (
        <div className="w-[30px] h-[30px] rounded-xl flex items-center justify-center text-[10px] font-semibold text-[var(--axiom-text-primary)] bg-[var(--axiom-bg-elevated)] border border-[rgba(240,241,243,0.08)] flex-shrink-0">FE</div>
      )}
      <div className={cn("max-w-[82%] min-w-0", !isYamako && "text-right")}>
        <div className={cn("rounded-2xl px-3.5 py-2.5 text-[12px] leading-relaxed", isYamako ? "border border-[rgba(240,241,243,0.06)] bg-[rgba(15,18,24,0.5)] text-[var(--axiom-text-secondary)]" : "text-[var(--axiom-text-primary)]")} style={isYamako ? {} : { background: "rgba(109,124,255,0.12)" }}>
          {m.text}
        </div>
        <span className={cn("block text-[9px] text-[var(--axiom-text-tertiary)] mt-1", !isYamako && "text-right")}>{m.time}</span>
      </div>
    </motion.div>
  );
}

function VoiceButton() {
  const [armed, setArmed] = useState(false);
  return (
    <button
      onClick={() => setArmed((a) => !a)}
      className={cn("flex items-center justify-center rounded-xl border transition-all duration-200 w-10 h-10 flex-shrink-0", armed ? "text-white border-transparent" : "text-[var(--axiom-text-secondary)]")}
      style={armed ? { background: `linear-gradient(135deg, ${PERSONAL_TEAL}, #4da3ff)` } : { background: "rgba(240,241,243,0.03)", borderColor: "rgba(240,241,243,0.08)" }}
      aria-pressed={armed}
      title="Voice input (placeholder)"
    >
      <span className="flex items-end gap-[2px] h-4">
        {[0, 1, 2, 3].map((b) => (
          <span key={b} className={cn("w-[2px] rounded-full bg-current", armed ? "animate-waveform" : "")} style={armed ? { animationDelay: `${b * 0.12}s` } : { height: 5 }} />
        ))}
      </span>
    </button>
  );
}

export default function YamakoAI() {
  const [messages, setMessages] = useState<YamakoMessage[]>(yamakoInitialMessages);
  const [draft, setDraft] = useState("");

  const send = () => {
    if (!draft.trim()) return;
    const sent: YamakoMessage = { id: `f-${Date.now()}`, role: "founder", text: draft.trim(), time: "now" };
    setMessages((ms) => [...ms, sent]);
    setDraft("");
    // Streaming response placeholder — mark it clearly as an integration point.
    setTimeout(() => {
      const reply: YamakoMessage = {
        id: `y-${Date.now()}`,
        role: "yamako",
        time: "now",
        text: "I've noted that down. In the live build I'd turn this into an actionable workflow — research, schedule, or a learning task. For now this is a demo reply from Yamako.",
      };
      setMessages((ms) => [...ms, reply]);
    }, 400);
  };

  return (
    <div className="flex flex-col gap-5 p-6 md:p-8 pb-32 min-w-0 h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <YamakoAvatar size={44} />
          <div>
            <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--axiom-text-primary)]">YAMAKO</h1>
            <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">Your executive intelligence</p>
          </div>
        </div>
        <StatusChip label="Online" tone="healthy" />
      </div>

      {/* Capabilities */}
      <div className="flex flex-wrap gap-1.5">
        {yamakoCapabilities.map((c) => (
          <span key={c} className="rounded-full px-2.5 py-1 text-[10px] font-medium text-[var(--axiom-text-secondary)] border" style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(109,124,255,0.05)" }}>
            {c}
          </span>
        ))}
      </div>

      {/* Conversation workspace — fills the remaining height */}
      <Panel className="flex-1 min-h-0 min-w-0 flex flex-col">
        <SectionTitle title="Conversation" hint="Yamako · demo" className="flex-shrink-0" />
        <div className="flex-1 overflow-y-auto hide-scrollbar px-4 pb-4 space-y-4 min-h-0">
          <AnimatePresence initial={false}>
            {messages.map((m) => <YamakoBubble key={m.id} m={m} />)}
          </AnimatePresence>
        </div>

        {/* Suggestions */}
        <div className="px-4 pb-3 border-t pt-3" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
          <div className="flex flex-wrap gap-1.5">
            {yamakoSuggestions.map((s) => (
              <button
                key={s}
                onClick={() => setDraft(s)}
                className="text-[10px] text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-text-primary)] rounded-full px-2.5 py-1 border border-[var(--axiom-border-hover)] bg-[var(--axiom-bg-glass)] text-left"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="px-4 pb-4">
          <div className="flex items-center gap-2 rounded-xl border px-2 py-1.5" style={{ borderColor: "rgba(109,124,255,0.16)", background: "rgba(10,12,16,0.5)" }}>
            <VoiceButton />
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") send(); }}
              placeholder="Message Yamako — ask, plan, research, review…"
              className="flex-1 min-w-0 bg-transparent outline-none text-[12px] text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] px-1"
            />
            <button onClick={send} className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-[11px] font-semibold text-white flex-shrink-0" style={{ background: "linear-gradient(135deg,#6d7cff,#a88cff)" }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" /></svg>
              Send
            </button>
          </div>
          <p className="mt-1.5 text-[9px] text-[var(--axiom-text-tertiary)]">
            Yamako coordinates your schedule, learning, research and progress. Demo interface — future replies stream live and can become workflows.
          </p>
        </div>
      </Panel>
    </div>
  );
}