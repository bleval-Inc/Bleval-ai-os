"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { BLEVAL_GRADIENT } from "./types";
import { jensonInitialMessages, jensonContext, type ChatMessage } from "./bleval-ws-data";

function JensonAvatar({ size = 30 }: { size?: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-lg text-white flex-shrink-0"
      style={{ width: size, height: size, background: BLEVAL_GRADIENT, boxShadow: "0 0 14px -2px rgba(109,124,255,0.5)" }}
    >
      <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4l8 8-8 8v-4" />
        <path d="M4 14h8" />
      </svg>
    </div>
  );
}

function ContextPanel() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      {jensonContext.map((block, bi) => (
        <motion.div
          key={block.title}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 + bi * 0.06 }}
          className="rounded-xl border p-3.5"
          style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(15,18,24,0.4)" }}
        >
          <div className="text-[9px] font-semibold tracking-[0.18em] uppercase text-[var(--axiom-text-tertiary)] mb-2.5">
            {block.title}
          </div>
          <div className="space-y-2">
            {block.stats.map((s) => (
              <div key={s.label} className="flex items-center justify-between gap-2">
                <span className="text-[11px] text-[var(--axiom-text-secondary)]">{s.label}</span>
                <span className="flex items-center gap-1.5">
                  <span className="text-[12px] font-semibold text-[var(--axiom-text-primary)] tabular-nums">{s.value}</span>
                  {s.delta && <span className="text-[9px] font-medium text-emerald-400/90 tabular-nums">{s.delta}</span>}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

const CANNED_REPLIES = [
  "Understood, Founder. I'll fold that into today's priorities.",
  "Noted. Want me to draft follow-ups for the Solar campaign leads?",
  "On it. The three qualified prospects remain in final contract review.",
  "Acknowledged. I've queued that for the operations backlog.",
];

export default function JensonWorkstation() {
  const [messages, setMessages] = useState<ChatMessage[]>(jensonInitialMessages);
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const now = new Date();
    const time = now.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: false });
    const reply =
      CANNED_REPLIES[
        Math.floor(Math.random() * CANNED_REPLIES.length)
      ];
    setMessages((prev) => [
      ...prev,
      { id: `f-${Date.now()}`, role: "founder", text, time },
      { id: `j-${Date.now()}`, role: "jenson", text: reply, time },
    ]);
    setDraft("");
  };

  return (
    <div className="flex flex-col min-h-0 p-6 md:p-8 gap-4 min-w-0 pb-28">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="flex items-center gap-3">
        <JensonAvatar size={40} />
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-[var(--axiom-text-primary)]">JENSON</h1>
            <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">COO — BLEVAL INC</p>
          </div>
          <div className="flex items-center gap-1.5 rounded-full px-2 py-0.5 border" style={{ borderColor: "rgba(34,211,119,0.25)", background: "rgba(34,211,119,0.06)" }}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[9px] font-semibold tracking-wider text-emerald-400">ONLINE</span>
          </div>
        </div>
      </motion.div>

      {/* Layout */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5 min-w-0">
        {/* Conversation */}
        <div className="min-w-0 flex flex-col rounded-2xl border backdrop-blur-xl overflow-hidden" style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(15,18,24,0.42)" }}>
          <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar px-5 py-4 flex flex-col gap-4">
            <div className="text-center">
              <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 border text-[9px] font-semibold tracking-wider text-[var(--axiom-text-tertiary)]" style={{ borderColor: "rgba(240,241,243,0.08)" }}>
                ● DAILY BRIEFING · 07:30
              </span>
            </div>

            {messages.map((m) => {
              const isJenson = m.role === "jenson";
              return (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn("flex gap-3", isJenson ? "items-start" : "items-start flex-row-reverse")}
                >
                  {isJenson && <JensonAvatar size={28} />}
                  <div className={cn("max-w-[78%] min-w-0", !isJenson && "text-right")}>
                    <div
                      className={cn(
                        "inline-block text-left px-3.5 py-2.5 rounded-2xl text-[13px] leading-relaxed",
                        isJenson
                          ? "text-[var(--axiom-text-primary)]"
                          : "text-white",
                      )}
                      style={
                        isJenson
                          ? { background: "rgba(109,124,255,0.07)", border: "1px solid rgba(109,124,255,0.12)" }
                          : { background: BLEVAL_GRADIENT }
                      }
                    >
                      {m.text}
                    </div>
                    <div className="mt-1 text-[9px] text-[var(--axiom-text-tertiary)]">{m.time}</div>
                  </div>
                </motion.div>
              );
            })}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <form onSubmit={onSubmit} className="border-t p-3" style={{ borderColor: "rgba(109,124,255,0.1)" }}>
            <div className="flex items-center gap-2 rounded-full px-4 py-1.5 border backdrop-blur-xl" style={{ borderColor: "rgba(109,124,255,0.16)", background: "rgba(10,12,16,0.5)" }}>
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Speak or type to Jenson..."
                className="flex-1 min-w-0 bg-transparent text-[13px] text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] outline-none"
              />
              <button type="button" aria-label="Voice input (coming soon)" className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)] transition-colors">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><path d="M12 19v3" /></svg>
              </button>
              <motion.button
                type="submit"
                whileHover={{ scale: 1.06 }}
                whileTap={{ scale: 0.94 }}
                aria-label="Send message to Jenson"
                className="flex items-center justify-center w-9 h-9 rounded-full text-white"
                style={{ background: BLEVAL_GRADIENT, boxShadow: "0 4px 16px -4px rgba(109,124,255,0.6)" }}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14" /><path d="M12 5l7 7-7 7" /></svg>
              </motion.button>
            </div>
          </form>
        </div>

        {/* Company context */}
        <div className="min-w-0 overflow-y-auto hide-scrollbar pr-1">
          <div className="text-[10px] font-semibold tracking-[0.2em] uppercase text-[var(--axiom-text-tertiary)] px-1 mb-3">Company Context</div>
          <ContextPanel />
        </div>
      </div>
    </div>
  );
}