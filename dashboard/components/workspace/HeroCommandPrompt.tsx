"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { useVoiceBroadcast } from "../../lib/voice/voice-websocket";
import { useVoiceWebSocket } from "../../lib/voice/voice-websocket";
import { cn } from "../../lib/utils";

interface HeroCommandPromptProps {
  onCommand?: (command: string) => void;
  placeholder?: string;
  className?: string;
}

export function HeroCommandPrompt({
  onCommand,
  placeholder = "Type a command or ask AXIOM anything...",
  className = "",
}: HeroCommandPromptProps) {
  const [input, setInput] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const {
      isAwake,
      isListening,
      listeningExecutive,
      voiceActive,
      setVoiceActive,
      addNotification,
      triggerPushToTalk,
    } = useAxiomStore();

  // Voice broadcast for real-time waveform
    const [voiceSpeaking, setVoiceSpeaking] = useState(false);
    const [voiceExecutive, setVoiceExecutive] = useState<string | null>(null);
    const { isConnected: voiceConnected } = useVoiceBroadcast({
      onSpeak: (msg) => {
        if (msg.executive && msg.text) {
          setVoiceSpeaking(true);
          setVoiceExecutive(msg.executive);
          // Auto-hide after speech ends
          const timeout = setTimeout(() => {
            setVoiceSpeaking(false);
            setVoiceExecutive(null);
          }, 3000);
          return () => clearTimeout(timeout);
        }
      },
      onStatus: (msg) => {
        // Update store based on voice status if needed
        console.log("Voice status:", msg);
        // Check if message has the listening state (status messages from broadcast)
        if (msg.type === "status" && "is_listening" in msg && msg.is_listening === false) {
          setVoiceSpeaking(false);
          setVoiceExecutive(null);
        }
      },
      autoConnect: true,
    });

    // Command suggestions based on context
  const commandSuggestions = [
    "Show system status",
    "Deploy to production",
    "Run workflow pipeline",
    "Check market data",
    "Create content brief",
    "View executive board",
    "Schedule meeting",
    "Generate report",
    "Switch to Engineering",
    "Open Boardroom",
    "Emergency pause",
    "Wake Jenson",
    "Wake Valta Prime",
    "Wake Yamako",
  ];

  // Update suggestions based on input
  useEffect(() => {
    if (input.length > 0) {
      const filtered = commandSuggestions
        .filter((cmd) => cmd.toLowerCase().includes(input.toLowerCase()))
        .slice(0, 5);
      setSuggestions(filtered);
      setSelectedSuggestion(0);
    } else {
      setSuggestions(commandSuggestions.slice(0, 5));
    }
  }, [input]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim()) return;

      const command = input.trim();
      setInput("");
      setSuggestions([]);

      // Add to notifications
      addNotification({
        id: `cmd-${Date.now()}`,
        type: "info",
        title: "Command executed",
        message: command,
        timestamp: Date.now(),
        read: false,
      });

      // Call external handler if provided
      onCommand?.(command);
    },
    [input, onCommand, addNotification],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown" && suggestions.length > 0) {
        e.preventDefault();
        setSelectedSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
      } else if (e.key === "ArrowUp" && suggestions.length > 0) {
        e.preventDefault();
        setSelectedSuggestion((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Tab" && suggestions.length > 0) {
        e.preventDefault();
        setInput(suggestions[selectedSuggestion]);
      } else if (e.key === "Escape") {
        setSuggestions([]);
        inputRef.current?.blur();
      }
    },
    [suggestions, selectedSuggestion],
  );

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      setInput(suggestion);
      inputRef.current?.focus();
    },
    [],
  );

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className={cn("relative w-full max-w-4xl mx-auto", className)}>
      <form onSubmit={handleSubmit} className="relative">
        {/* Main Input */}
        <div className="relative">
          <label htmlFor="hero-command" className="sr-only">
            AXIOM Command Prompt
          </label>
          <div className="relative flex items-center">
            {/* Prefix */}
            <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
              <span className="text-sm font-mono text-slate-500">{"AXIOM>"}</span>
            </div>

            {/* Input Field */}
            <input
              ref={inputRef}
              id="hero-command"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsExpanded(true)}
              onBlur={() => {
                setTimeout(() => setSuggestions([]), 200);
              }}
              placeholder={placeholder}
              className={cn(
                "w-full bg-slate-950/50 backdrop-blur-sm border border-white/10 rounded-xl px-16 py-5 text-lg text-white placeholder-slate-500",
                "focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 focus:ring-offset-2 focus:ring-offset-slate-950",
                "transition-all duration-200",
                isExpanded && "border-indigo-500/30 bg-slate-950/80",
              )}
              autoComplete="off"
              spellCheck={false}
            />

            {/* Voice Visualizer - Inline */}
            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
              {/* Real-time waveform when speaking */}
              {(voiceSpeaking || isListening || voiceActive) && (
                <div className="flex items-center gap-1.5" style={{ width: 80 }}>
                  <span className="text-[9px] font-mono text-slate-500 hidden sm:inline">VOICE</span>
                  <div className="flex items-end gap-0.5 h-6 flex-1" role="img" aria-label="Voice waveform">
                    {Array.from({ length: 12 }).map((_, i) => (
                      <motion.div
                        key={i}
                        initial={{ height: 2 }}
                        animate={{
                          height: [
                            Math.max(2, (voiceSpeaking || isListening ? (0.3 + Math.random() * 0.7) : 0.1) * 24),
                            Math.max(2, (voiceSpeaking || isListening ? (0.3 + Math.random() * 0.7) : 0.1) * 24),
                            Math.max(2, (voiceSpeaking || isListening ? (0.3 + Math.random() * 0.7) : 0.1) * 24),
                          ],
                        }}
                        transition={{ duration: 0.15, repeat: Infinity, delay: i * 0.03 }}
                        className="rounded"
                        style={{
                          width: 3,
                          background: voiceSpeaking || isListening
                            ? "linear-gradient(to top, var(--axiom-indigo-400), var(--axiom-indigo-600))"
                            : "linear-gradient(to top, var(--axiom-sky-400), var(--axiom-sky-600))",
                          opacity: voiceSpeaking || isListening ? 0.9 : 0.4,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Status Indicator */}
              <div className="flex items-center gap-2">
                {isAwake && isListening && (
                  <motion.span
                    className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-[10px] font-medium border border-green-500/30"
                    animate={{ opacity: [1, 0.6, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                    LISTENING
                  </motion.span>
                )}
                {voiceSpeaking && voiceExecutive && !isListening && (
                  <motion.span
                    className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px] font-medium border border-indigo-500/30"
                    animate={{ opacity: [1, 0.7, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <motion.span
                      className="w-1.5 h-1.5 rounded-full"
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ duration: 0.5, repeat: Infinity }}
                      style={{ backgroundColor: "var(--axiom-indigo-500)" }}
                    />
                    {voiceExecutive.replace("_", " ").toUpperCase()}
                  </motion.span>
                )}
                {!isAwake && voiceActive && !voiceSpeaking && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px] font-medium border border-indigo-500/30">
                    <span className="relative w-1.5 h-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-60" />
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-indigo-400" />
                    </span>
                    WAKE WORD
                  </span>
                )}
                {!voiceActive && !voiceSpeaking && !isListening && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-500 text-[10px] font-medium border border-white/5">
                    INACTIVE
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Suggestions Dropdown */}
          <AnimatePresence>
            {isExpanded && suggestions.length > 0 && input.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -8, height: 0 }}
                animate={{ opacity: 1, y: 0, height: "auto" }}
                exit={{ opacity: 0, y: -8, height: 0 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="absolute left-0 right-0 top-full mt-2 glass-panel border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 max-h-60 overflow-y-auto"
              >
                {suggestions.map((suggestion, index) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => handleSuggestionClick(suggestion)}
                    onMouseEnter={() => setSelectedSuggestion(index)}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-3 text-left text-sm transition-colors border-t border-white/5",
                      index === 0 && "border-t-0",
                      index === selectedSuggestion
                        ? "bg-indigo-500/10 text-indigo-400"
                        : "text-slate-300 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                    <span>{suggestion}</span>
                    <kbd className="ml-auto text-[9px] font-mono text-slate-500 px-1.5 py-0.5 bg-white/5 rounded">Enter</kbd>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-500">Quick:</span>
            {["Deploy", "Research", "Report", "Board"].map((action) => (
              <button
                key={action}
                type="button"
                onClick={() => {
                  const cmd = action.toLowerCase();
                  setInput(cmd);
                  inputRef.current?.focus();
                }}
                className="px-3 py-1 text-[10px] font-medium text-slate-400 hover:text-white hover:bg-white/5 border border-white/5 rounded-full transition-colors"
              >
                {action}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
                          type="button"
                          onClick={() => {
                            if (!voiceActive) setVoiceActive(true);
                            // Trigger push-to-talk via store callback
                            triggerPushToTalk();
                          }}
                          className={cn(
                            "p-2 rounded-lg transition-all duration-150",
                            "flex items-center justify-center",
                            voiceActive
                              ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30"
                              : "bg-white/5 text-slate-500 border border-white/10 hover:bg-white/10 hover:text-slate-300"
                          )}
                          title="Voice Command (⌘⇧V)"
                        >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            </button>

            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-[9px] font-mono text-slate-500 bg-white/5 rounded border border-white/5">
              <span>⌘</span>⇧V
            </kbd>
          </div>
        </div>
      </form>
    </div>
  );
}

// Executive Summary Card for the hero grid
interface ExecutiveSummaryCardProps {
  executive: "axiom" | "jenson" | "valta_prime" | "yamako";
  status: "online" | "busy" | "idle" | "offline";
  currentTask?: string;
  metrics?: Record<string, string>;
  onClick?: () => void;
}

const EXECUTIVE_INFO: Record<string, {
  name: string;
  title: string;
  color: string;
  colorFrom: string;
  colorTo: string;
  avatar: string;
}> = {
  axiom: { name: "AXIOM", title: "Chief Orchestration", color: "indigo", colorFrom: "indigo-400", colorTo: "indigo-600", avatar: "A" },
  jenson: { name: "Jenson", title: "Chief Operations", color: "sky", colorFrom: "sky-400", colorTo: "blue-600", avatar: "J" },
  valta_prime: { name: "Valta Prime", title: "Chief Capital", color: "amber", colorFrom: "amber-400", colorTo: "amber-600", avatar: "V" },
  yamako: { name: "Yamako", title: "Chief Personal", color: "violet", colorFrom: "violet-400", colorTo: "purple-600", avatar: "Y" },
};

const STATUS_CONFIG = {
  online: { label: "ONLINE", color: "emerald", pulse: true },
  busy: { label: "BUSY", color: "amber", pulse: true },
  idle: { label: "IDLE", color: "slate", pulse: false },
  offline: { label: "OFFLINE", color: "rose", pulse: false },
};

export function ExecutiveSummaryCard({
  executive,
  status = "idle",
  currentTask,
  metrics = {},
  onClick,
}: ExecutiveSummaryCardProps) {
  const info = EXECUTIVE_INFO[executive];
  const statusInfo = STATUS_CONFIG[status];

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "relative glass-panel p-6 rounded-2xl border overflow-hidden transition-all duration-300",
        "bg-gradient-to-br from-white/5 to-white/2.5",
        onClick && "cursor-pointer hover:shadow-xl"
      )}
      style={{
        background: `linear-gradient(135deg, ${info.colorFrom}/10 0%, ${info.colorTo}/5 100%)`,
        borderColor: `${info.colorFrom}/20`,
      }}
    >
      {/* Top accent bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-current to-transparent opacity-50" style={{ background: `var(--axiom-${info.color}-500)` }} />

      {/* Executive Header */}
      <div className="flex items-center gap-4 relative z-10">
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br" style={{ background: `var(--axiom-${info.colorFrom}) to var(--axiom-${info.colorTo})` }} />
          <span className="relative text-2xl font-bold text-white">{info.avatar}</span>

          {/* Status dot */}
          <motion.span
            className={`absolute bottom-1 right-1 w-4 h-4 rounded-full border-2 border-slate-950`}
            style={{ backgroundColor: `var(--axiom-${statusInfo.color}-500)` }}
            animate={{ scale: statusInfo.pulse ? [1, 1.2, 1] : 1 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white truncate">{info.name}</h3>
          <p className="text-sm text-slate-400 truncate">{info.title}</p>
        </div>
      </div>

      {/* Status Badge */}
      <div className="absolute top-4 right-4">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border`} style={{
          backgroundColor: `var(--axiom-${statusInfo.color}-500)/20`,
          color: `var(--axiom-${statusInfo.color}-400)`,
          borderColor: `var(--axiom-${statusInfo.color}-500)/30`,
        }}>
          <motion.span
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: `var(--axiom-${statusInfo.color}-500)` }}
            animate={{ scale: statusInfo.pulse ? [1, 1.3, 1] : 1 }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          {statusInfo.label}
        </span>
      </div>

      {/* Current Task */}
      {currentTask && (
        <div className="mt-4 p-3 rounded-xl bg-white/5 backdrop-blur-sm border border-white/5 relative z-10">
          <p className="text-sm text-slate-300 leading-relaxed">
            <span className="text-slate-500 font-medium">Current:</span> {currentTask}
          </p>
        </div>
      )}

      {/* Metrics */}
      {Object.keys(metrics).length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-3 relative z-10">
          {Object.entries(metrics).map(([key, value]) => (
            <div key={key} className="text-center p-2 rounded-lg bg-white/2.5">
              <div className="text-lg font-bold text-white tabular-nums">{value}</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">{key}</div>
            </div>
          ))}
        </div>
      )}
    </motion.button>
  );
}

export default HeroCommandPrompt;