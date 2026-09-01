"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { axiom } from "../../../lib/api";
import type {
  SystemAwareness,
  ExecutiveAwareness,
  EngineAwareness,
  AxiomChatResponse,
} from "../../../lib/api-types";

/* Sub-components */

function StateBadge({ state }: { state: string }) {
  const colorMap: Record<string, string> = {
    ONLINE: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    DEGRADED: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    BLOCKED: "bg-red-500/20 text-red-400 border-red-500/30",
    FAILED: "bg-red-600/20 text-red-300 border-red-600/30",
    RECOVERING: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    OFFLINE: "bg-neutral-500/20 text-neutral-400 border-neutral-500/30",
  };
  const cls = colorMap[state] || "bg-neutral-500/20 text-neutral-400 border-neutral-500/30";

  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`}>
      {state}
    </span>
  );
}

function HealthBar({ score }: { score: number }) {
  const hue = Math.round((score / 100) * 120);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[var(--axiom-bg-elevated)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: `hsl(${hue}, 60%, 45%)` }}
        />
      </div>
      <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] w-8 text-right">
        {score}%
      </span>
    </div>
  );
}

function ExecCard({ exec }: { exec: ExecutiveAwareness }) {
  return (
    <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)]">
      <div>
        <p className="text-xs font-medium text-[var(--axiom-text-primary)]">{exec.id}</p>
        <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{exec.org}</p>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-[var(--axiom-text-tertiary)]">×{exec.cycle_count}</span>
        <StateBadge state={exec.health} />
      </div>
    </div>
  );
}

function QuickAction({
  label,
  icon,
  onClick,
}: {
  label: string;
  icon: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-lg hover:bg-[var(--axiom-bg-elevated)] hover:text-[var(--axiom-text-primary)] transition-colors"
    >
      <span className="text-sm">{icon}</span>
      {label}
    </button>
  );
}

/* Main Component */

export default function AXIOMWorkspace() {
  const [awareness, setAwareness] = useState<SystemAwareness | null>(null);
  const [chatMessages, setChatMessages] = useState<
    { role: "user" | "axiom"; content: string }[]
  >([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [tab, setTab] = useState<"chat" | "awareness" | "executives">("chat");
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load awareness on mount and periodically
  useEffect(() => {
    const load = async () => {
      try {
        const data = await axiom.awareness();
        setAwareness(data);
        setError(null);
      } catch {
        // Backend not ready yet
      }
    };
    load();
    const interval = setInterval(load, 15_000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Add initial AXIOM greeting if chat is empty
  useEffect(() => {
    if (chatMessages.length === 0) {
      setChatMessages([
        {
          role: "axiom",
          content:
            awareness
              ? `Good day, Founder. AXIOM is ${awareness.state}. Health: ${awareness.overall_health}. I have ${awareness.executives.length} executives and ${awareness.workflows.active} active workflows. How may I assist you?`
              : "Good day, Founder. AXIOM Core initialising...",
        },
      ]);
    }
  }, [awareness, chatMessages.length]);

  const sendChat = async () => {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: msg }]);
    setChatLoading(true);

    try {
      const response: AxiomChatResponse = await axiom.chat(msg);
      setChatMessages((prev) => [
        ...prev,
        { role: "axiom", content: response.response },
      ]);
      if (response.awareness) setAwareness(response.awareness);
    } catch (e) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "axiom",
          content: "I encountered an error processing your request. Please try again.",
        },
      ]);
    }
    setChatLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">AXIOM Workstation</h2>
          </div>
          {awareness && <StateBadge state={awareness.state} />}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)]">
            {awareness ? `${awareness.uptime_seconds}s uptime` : "---"}
          </span>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex border-b border-[var(--axiom-border)] px-6">
        {(["chat", "awareness", "executives"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors capitalize ${
              tab === t
                ? "border-[var(--axiom-accent)] text-[var(--axiom-accent)]"
                : "border-transparent text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        <AnimatePresence mode="wait">
          {tab === "chat" && (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col overflow-hidden"
            >
              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                  >
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${
                        msg.role === "user"
                          ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                          : "bg-gradient-to-br from-[var(--axiom-accent)] to-purple-600 text-white"
                      }`}
                    >
                      {msg.role === "user" ? "U" : "A"}
                    </div>
                    <div
                      className={`max-w-[70%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-text-primary)]"
                          : "bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] text-[var(--axiom-text-secondary)]"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex gap-3">
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--axiom-accent)] to-purple-600 flex items-center justify-center flex-shrink-0">
                      <span className="animate-pulse text-white text-[10px]">A</span>
                    </div>
                    <div className="bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] rounded-xl px-4 py-2.5">
                      <div className="flex gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[var(--axiom-text-tertiary)] animate-bounce" style={{ animationDelay: "0ms" }} />
                        <span className="w-2 h-2 rounded-full bg-[var(--axiom-text-tertiary)] animate-bounce" style={{ animationDelay: "150ms" }} />
                        <span className="w-2 h-2 rounded-full bg-[var(--axiom-text-tertiary)] animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="px-6 py-3 border-t border-[var(--axiom-border)]">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message AXIOM..."
                    disabled={chatLoading}
                    className="flex-1 bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] rounded-lg px-3 py-2 text-sm text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] focus:outline-none focus:border-[var(--axiom-accent)] disabled:opacity-50"
                  />
                  <button
                    onClick={sendChat}
                    disabled={chatLoading || !chatInput.trim()}
                    className="px-3 py-2 bg-[var(--axiom-accent)] text-white rounded-lg text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    Send
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {tab === "awareness" && (
            <motion.div
              key="awareness"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 overflow-y-auto px-6 py-4 space-y-6"
            >
              {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
                  {error}
                </div>
              )}

              {!awareness && !error && (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-10 h-10 border-2 border-[var(--axiom-accent)] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-sm text-[var(--axiom-text-tertiary)]">Loading system awareness...</p>
                  </div>
                </div>
              )}

              {awareness && (
                <>
                  {/* Core Health */}
                  <div>
                    <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-3">
                      System Health
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)]">
                        <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide mb-1">State</p>
                        <p className="text-sm font-mono text-[var(--axiom-text-primary)]">{awareness.state}</p>
                      </div>
                      <div className="p-4 rounded-xl bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)]">
                        <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide mb-1">Overall Health</p>
                        <p className="text-sm font-mono text-[var(--axiom-text-primary)]">{awareness.overall_health}</p>
                      </div>
                      <div className="p-4 rounded-xl bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] col-span-2">
                        <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide mb-2">Health Score</p>
                        <HealthBar score={awareness.health_score} />
                      </div>
                    </div>
                  </div>

                  {/* Engines */}
                  <div>
                    <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-3">
                      Engines ({awareness.engines.length})
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {awareness.engines.map((eng: EngineAwareness) => (
                        <div
                          key={eng.name}
                          className="px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)]"
                        >
                          <p className="text-xs font-medium text-[var(--axiom-text-primary)]">{eng.label}</p>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{eng.name}</span>
                            <StateBadge state={eng.state} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Workflow Summary */}
                  <div>
                    <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-3">
                      Workflows
                    </h3>
                    <div className="grid grid-cols-5 gap-2">
                      {([
                        ["Defined", awareness.workflows.defined],
                        ["Active", awareness.workflows.active],
                        ["Pending", awareness.workflows.pending],
                        ["Failed", awareness.workflows.failed],
                        ["Approval", awareness.workflows.awaiting_approval],
                      ] as const).map(([label, count]) => (
                        <div
                          key={label}
                          className="p-3 rounded-lg bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] text-center"
                        >
                          <p className="text-lg font-bold text-[var(--axiom-text-primary)]">{count}</p>
                          <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {tab === "executives" && (
            <motion.div
              key="executives"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
            >
              <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-3">
                Executive Board
              </h3>
              {awareness && awareness.executives.length > 0 ? (
                <div className="space-y-2">
                  {awareness.executives.map((exec: ExecutiveAwareness) => (
                    <ExecCard key={exec.id} exec={exec} />
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32">
                  <p className="text-sm text-[var(--axiom-text-tertiary)]">No executive data available.</p>
                </div>
              )}

              {/* Quick Actions */}
              <div className="pt-6">
                <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wide mb-3">
                  Quick Actions
                </h3>
                <div className="flex flex-wrap gap-2">
                  <QuickAction
                    label="Route Request"
                    icon="⚡"
                    onClick={() => setTab("chat")}
                  />
                  <QuickAction
                    label="Communicate (Jenson)"
                    icon="📨"
                    onClick={async () => {
                      try {
                        const r = await axiom.communicate("jenson", "Status report?");
                        setChatMessages((prev) => [
                          ...prev,
                          { role: "axiom", content: `Jenson: ${r.response}` },
                        ]);
                        setTab("chat");
                      } catch { /* ignore */ }
                    }}
                  />
                  <QuickAction
                    label="System Execute"
                    icon="▶"
                    onClick={async () => {
                      try {
                        const r = await axiom.execute("status_summary");
                        setChatMessages((prev) => [
                          ...prev,
                          { role: "axiom", content: `Execute: ${r.result}` },
                        ]);
                        setTab("chat");
                      } catch { /* ignore */ }
                    }}
                  />
                  <QuickAction
                    label="Refresh Awareness"
                    icon="🔄"
                    onClick={async () => {
                      try {
                        const data = await axiom.awareness();
                        setAwareness(data);
                      } catch { /* ignore */ }
                    }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}