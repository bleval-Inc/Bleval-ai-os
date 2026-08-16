"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useVoiceBroadcast, type VoiceWSMessage, type SpeechUrgency } from "../../lib/voice/voice-websocket";
import { cn } from "../../lib/utils";

interface VoiceVisualizerProps {
  className?: string;
  height?: number;
  barsCount?: number;
  color?: "indigo" | "sky" | "amber" | "violet" | "emerald";
  autoConnect?: boolean;
}

export function VoiceVisualizer({
  className = "",
  height = 40,
  barsCount = 32,
  color = "indigo",
  autoConnect = true,
}: VoiceVisualizerProps) {
  const [amplitudes, setAmplitudes] = useState<number[]>(
    Array(barsCount).fill(0).map(() => Math.random() * 0.1)
  );
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentExecutive, setCurrentExecutive] = useState<string | null>(null);
  const [urgency, setUrgency] = useState<SpeechUrgency>("normal");
  const [mappedUrgency, setMappedUrgency] = useState<"normal" | "high" | "emergency">("normal");
  const animationFrameRef = useRef<number | null>(null);
  const targetAmplitudesRef = useRef<number[]>(Array(barsCount).fill(0));

  const COLOR_CONFIG = {
    indigo: { primary: "indigo", from: "indigo-400", to: "indigo-600", glow: "rgba(99, 102, 241," },
    sky: { primary: "sky", from: "sky-400", to: "sky-600", glow: "rgba(56, 189, 248," },
    amber: { primary: "amber", from: "amber-400", to: "amber-600", glow: "rgba(251, 191, 36," },
    violet: { primary: "violet", from: "violet-400", to: "violet-600", glow: "rgba(167, 139, 250," },
    emerald: { primary: "emerald", from: "emerald-400", to: "emerald-600", glow: "rgba(16, 185, 129," },
  };

  const config = COLOR_CONFIG[color];

  const handleSpeak = useCallback((message: VoiceWSMessage) => {
    if (message.type === "speak" && message.executive && message.text) {
      setIsSpeaking(true);
      setCurrentExecutive(message.executive);
      setUrgency(message.urgency || "normal");

      // Map urgency for use in JSX
      const urgencyMap: Record<string, "normal" | "high" | "emergency"> = {
        silent: "normal",
        low: "normal",
        normal: "normal",
        high: "high",
        critical: "emergency",
        escalation: "emergency",
      };
      setMappedUrgency(urgencyMap[message.urgency || "normal"] || "normal");

      // Generate dynamic waveform based on speech
      generateWaveform(message.text.length, message.urgency);
    }
  }, []);

  const handleStatus = useCallback((message: VoiceWSMessage) => {
    if (message.type === "status") {
      // Check if this executive is done speaking
      if ("is_listening" in message && message.is_listening === false && "listening_executive" in message) {
        // Stop animation after a delay
        setTimeout(() => {
          setIsSpeaking(false);
          setCurrentExecutive(null);
        }, 1000);
      }
    }
  }, []);

  const { isConnected } = useVoiceBroadcast({
    onSpeak: handleSpeak,
    onStatus: handleStatus,
    autoConnect,
  });

  const generateWaveform = (textLength: number, urgency?: SpeechUrgency) => {
    const urgencyMap: Record<string, "normal" | "high" | "emergency"> = {
      silent: "normal",
      low: "normal",
      normal: "normal",
      high: "high",
      critical: "emergency",
      escalation: "emergency",
    };
    const mappedUrgencyInternal = urgency ? urgencyMap[urgency] || "normal" : "normal";

    const baseIntensity = Math.min(0.3 + textLength * 0.008, 0.8);
    const urgencyMultiplier = mappedUrgencyInternal === "emergency" ? 1.5 : mappedUrgencyInternal === "high" ? 1.2 : 1;

    targetAmplitudesRef.current = Array.from({ length: barsCount }, (_, i) => {
      // Create a more natural speech pattern with varying frequencies
      const centerFreq = barsCount / 2;
      const distanceFromCenter = Math.abs(i - centerFreq);
      const falloff = Math.exp(-distanceFromCenter / (barsCount / 4));

      const noise = 0.1 + Math.random() * 0.4;
      const intensity = baseIntensity * falloff * noise * urgencyMultiplier;

      return Math.min(intensity + Math.random() * 0.15, 1);
    });

    // Start animation loop
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    animate();
  };

  const animate = () => {
    if (!isSpeaking) {
      // Fade out when not speaking
      const allZero = targetAmplitudesRef.current.every((v) => v < 0.01);
      targetAmplitudesRef.current = targetAmplitudesRef.current.map((v) => v * 0.92);

      setAmplitudes((prev) =>
        prev.map((amp, i) => {
          const target = targetAmplitudesRef.current[i] || 0;
          return amp + (target - amp) * 0.3;
        })
      );

      if (!allZero) {
        animationFrameRef.current = requestAnimationFrame(animate);
      }
      return;
    }

    // Smooth interpolation towards target
    setAmplitudes((prev) =>
      prev.map((amp, i) => {
        const target = targetAmplitudesRef.current[i] || 0;
        // Add some micro-variation for realism
        const vibration = (Math.random() - 0.5) * 0.05;
        const newAmp = amp + (target - amp) * 0.25 + vibration;
        return Math.max(0, Math.min(1, newAmp));
      })
    );

    // Gradually decay targets for natural speech rhythm
    targetAmplitudesRef.current = targetAmplitudesRef.current.map((v) =>
      v * (0.95 + Math.random() * 0.05)
    );

    animationFrameRef.current = requestAnimationFrame(animate);
  };

  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <div className={cn("relative flex items-end justify-center gap-1", className)}>
      {/* Background glow when speaking */}
      <AnimatePresence>
        {isSpeaking && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute inset-0 rounded-lg blur-xl opacity-30"
            style={{
              background: `linear-gradient(90deg, var(--axiom-${config.from}) 0%, var(--axiom-${config.to}) 100%)`,
              animation: `pulse-glow ${mappedUrgency === "emergency" ? "0.5s" : mappedUrgency === "high" ? "1s" : "2s"} ease-in-out infinite`,
            }}
          />
        )}
      </AnimatePresence>

      {/* Frequency Bars */}
      <div className="flex items-end justify-center gap-1 h-full" role="img" aria-label="Voice waveform visualizer">
        {amplitudes.map((amplitude, index) => {
          const barHeight = Math.max(2, amplitude * height);
          // Add slight variation for visual interest
          const delay = index * 0.01;

          return (
            <motion.div
              key={index}
              initial={{ height: 2, opacity: 0.3 }}
              animate={{
                height: barHeight,
                opacity: 0.4 + amplitude * 0.6,
              }}
              transition={{ duration: 0.05, ease: "easeOut" }}
              className="rounded relative"
              style={{
                width: Math.max(2, 120 / barsCount),
                background: `linear-gradient(to top, var(--axiom-${config.from}) 0%, var(--axiom-${config.to}) 100%)`,
                boxShadow: `0 0 ${2 + amplitude * 8}px ${config.glow}${0.3 + amplitude * 0.5})`,
              }}
            />
          );
        })}
      </div>

      {/* Executive indicator when speaking */}
      <AnimatePresence>
        {isSpeaking && currentExecutive && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 rounded-full text-[10px] font-medium uppercase tracking-wider whitespace-nowrap"
            style={{
              background: `linear-gradient(135deg, var(--axiom-${config.from})/20, var(--axiom-${config.to})/10)`,
              color: `var(--axiom-${config.from})`,
              borderColor: `var(--axiom-${config.from})/30`,
              borderWidth: "1px",
              borderStyle: "solid",
            }}
          >
            {currentExecutive.replace("_", " ")}
            <span className="ml-1.5 inline-flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full animate-pulse`} style={{ backgroundColor: `var(--axiom-${config.from})` }} />
              {urgency !== "normal" && <span className="text-[8px]">{urgency.toUpperCase()}</span>}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Connection status indicator */}
      <div className="absolute -right-6 top-1/2 -translate-y-1/2 flex items-center gap-1">
        <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-rose-400"}`} />
        <span className="text-[9px] font-mono text-slate-500 hidden sm:inline">
          {isConnected ? "LIVE" : "OFF"}
        </span>
      </div>

      <style jsx>{`
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.2; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
}

// Mini version for inline use (e.g., in header)
export function InlineVoiceVisualizer({
  executive = "axiom",
  isActive = false,
  className = "",
  size = 32,
}: {
  executive?: "axiom" | "jenson" | "valta_prime" | "yamako";
  isActive?: boolean;
  className?: string;
  size?: number;
}) {
  const EXECUTIVE_COLORS = {
    axiom: { from: "indigo-400", to: "indigo-600" },
    jenson: { from: "sky-400", to: "blue-600" },
    valta_prime: { from: "amber-400", to: "amber-600" },
    yamako: { from: "violet-400", to: "purple-600" },
  };

  const config = EXECUTIVE_COLORS[executive];
  const barsCount = 8;
  const [amplitudes, setAmplitudes] = useState<number[]>(
    Array(barsCount).fill(0).map(() => Math.random() * 0.1)
  );
  const animationFrameRef = useRef<number | null>(null);
  const targetAmplitudesRef = useRef<number[]>(Array(barsCount).fill(0));

  useEffect(() => {
    if (!isActive) {
      // Fade out
      const fadeInterval = setInterval(() => {
        targetAmplitudesRef.current = targetAmplitudesRef.current.map((v) => v * 0.8);
        if (targetAmplitudesRef.current.every((v) => v < 0.01)) {
          clearInterval(fadeInterval);
        }
      }, 50);
      return () => clearInterval(fadeInterval);
    }

    // Generate active waveform
    const interval = setInterval(() => {
      targetAmplitudesRef.current = Array.from({ length: barsCount }, (_, i) => {
        const center = barsCount / 2;
        const dist = Math.abs(i - center);
        const falloff = Math.exp(-dist / 2);
        return Math.random() * 0.6 * falloff + 0.2 * falloff;
      });
    }, 100);

    // Animation loop
    const animate = () => {
      setAmplitudes((prev) =>
        prev.map((amp, i) => {
          const target = targetAmplitudesRef.current[i] || 0;
          return amp + (target - amp) * 0.3;
        })
      );
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      clearInterval(interval);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isActive, executive]);

  return (
    <div className={cn("flex items-end gap-0.5", className)} role="img" aria-label={`${executive} voice activity`}>
      {amplitudes.map((amplitude, index) => (
        <motion.div
          key={index}
          animate={{ height: Math.max(2, amplitude * size) }}
          transition={{ duration: 0.05 }}
          className="rounded"
          style={{
            width: Math.max(1, (size * 0.6) / barsCount),
            background: `linear-gradient(to top, var(--axiom-${config.from}), var(--axiom-${config.to}))`,
            opacity: 0.5 + amplitude * 0.5,
          }}
        />
      ))}
    </div>
  );
}

export default VoiceVisualizer;