"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { cn } from "../../../lib/utils";

interface VoiceIndicatorProps {
  isAwake: boolean;
  isListening: boolean;
  listeningExecutive: string | null;
  voiceActive: boolean;
  setVoiceActive: (active: boolean) => void;
}

const EXECUTIVE_COLORS: Record<string, string> = {
  axiom: "text-indigo-400 bg-indigo-500/20",
  jenson: "text-blue-400 bg-blue-500/20",
  valta_prime: "text-amber-400 bg-amber-500/20",
  yamako: "text-violet-400 bg-violet-500/20",
};

export function VoiceIndicator({ isAwake, isListening, listeningExecutive, voiceActive, setVoiceActive }: VoiceIndicatorProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const getStateConfig = () => {
    if (isListening && listeningExecutive) {
      return { label: `LISTENING: ${listeningExecutive.toUpperCase()}`, color: "text-cyan-400", bgColor: "bg-cyan-500/20", pulse: true, icon: "listening" };
    }
    if (isAwake) {
      return { label: "AXIOM ONLINE", color: "text-green-400", bgColor: "bg-green-500/20", pulse: true, icon: "awake" };
    }
    if (voiceActive) {
      return { label: "VOICE READY", color: "text-indigo-400", bgColor: "bg-indigo-500/20", pulse: false, icon: "ready" };
    }
    return { label: "VOICE OFFLINE", color: "text-slate-500", bgColor: "bg-slate-500/20", pulse: false, icon: "offline" };
  };

  const config = getStateConfig();
  const execColor = listeningExecutive ? EXECUTIVE_COLORS[listeningExecutive] : "text-indigo-400 bg-indigo-500/20";

  return (
    <div className="relative">
      <button
        onClick={() => setVoiceActive(!voiceActive)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={cn(
          "relative flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all duration-200",
          config.pulse ? "bg-green-500/10 border border-green-500/30" : "bg-slate-800/50 border border-slate-700/50",
          "hover:bg-slate-800 hover:border-slate-600"
        )}
        title={
          isAwake
            ? "AXIOM ON — listening for commands"
            : voiceActive
              ? 'Say "AXIOM ON" to wake'
              : "Voice inactive — click to enable"
        }
      >
        {/* Mic Icon with Aura */}
        <div className="relative flex items-center justify-center">
          {/* Pulsing Aura Rings */}
          <AnimatePresence>
            {(config.pulse || isListening) && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0.6 }}
                animate={{ scale: [1, 1.5, 1], opacity: [0.4, 0, 0.4] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 rounded-full"
                style={{
                  background: config.icon === "listening"
                    ? "radial-gradient(circle, rgba(6, 182, 212, 0.4) 0%, transparent 70%)"
                    : "radial-gradient(circle, rgba(34, 197, 94, 0.4) 0%, transparent 70%)"
                }}
              />
            )}
          </AnimatePresence>

          {/* Mic Icon */}
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("flex-shrink-0 transition-colors duration-200", config.color)}
          >
            {config.icon === "offline" ? (
              <>
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <line x1="9" y1="9" x2="15" y2="15" />
                <line x1="1" y1="1" x2="23" y2="23" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </>
            ) : (
              <>
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </>
            )}
          </svg>

          {/* Audio Waveform when listening */}
          <AnimatePresence>
            {isListening && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute -right-6 top-1/2 -translate-y-1/2 flex items-center gap-1"
              >
                {[0, 1, 2, 3].map((i) => (
                  <motion.span
                    key={i}
                    className="w-0.5 rounded-full bg-cyan-400"
                    animate={{ height: [4, 16, 4] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.1, ease: "easeInOut" }}
                    style={{ height: 4 + i * 4 }}
                  />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Status Badge */}
        <span className={cn("text-[10px] font-semibold uppercase tracking-wider hidden sm:inline", config.color)}>
          {config.label}
        </span>

        {/* Executive indicator when listening */}
        <AnimatePresence>
          {isListening && listeningExecutive && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className={cn("text-[9px] font-medium px-1.5 py-0.5 rounded-full hidden sm:inline", execColor)}
            >
              {listeningExecutive.toUpperCase()}
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && !isListening && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute bottom-full mb-2 right-0 glass-panel px-3 py-2.5 whitespace-nowrap min-w-[220px] z-50"
          >
            <p className="text-[11px] font-medium text-white flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              Voice Controls
            </p>
            <p className="text-[9px] text-slate-400 mt-1">
              Say <span className="text-indigo-400 font-mono">&ldquo;AXIOM ON&rdquo;</span> to wake, or click to enable
            </p>
            <div className="flex items-center justify-between mt-1.5 text-[8px] text-slate-500 font-mono">
              <span>⌘⇧V</span>
              <span>Push-to-Talk</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

import { useState } from "react";

export default VoiceIndicator;