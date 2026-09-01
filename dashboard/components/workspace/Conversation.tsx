"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { speak } from "../../lib/voice/speak";

interface Message {
  id: string;
  role: "user" | "axiom";
  content: string;
  timestamp: Date;
  artifacts?: string[];
}

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "axiom",
  content:
    "I'm AXIOM, your operating system concierge. I can help you navigate the system, manage executives, launch workflows, review memory, or answer questions about what's happening across your organization. What would you like to explore?",
  timestamp: new Date(),
};

const SUGGESTIONS = [
  "Show me the executive board status",
  "What happened overnight?",
  "Launch a workflow",
  "Show my memory entries",
];

async function sendChat(
  message: string,
  agentId = "founder",
): Promise<string> {
  try {
    const res = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, agent_id: agentId }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.response || "(no response)";
  } catch (err) {
    return `[Connection Error] ${err instanceof Error ? err.message : "Unable to reach AXIOM intelligence. The backend may be offline."}`;
  }
}

export default function Conversation() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const {
    setIsSpeaking,
    pendingVoiceCommand,
    setPendingVoiceCommand,
  } = useAxiomStore();

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Watch for voice commands from VoiceEngine

  useEffect(() => {
    if (pendingVoiceCommand) {
      const cmd = pendingVoiceCommand;
      setPendingVoiceCommand(null);
      handleSend(cmd);
    }
  }, [pendingVoiceCommand]);

  const axiomSpeak = useCallback(
    (text: string) => {
      speak(text, {
        rate: 0.85,
        pitch: 1.08,
        onStart: () => setIsSpeaking(true),
        onEnd: () => setIsSpeaking(false),
      });
    },
    [setIsSpeaking],
  );

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isProcessing) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsProcessing(true);

    try {
      // Send to AXIOM backend intelligence engine with smart model routing
      const initialMsg = text.trim();
      const activeView = useAxiomStore.getState().activeView;
      const agentId =
        activeView === "boardroom"
          ? "jenson"
          : "founder";

      const response = await sendChat(initialMsg, agentId);

      const axiomMsg: Message = {
        id: `axiom-${Date.now()}`,
        role: "axiom",
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, axiomMsg]);

      // AXIOM speaks every response with proper voice
      axiomSpeak(axiomMsg.content);
    } catch {
      const axiomMsg: Message = {
        id: `axiom-${Date.now()}`,
        role: "axiom",
        content:
          "I encountered an error processing your request. Please try again or check that the backend is running.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, axiomMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" as const }}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {/* AXIOM avatar */}
              {msg.role === "axiom" && (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-[10px] font-bold text-white">A</span>
                </div>
              )}

              <div
                className={`max-w-[70%] ${
                  msg.role === "user"
                    ? "bg-[var(--axiom-accent)] text-white rounded-2xl rounded-br-md px-4 py-2.5"
                    : "text-[var(--axiom-text-primary)]"
                }`}
              >
                {msg.role === "axiom" && (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </p>
                )}
                {msg.role === "user" && (
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                )}
                <span
                  className={`block text-[10px] mt-1.5 ${
                    msg.role === "user"
                      ? "text-white/60"
                      : "text-[var(--axiom-text-tertiary)]"
                  }`}
                >
                  {msg.timestamp.toLocaleTimeString([], {
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </span>
              </div>

              {/* User avatar */}
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-[10px] font-medium text-[var(--axiom-text-secondary)]">
                    F
                  </span>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Processing indicator */}
        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex gap-3"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center flex-shrink-0">
                <span className="text-[10px] font-bold text-white">A</span>
              </div>
              <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl rounded-tl-md bg-[var(--axiom-bg-elevated)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse" />
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse animate-delay-200" />
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse animate-delay-400" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Suggestions (shown when no messages besides welcome) */}
        {messages.length === 1 && !isProcessing && (
          <div className="flex flex-wrap gap-2 mt-4">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSend(suggestion)}
                className="px-3 py-1.5 text-xs text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-full hover:bg-[var(--axiom-bg-elevated)] hover:text-[var(--axiom-text-primary)] transition-all duration-150"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="px-4 py-3 border-t border-[var(--axiom-border)]">
        <div className="flex items-end gap-2 glass-card p-2">
          {/* Text input */}
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AXIOM anything... (⌘⇧V for voice)"
            rows={1}
            className="flex-1 bg-transparent text-sm text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] outline-none resize-none py-1.5 font-sans max-h-32"
          />

          {/* Send button */}
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isProcessing}
            className="p-2 rounded-lg bg-[var(--axiom-accent)] text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[var(--axiom-accent-hover)] transition-all duration-150"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m22 2-7 20-4-9-9-4Z" />
              <path d="M22 2 11 13" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}