"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import {
  speak,
  stopSpeaking,
  loadVoices as loadSpeakVoices,
} from "../../lib/voice/speak";
import { loadAllVoices, getVoiceInfo } from "../../lib/voice/voices";
import {
  requestSpeak,
  releaseSpeaker,
  getActiveSpeaker,
  setArbiterCallbacks,
  interruptCurrentSpeaker,
} from "../../lib/voice/speech-arbiter";
import {
  installActivityTracking,
  useFounderState,
} from "../../lib/voice/founder-detector";
import {
  startSystemHealthPolling,
  acknowledgeEscalation,
  acknowledgeAllEscalations,
  raisePoiAlert,
  raiseRoutineReminder,
  getActiveEscalations,
} from "../../lib/voice/emergency-escalator";
import {
  getGreeting,
  getWakeGreeting,
} from "../../lib/axiom/system-monitor";
import type { GreetingResult } from "../../lib/axiom/telemetry-types";
import type { SpeakerId } from "../../lib/api-types";
import { voice } from "../../lib/api";
import { useVoiceWebSocket, type SpeechUrgency } from "../../lib/voice/voice-websocket";

// Types

export interface AudioDeviceInfo {
  id: string;
  label: string;
  kind: "audioinput" | "audiooutput";
  active: boolean;
}

export type ExecutiveId = "jenson" | "valta_prime" | "yamako" | "axiom";

// Executive wake words and configurations
const EXECUTIVE_CONFIG: Record<ExecutiveId, {
  wakeWords: string[];
  label: string;
  color: string;
  avatar: string;
  shortName: string;
}> = {
  axiom: {
    wakeWords: ["axiom on", "axiom", "hey axiom", "ok axiom"],
    label: "AXIOM",
    color: "bg-indigo-400",
    avatar: "A",
    shortName: "Axiom"
  },
  jenson: {
    wakeWords: ["jenson", "hey jenson", "jensen"],
    label: "Jenson",
    color: "bg-blue-500",
    avatar: "J",
    shortName: "Jenson"
  },
  valta_prime: {
    wakeWords: ["valta prime", "valta", "hey valta", "prime"],
    label: "Valta Prime",
    color: "bg-amber-500",
    avatar: "V",
    shortName: "Valta Prime"
  },
  yamako: {
    wakeWords: ["yamako", "hey yamako"],
    label: "Yamako",
    color: "bg-violet-400",
    avatar: "Y",
    shortName: "Yamako"
  },
};

// Speaker display config (extended for executives)
const SPEAKER_CONFIG: Record<SpeakerId, { label: string; color: string; avatar: string }> = {
  axiom: { label: "AXIOM", color: "bg-indigo-400", avatar: "A" },
  jenson: { label: "Jenson", color: "bg-blue-500", avatar: "J" },
  valta_prime: { label: "Valta Prime", color: "bg-amber-500", avatar: "V" },
  yamako: { label: "Yamako", color: "bg-violet-400", avatar: "Y" },
};

// Helper to detect which executive is being addressed
function detectExecutive(transcript: string): ExecutiveId | null {
  const lower = transcript.toLowerCase();
  for (const [execId, config] of Object.entries(EXECUTIVE_CONFIG)) {
    for (const wakeWord of config.wakeWords) {
      if (lower.includes(wakeWord.toLowerCase())) {
        return execId as ExecutiveId;
      }
    }
  }
  return null;
}

// Wake an executive by name
async function wakeExecutive(execId: ExecutiveId) {
  const config = EXECUTIVE_CONFIG[execId];
  console.log(`[Voice] Waking ${config.label} (${execId})`);

  // Use the speech arbiter to have the executive respond
  const greetings: Record<ExecutiveId, string> = {
    axiom: "Axiom online. How can I help?",
    jenson: "Jenson here. Operations standing by.",
    valta_prime: "Valta Prime active. Markets monitored.",
    yamako: "Yamako ready. Personal ops at your service.",
  };

  await requestSpeak(execId, greetings[execId] || `${config.shortName} online.`, "normal");
}

// VoiceEngine

export default function VoiceEngine() {
  const store = useAxiomStore();

  // Optimized selectors - destructure once to avoid 19 separate subscriptions
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
    setListeningExecutive,
    addNotification,
    activeSpeaker,
    setActiveSpeaker,
    emergencyActive,
    emergencySource,
    emergencyLevel,
    clearEmergency,
    listeningExecutive,
  } = store;

  // Keep refs synced for callbacks
  const isAwakeRef = useRef(isAwake);
  const voiceActiveRef = useRef(voiceActive);
  const listeningExecutiveRef = useRef(listeningExecutive);
  const emergencyActiveRef = useRef(emergencyActive);

  // Refs for timeouts and cleanup
  const wakeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wakeRecognitionRef = useRef<any>(null); // SpeechRecognition (webkit/standard)
  const wakeRestartTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cleanupActivityRef = useRef<() => void | null>(null);
  const cleanupHealthPollRef = useRef<() => void | null>(null);
  const hasGreeted = useRef(false);

  // State
  const [voicesReady, setVoicesReady] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [pttActive, setPttActive] = useState(false);
  const [audioDevices, setAudioDevices] = useState<AudioDeviceInfo[]>([]);
  const [activeMic, setActiveMic] = useState<string>("default");
  const [deviceCount, setDeviceCount] = useState(0);
  const [queueLength, setQueueLength] = useState(0);

  // WebSocket for real-time voice communication
  const [clientId] = useState<string>(() => {
    if (typeof window !== "undefined") {
      let id = sessionStorage.getItem("voice-client-id");
      if (!id) {
        id = `voice-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        sessionStorage.setItem("voice-client-id", id);
      }
      return id;
    }
    return `voice-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  });

  const voiceWs = useVoiceWebSocket({
    clientId,
    autoConnect: false, // We'll connect manually when backend is ready
    onResponse: (message) => {
      if (message.response) {
        requestSpeak(message.executive as SpeakerId, message.response, "normal");
      }
      if (message.workflow_triggered) {
        addNotification({
          id: `wf-${Date.now()}`,
          type: "success",
          title: "Workflow Launched",
          message: `${message.workflow_triggered} has been triggered by ${message.executive}`,
          timestamp: Date.now(),
          read: false,
        });
      }
      if (message.requires_approval && message.approval_id) {
        addNotification({
          id: `appr-${Date.now()}`,
          type: "warning",
          title: "Approval Required",
          message: `Founder approval needed for ${message.action_taken || "action"}`,
          timestamp: Date.now(),
          read: false,
        });
      }
    },
    onSpeak: (message) => {
      if (message.text) {
        requestSpeak(message.executive as SpeakerId, message.text, message.urgency || "normal");
      }
    },
    onStatus: (message) => {
      if (message.executive && typeof message.is_listening === "boolean") {
        if (message.is_listening) {
          setIsListening(true);
          setIsAwake(true);
          setListeningExecutive(message.executive as ExecutiveId);
        } else {
          setIsListening(false);
          setIsAwake(false);
          setListeningExecutive(null);
        }
      }
    },
    onError: (error) => {
      console.error("[Voice WS] Error:", error);
    },
  });

  // Initialize founder detector polling
  useFounderState();

  // Keep refs in sync
  useEffect(() => { isAwakeRef.current = isAwake; }, [isAwake]);
  useEffect(() => { voiceActiveRef.current = voiceActive; }, [voiceActive]);
  useEffect(() => { listeningExecutiveRef.current = listeningExecutive; }, [listeningExecutive]);
  useEffect(() => { emergencyActiveRef.current = emergencyActive; }, [emergencyActive]);
  useEffect(() => {
    // Sync the listening executive state with isAwake and isListening
    if (!isAwake || !isListening) {
      setListeningExecutive(null);
    }
  }, [isAwake, isListening]);

  // Initialize on Mount
  useEffect(() => {
    // Load both speech system voices and executive voice profiles
    Promise.all([loadSpeakVoices(), loadAllVoices()]).then(() => setVoicesReady(true));
    setVoiceActive(true);
    enumerateAudioDevices();

    // Start backend health checker and connect WebSocket when ready
    const checkBackendAndConnect = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/health`);
        if (res.ok) {
          voiceWs.setShouldConnect(true);
        } else {
          voiceWs.setShouldConnect(false);
        }
      } catch {
        voiceWs.setShouldConnect(false);
      }
    };

    checkBackendAndConnect();
    const healthInterval = setInterval(checkBackendAndConnect, 30000);

    // Install activity tracking
    cleanupActivityRef.current = installActivityTracking();

    // Start system health polling for emergency escalations
    cleanupHealthPollRef.current = startSystemHealthPolling();

    // Wire speech arbiter callbacks to sync store
    setArbiterCallbacks({
      onSpeakingStarted: (speaker: SpeakerId) => {
        setActiveSpeaker(speaker);
        setIsSpeaking(true);
      },
      onSpeakingEnded: () => {
        setActiveSpeaker(null);
        setIsSpeaking(false);
      },
      onQueueChanged: (queue) => {
        setQueueLength(queue.length);
      },
    });

    return () => {
      clearInterval(healthInterval);
      cleanupActivityRef.current?.();
      cleanupHealthPollRef.current?.();
      voiceWs.setShouldConnect(false);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Audio Device Enumeration
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

  // Process Command
  const processCommand = useCallback(
    async (command: string) => {
      if (wakeTimeoutRef.current) clearTimeout(wakeTimeoutRef.current);
      setIsListening(false);
      setIsAwake(false);
      isAwakeRef.current = false;
      setPttActive(false);

      if (!command.trim()) return;

      // Interruption keywords — stop any current speech
      const lower = command.trim().toLowerCase();
      if (lower === "stop" || lower === "quiet" || lower === "silence" || lower === "enough") {
        interruptCurrentSpeaker();
        return;
      }

      // Acknowledge emergency keywords
      if (lower.includes("acknowledge") || lower.includes("got it") || lower.includes("understood")) {
        if (emergencyActive) {
          acknowledgeAllEscalations();
          clearEmergency();
        }
      }

      setPendingVoiceCommand(command.trim());

      // Simulate a POI alert for demo purposes if keyword is said
      if (lower.includes("test alert") || lower.includes("test poi")) {
        raisePoiAlert("Test POI", "Gold support level breached at $2,345. Monitor closely.");
      }

      addNotification({
        id: `cmd-${Date.now()}`,
        type: "info",
        title: "Voice command",
        message: `"${command.trim()}"`,
        timestamp: Date.now(),
        read: false,
      });

      // Use WebSocket if connected, otherwise fall back to HTTP
      const listeningExec = (listeningExecutive || "axiom") as ExecutiveId;
      const wakeWord = EXECUTIVE_CONFIG[listeningExec]?.wakeWords[0] || "";

      if (voiceWs.isConnected) {
        // Send via WebSocket for real-time streaming
        voiceWs.sendCommand(command.trim(), listeningExec as "axiom" | "jenson" | "valta_prime" | "yamako", wakeWord, 1.0);
      } else {
        // Fallback to HTTP
        try {
          const response = await voice.command({
            transcript: command.trim(),
            executive: listeningExec,
            wake_word: wakeWord,
            confidence: 1.0,
            timestamp: Date.now(),
          });

          // Speak the executive's response via speech arbiter
          if (response.response) {
            await requestSpeak(listeningExec as SpeakerId, response.response, "normal");
          }

          // If workflow was triggered, notify user
          if (response.workflow_triggered) {
            addNotification({
              id: `wf-${Date.now()}`,
              type: "success",
              title: "Workflow Launched",
              message: `${response.workflow_triggered} has been triggered by ${listeningExec}`,
              timestamp: Date.now(),
              read: false,
            });
          }

          // If approval required
          if (response.requires_approval && response.approval_id) {
            addNotification({
              id: `appr-${Date.now()}`,
              type: "warning",
              title: "Approval Required",
              message: `Founder approval needed for ${response.action_taken || "action"}`,
              timestamp: Date.now(),
              read: false,
            });
          }
        } catch (error) {
          console.error("[Voice] Command processing failed:", error);
          // Fallback to local response
          await requestSpeak("axiom", "Command received, but I couldn't reach the backend.", "normal");
        }
      }
    },
    [
      setPendingVoiceCommand,
      addNotification,
      setIsListening,
      setIsAwake,
      emergencyActive,
      clearEmergency,
      listeningExecutive,
      voiceWs,
    ],
  );

  // Wake Timeout
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

  // Wake AXIOM
  const wakeAxiom = useCallback(async () => {
    clearWakeTimeout();
    setIsAwake(true);
    setIsListening(true);
    setListeningExecutive("axiom");
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
      // Use speech arbiter for wake greeting
      requestSpeak("axiom", wake.text, "normal");
    } catch { /* server unavailable — skip audio confirmation */ }

    setWakeTimeout();
  }, [clearWakeTimeout, setIsAwake, setIsListening, addNotification, setWakeTimeout]);

  // Wake Executive
  const wakeExecutiveByName = useCallback(async (execId: ExecutiveId) => {
    if (execId === "axiom") {
      wakeAxiom();
      return;
    }

    clearWakeTimeout();
    setIsAwake(true);
    setIsListening(true);
    setListeningExecutive(execId);
    isAwakeRef.current = true;

    const config = EXECUTIVE_CONFIG[execId];
    addNotification({
      id: `wake-${execId}-${Date.now()}`,
      type: "success",
      title: `${config.label} ON`,
      message: "Listening — say your command",
      timestamp: Date.now(),
      read: false,
    });

    // Have the executive respond with their voice
    const responses: Record<ExecutiveId, string> = {
      axiom: "",
      jenson: "Jenson here. Operations standing by.",
      valta_prime: "Valta Prime active. Markets monitored.",
      yamako: "Yamako ready. Personal ops at your service.",
    };

    requestSpeak(execId, responses[execId] || `${config.shortName} online.`, "normal");

    setWakeTimeout();
  }, [clearWakeTimeout, setIsAwake, setIsListening, addNotification, setWakeTimeout, wakeAxiom]);

  // Boot Greeting
  useEffect(() => {
    if (hasGreeted.current || !voiceActive || !voicesReady) return;
    hasGreeted.current = true;

    const t = setTimeout(async () => {
      try {
        const greeting: GreetingResult = await getGreeting(true);
        requestSpeak("axiom", greeting.text, "normal");
      } catch {
        const h = new Date().getHours();
        const tod = h < 12 ? "morning" : h < 17 ? "afternoon" : "evening";
        requestSpeak("axiom", `Good ${tod}. All systems are online and ready to rock.`, "normal");
      }
    }, 1500);
    return () => clearTimeout(t);
  }, [voiceActive, voicesReady]);

  // Continuous Wake-Word Listener
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

        // Check for executive wake words in interim results
        if (!res.isFinal) {
          const execId = detectExecutive(t);
          if (execId && !isAwakeRef.current) {
            wakeExecutiveByName(execId);
            const config = EXECUTIVE_CONFIG[execId];
            for (const ww of config.wakeWords) {
              const index = t.indexOf(ww.toLowerCase());
              if (index !== -1) {
                const rest = t.substring(index + ww.length).trim();
                if (rest.length > 2) {
                  processCommand(rest);
                }
              }
            }
          }
          continue;
        }

        // Final result - check for wake words
        const execId = detectExecutive(t);
        if (execId && !isAwakeRef.current) {
          wakeExecutiveByName(execId);
          const config = EXECUTIVE_CONFIG[execId];
          for (const ww of config.wakeWords) {
            const index = t.indexOf(ww.toLowerCase());
            if (index !== -1) {
              const rest = t.substring(index + ww.length).trim();
              if (rest.length >= 2 || rest.match(/thank|stop|quit|exit|bye|sleep|goodbye/i)) {
                processCommand(rest);
              }
            }
          }
          continue;
        }

        // Already awake - process as normal command
        if (isAwakeRef.current) {
          if (t.length >= 2 || t.match(/thank|stop|quit|exit|bye|sleep|goodbye/i)) {
            processCommand(t);
          }
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
        // Increased from 300ms to 2000ms to prevent CPU thrashing
        wakeRestartTimeout.current = setTimeout(startWakeListener, 2000);
      }
    };

    wakeRecognitionRef.current = r;
    try { r.start(); } catch {}
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  // Push-to-Talk
  const startPushToTalk = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;

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
          }, 1500);
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

  // Keyboard Shortcut
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

  // Cleanup on Unmount
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

  // Derived
  const currentSpeakerConfig = activeSpeaker ? SPEAKER_CONFIG[activeSpeaker] : null;
  const voiceInfo = voicesReady ? getVoiceInfo().axiom?.name ?? "Browser" : "Loading...";

  // RENDER
  return (
    <>
      {/* Emergency banner */}
      <AnimatePresence>
        {emergencyActive && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-10 left-0 right-0 z-40 px-4 py-2 bg-red-500/90 backdrop-blur-md flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
              <span className="text-xs font-semibold text-white uppercase tracking-wider">
                {emergencyLevel === "critical" ? "🚨 Emergency" : "⚠️ Alert"}
              </span>
              <span className="text-xs text-white/90">
                {emergencySource === "valta_prime" && "Valta Prime — "}
                {emergencySource === "system" && "System — "}
                {emergencySource === "yamako" && "Yamako — "}
                Requires attention
              </span>
            </div>
            <button
              onClick={() => {
                acknowledgeAllEscalations();
                clearEmergency();
              }}
              className="px-3 py-1 text-[10px] font-medium text-white bg-white/20 rounded-md hover:bg-white/30 transition-colors"
            >
              Acknowledge
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
        {/* Speaking indicator — now shows WHO is speaking */}
        <AnimatePresence>
          {isSpeaking && currentSpeakerConfig && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className={`flex items-center gap-2.5 px-3.5 py-2 glass-panel rounded-full ${
                emergencyActive ? "border border-red-400/50" : ""
              }`}
            >
              {/* Speaker avatar */}
              <div className={`w-5 h-5 rounded-full ${currentSpeakerConfig.color} flex items-center justify-center flex-shrink-0`}>
                <span className="text-[8px] font-bold text-white">{currentSpeakerConfig.avatar}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-medium text-[var(--axiom-text-secondary)]">
                  {currentSpeakerConfig.label} speaking
                </span>
                <div className="flex items-center gap-[2px]">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <span key={i} className="w-0.5 rounded-full bg-indigo-400 animate-waveform"
                      style={{ height: 12 + i * 4, animationDelay: `${i * 80}ms` }} />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Queue length indicator */}
        <AnimatePresence>
          {queueLength > 0 && !isSpeaking && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="glass-panel px-3 py-1.5 rounded-full"
            >
              <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
                {queueLength} message{queueLength > 1 ? "s" : ""} queued
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Passive listening */}
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

        {/* Active listening */}
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

        {/* Microphone button */}
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
          className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 sm:w-12 sm:h-12 ${
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
              <div className="text-[8px] text-[var(--axiom-text-tertiary)] font-mono mt-1">
                Voice: {voiceInfo}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}