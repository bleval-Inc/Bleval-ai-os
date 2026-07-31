"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import {
  speak,
  stopSpeaking,
  loadVoices,
  getAxiomVoice,
} from "../../lib/voice/speak";
import {
  getGreeting,
  getWakeGreeting,
} from "../../lib/axiom/system-monitor";
import type { GreetingResult } from "../../lib/axiom/telemetry-types";

// ── Types ──────────────────────────────────────────────────────────────

interface AudioDeviceInfo {
  id: string;
  label: string;
  kind: "audioinput" | "audiooutput";
  active: boolean;
}

// ── VoiceEngine ────────────────────────────────────────────────────────

export default function VoiceEngine() {
  const {
    voiceActive,
    setVoiceActive,
    isListening,
    setIsListening,
    isSpeaking,
    setIsSpeaking,
    isAwake,
    setIsAwake,
    setPendingVoiceCommand,
    addNotification,
  } = useAxiomStore();

  // ── Refs ─────────────────────────────────────────────────────────────
  const wakeRecognitionRef = useRef<any>(null);
  const wakeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wakeRestartTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isAwakeRef = useRef(false);
  const voiceActiveRef = useRef(false);
  const hasGreeted = useRef(false);

  // ── State ────────────────────────────────────────────────────────────
  const [voicesReady, setVoicesReady] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [pttActive, setPttActive] = useState(false);
  const [audioDevices, setAudioDevices] = useState<AudioDeviceInfo[]>([]);
  const [activeMic, setActiveMic] = useState<string>("default");
  const [deviceCount, setDeviceCount] = useState(0);

  // ── Keep refs in sync ────────────────────────────────────────────────
  useEffect(() => { isAwakeRef.current = isAwake; }, [isAwake]);
  useEffect(() => { voiceActiveRef.current = voiceActive; }, [voiceActive]);

  // ── Initialize on Mount ──────────────────────────────────────────────
  useEffect(() => {
    loadVoices().then(() => setVoicesReady(true));
    setVoiceActive(true);
    enumerateAudioDevices();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Audio Device Enumeration & Hot-Plugging ──────────────────────────
  const enumerateAudioDevices = useCallback(async () => {
    try {
      await navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((s) => s.getTracks().forEach((t) => t.stop()));

      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs: AudioDeviceInfo[] = devices
        .filter((d) => d.kind === "audioinput")
        .map((d, i) => ({
          id: d.deviceId,
          label: d.label || `Microphone ${i + 1}`,
          kind: "audioinput" as const,
          active: d.deviceId === activeMic,
        }));
      const outputs: AudioDeviceInfo[] = devices
        .filter((d) => d.kind === "audiooutput")
        .map((d, i) => ({
          id: d.deviceId,
          label: d.label || `Speaker ${i + 1}`,
          kind: "audiooutput" as const,
          active: true,
        }));

      const all = [...inputs, ...outputs];
      setAudioDevices(all);
      setDeviceCount(all.length);
      if (inputs.length > 0 && activeMic === "default") {
        setActiveMic(inputs[0].id);
      }
    } catch { /* permissions denied */ }
  }, [activeMic]);

  useEffect(() => {
    const handler = () => enumerateAudioDevices();
    navigator.mediaDevices?.addEventListener("devicechange", handler);
    return () => navigator.mediaDevices?.removeEventListener("devicechange", handler);
  }, [enumerateAudioDevices]);

  // ── Process Command ─────────────────────────────────────────────────
  const processCommand = useCallback(
    (command: string) => {
      if (wakeTimeoutRef.current) clearTimeout(wakeTimeoutRef.current);
      setIsListening(false);
      setIsAwake(false);
      isAwakeRef.current = false;
      setPttActive(false);

      if (!command.trim()) return;
      setPendingVoiceCommand(command.trim());
      addNotification({
        id: `cmd-${Date.now()}`,
        type: "info",
        title: "Voice command",
        message: `"${command.trim()}"`,
        timestamp: Date.now(),
        read: false,
      });
    },
    [setPendingVoiceCommand, addNotification, setIsListening, setIsAwake]
  );

  // ── Wake Timeout ─────────────────────────────────────────────────────
  const clearWakeTimeout = useCallback(() => {
    if (wakeTimeoutRef.current) {
      clearTimeout(wakeTimeoutRef.current);
      wakeTimeoutRef.current = null;
    }
  }, []);

  const setWakeTimeout = useCallback(() => {
    clearWakeTimeout();
    wakeTimeoutRef.current = setTimeout(() => {
      setIsAwake(false);
      setIsListening(false);
      isAwakeRef.current = false;
      setPttActive(false);
    }, 30000);
  }, [clearWakeTimeout, setIsAwake, setIsListening]);

  // ── Wake AXIOM ──────────────────────────────────────────────────────
  const wakeAxiom = useCallback(async () => {
    clearWakeTimeout();
    setIsAwake(true);
    setIsListening(true);
    isAwakeRef.current = true;

    addNotification({
      id: `wake-${Date.now()}`,
      type: "success",
      title: "AXIOM ON",
      message: "Listening — say your command",
      timestamp: Date.now(),
      read: false,
    });

    try {
      const wake = await getWakeGreeting();
      speak(wake.text, {
        rate: 0.85, pitch: 1.05,
        onStart: () => setIsSpeaking(true),
        onEnd: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false),
      });
    } catch { /* server unavailable — skip audio confirmation */ }

    setWakeTimeout();
  }, [clearWakeTimeout, setIsAwake, setIsListening, setIsSpeaking, addNotification, setWakeTimeout]);

  // ── Boot Greeting ────────────────────────────────────────────────────
  useEffect(() => {
    if (hasGreeted.current || !voiceActive || !voicesReady) return;
    hasGreeted.current = true;

    const t = setTimeout(async () => {
      try {
        const greeting: GreetingResult = await getGreeting(true);
        speak(greeting.text, {
          rate: 0.85, pitch: 1.05,
          onStart: () => setIsSpeaking(true),
          onEnd: () => setIsSpeaking(false),
          onError: () => setIsSpeaking(false),
        });
      } catch {
        const h = new Date().getHours();
        const tod = h < 12 ? "morning" : h < 17 ? "afternoon" : "evening";
        speak(`Good ${tod}. All systems are online and ready to rock.`, {
          rate: 0.85, pitch: 1.05,
          onStart: () => setIsSpeaking(true),
          onEnd: () => setIsSpeaking(false),
          onError: () => setIsSpeaking(false),
        });
      }
    }, 1500);
    return () => clearTimeout(t);
  }, [voiceActive, voicesReady, setIsSpeaking]);

  // ── Continuous Wake-Word Listener (ALWAYS ON) ───────────────────────
  const startWakeListener = useCallback(() => {
    if (typeof window === "undefined") return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;

    if (wakeRecognitionRef.current) {
      try { wakeRecognitionRef.current.stop(); } catch {}
    }

    const r = new SR();
    r.lang = "en-US";
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 3;

    r.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        const t = res[0].transcript.toLowerCase().trim();

        if (!res.isFinal) {
          if (!isAwakeRef.current && (t.includes("axiom on") || t === "axiom")) {
            wakeAxiom();
          }
          continue;
        }

        if (!isAwakeRef.current) {
          if (t.includes("axiom on") || t === "axiom" || (t.includes("axiom") && t.includes("on"))) {
            wakeAxiom();
            const rest = t.replace(/axiom on/g, "").replace(/axiom/g, "").trim();
            if (rest.length > 2) processCommand(rest);
          }
          continue;
        }

        // Already awake — capture via continuous listener too
        let cmd = t.replace(/^axiom on/i, "").replace(/^axiom/i, "").trim();
        if (cmd.length >= 2 || cmd.match(/thank|stop|quit|exit|bye|sleep|goodbye/i)) {
          processCommand(cmd);
        }
      }
    };

    r.onerror = () => {
      if (voiceActiveRef.current) {
        if (wakeRestartTimeout.current) clearTimeout(wakeRestartTimeout.current);
        wakeRestartTimeout.current = setTimeout(startWakeListener, 1000);
      }
    };

    r.onend = () => {
      if (voiceActiveRef.current) {
        if (wakeRestartTimeout.current) clearTimeout(wakeRestartTimeout.current);
        wakeRestartTimeout.current = setTimeout(startWakeListener, 300);
      }
    };

    wakeRecognitionRef.current = r;
    try { r.start(); } catch {}
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Manage wake listener lifecycle
  useEffect(() => {
    if (voiceActive) startWakeListener();
    return () => {
      if (wakeRecognitionRef.current) {
        try { wakeRecognitionRef.current.stop(); } catch {}
        wakeRecognitionRef.current = null;
      }
      if (wakeRestartTimeout.current) clearTimeout(wakeRestartTimeout.current);
    };
  }, [voiceActive, startWakeListener]);

  // ── Push-to-Talk (Click → Listen → Silence → Analyze) ───────────────
  const startPushToTalk = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;

    // Pause wake listener temporarily
    if (wakeRecognitionRef.current) {
      try { wakeRecognitionRef.current.stop(); } catch {}
    }

    setPttActive(true);
    setIsListening(true);
    setIsAwake(true);
    isAwakeRef.current = true;

    let silenceTimer: ReturnType<typeof setTimeout> | null = null;

    const ptt = new SR();
    ptt.lang = "en-US";
    ptt.continuous = true;
    ptt.interimResults = true;
    ptt.maxAlternatives = 3;

    ptt.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        if (res.isFinal) {
          const transcript = res[0].transcript.trim();
          if (silenceTimer) clearTimeout(silenceTimer);
          silenceTimer = setTimeout(() => {
            ptt.stop();
            if (transcript) processCommand(transcript);
          }, 1500); // 1.5s silence = end of speech
        }
      }
    };

    ptt.onerror = () => {
      setPttActive(false);
      setIsListening(false);
      setIsAwake(false);
      isAwakeRef.current = false;
      if (voiceActiveRef.current) startWakeListener();
    };

    ptt.onend = () => {
      setPttActive(false);
      if (silenceTimer) clearTimeout(silenceTimer);
      if (!isAwakeRef.current && voiceActiveRef.current) startWakeListener();
    };

    try { ptt.start(); } catch {
      setPttActive(false);
      setIsListening(false);
      setIsAwake(false);
      isAwakeRef.current = false;
    }
  }, [processCommand, setIsListening, setIsAwake, startWakeListener]);

  // ── Keyboard Shortcut ───────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.code === "KeyV" && e.metaKey && e.shiftKey) {
        e.preventDefault();
        if (!voiceActive) setVoiceActive(true);
        startPushToTalk();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [voiceActive, setVoiceActive, startPushToTalk]);

  // ── Cleanup on Unmount ─────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (wakeRecognitionRef.current) {
        try { wakeRecognitionRef.current.stop(); } catch {}
      }
      if (wakeRestartTimeout.current) clearTimeout(wakeRestartTimeout.current);
      clearWakeTimeout();
      stopSpeaking();
    };
  }, [clearWakeTimeout]);

  // ── Voice Info ─────────────────────────────────────────────────────
  const voiceInfo = voicesReady ? getAxiomVoice()?.name ?? "Browser" : "Loading...";

  // ── RENDER ─────────────────────────────────────────────────────────
  return (
    <>
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
        {/* Speaking indicator */}
        <AnimatePresence>
          {isSpeaking && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2.5 px-3.5 py-2 glass-panel rounded-full"
            >
              <div className="flex items-center gap-[2px]">
                {[0, 1, 2, 3, 4].map((i) => (
                  <span key={i} className="w-0.5 rounded-full bg-indigo-400 animate-waveform"
                    style={{ height: 12 + i * 4, animationDelay: `${i * 80}ms` }} />
                ))}
              </div>
              <span className="text-[10px] font-medium text-[var(--axiom-text-secondary)]">
                AXIOM speaking
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Passive listening — always on */}
        <AnimatePresence>
          {!isAwake && !isSpeaking && voiceActive && !pttActive && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2.5 px-3.5 py-2 glass-panel rounded-full opacity-70"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-60" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-400" />
              </span>
              <div>
                <span className="text-[10px] font-medium text-[var(--axiom-text-secondary)]">
                  Listening for &ldquo;AXIOM ON&rdquo;
                </span>
                <span className="block text-[8px] text-[var(--axiom-text-tertiary)]">
                  {deviceCount} device{deviceCount !== 1 ? "s" : ""}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Active listening (PTT engaged) */}
        <AnimatePresence>
          {(isAwake || pttActive) && !isSpeaking && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2.5 px-3.5 py-2 glass-panel rounded-full"
            >
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
              </span>
              <div>
                <span className="text-[10px] font-medium text-[var(--axiom-text-secondary)]">
                  AXIOM ON
                </span>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)] block">
                  {pttActive ? "Push-to-Talk active — speak now" : "Listening for command..."}
                </span>
              </div>
              <div className="flex items-center gap-[2px]">
                {[0, 1, 2, 3, 4].map((i) => (
                  <span key={i} className="w-0.5 rounded-full bg-green-400 animate-waveform"
                    style={{ height: 8 + i * 3, animationDelay: `${i * 100}ms`, animationDuration: "0.5s" }} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Microphone button — PTT */}
        <button
          onClick={() => {
            if (pttActive || isAwake) return;
            if (!voiceActive) {
              setVoiceActive(true);
              setTimeout(() => startPushToTalk(), 500);
            } else {
              startPushToTalk();
            }
          }}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            pttActive
              ? "bg-green-500 shadow-lg shadow-green-500/30 scale-110 animate-pulse"
              : isAwake
                ? "bg-green-500 shadow-lg shadow-green-500/30 scale-110"
                : voiceActive
                  ? "bg-indigo-500/80 shadow-lg shadow-indigo-500/20 hover:scale-105 hover:bg-indigo-500"
                  : "bg-[var(--axiom-bg-surface)] border border-[var(--axiom-border)] shadow-md hover:shadow-lg hover:scale-105"
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            className={isAwake || pttActive || voiceActive ? "text-white" : "text-[var(--axiom-text-secondary)]"}>
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
            <line x1="8" y1="22" x2="16" y2="22" />
          </svg>
        </button>

        {/* Tooltip */}
        <AnimatePresence>
          {showTooltip && !isAwake && !pttActive && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute bottom-20 right-0 glass-panel px-3 py-2.5 whitespace-nowrap min-w-[220px]"
            >
              <p className="text-[11px] font-medium text-[var(--axiom-text-primary)] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                Voice controls — always listening
              </p>
              <p className="text-[9px] text-[var(--axiom-text-tertiary)] mt-1">
                Say <span className="text-[var(--axiom-accent)] font-mono">&ldquo;AXIOM ON&rdquo;</span>{" "}
                to wake, or click the mic to speak now
              </p>
              <div className="flex items-center justify-between mt-1.5 text-[8px] text-[var(--axiom-text-tertiary)] font-mono">
                <span>⌘⇧V</span>
                <span>{deviceCount} audio devices</span>
              </div>
              <div className="text-[8px] text-[var(--axiom-text-tertiary)] font-mono truncate mt-0.5">
                Mic: {audioDevices.find((d) => d.kind === "audioinput" && d.id === activeMic)?.label || "Default"}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}