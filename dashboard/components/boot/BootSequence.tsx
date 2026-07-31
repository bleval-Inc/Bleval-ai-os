"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBootStore } from "../../lib/store/boot-store";
import { system } from "../../lib/api";
import { speak, stopSpeaking, loadVoices } from "../../lib/voice/speak";
import type { RuntimeStatus } from "../../lib/api-types";

/* ── Boot Particle Canvas ─────────────────────────────────────────── */

function BootParticles({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<
    { x: number; y: number; vx: number; vy: number; size: number; alpha: number }[]
  >([]);
  const animRef = useRef<number>(0);

  useEffect(() => {
    if (!active) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      let opacity = 1;
      const fadeOut = () => {
        opacity -= 0.02;
        if (opacity <= 0) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.globalAlpha = opacity;
        particlesRef.current.forEach((p) => {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
          ctx.fill();
        });
        animRef.current = requestAnimationFrame(fadeOut);
      };
      fadeOut();
      return () => cancelAnimationFrame(animRef.current);
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const count = 80;
    particlesRef.current = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      size: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.3 + 0.1,
    }));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particlesRef.current.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
        ctx.fill();
      });
      animRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [active]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}

/* ── Waveform ──────────────────────────────────────────────────── */

function AxiomWaveform({ active, speaking }: { active: boolean; speaking: boolean }) {
  const bars = 32;

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.2, ease: "easeInOut" }}
          className="flex items-end justify-center gap-[2px] h-10"
        >
          {Array.from({ length: bars }).map((_, i) => {
            const delay = i * 0.05;
            const duration = speaking ? 0.35 : 0.8;
            return (
              <motion.div
                key={i}
                className="w-[2px] rounded-full bg-white/30"
                animate={
                  speaking
                    ? {
                        height: [4, 16 + Math.sin(i * 0.7) * 14, 4],
                        opacity: [0.3, 0.8, 0.3],
                      }
                    : {
                        height: [4, 8, 4],
                        opacity: [0.15, 0.35, 0.15],
                      }
                }
                transition={{
                  duration,
                  repeat: Number.POSITIVE_INFINITY,
                  delay,
                  ease: "easeInOut",
                }}
              />
            );
          })}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ── Loading Line ─────────────────────────────────────────────────── */

function LoadingLine({ progress }: { progress: number }) {
  return (
    <div className="w-64 h-[1.5px] bg-white/8 overflow-hidden rounded-full">
      <motion.div
        className="h-full bg-white/70 rounded-full"
        initial={{ width: "0%" }}
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );
}

/* ── Boot Stage ───────────────────────────────────────────────────── */

function BootStageItem({
  stage,
  index,
  currentStage,
}: {
  stage: { label: string };
  index: number;
  currentStage: number;
}) {
  const isActive = index === currentStage;
  const isCompleted = index < currentStage;

  return (
    <motion.div
      className="flex items-center gap-3"
      initial={{ opacity: 0, y: 8 }}
      animate={{
        opacity: isCompleted ? 0.4 : isActive ? 1 : 0,
        y: 0,
      }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      <div className="w-1.5 h-1.5 rounded-full flex-shrink-0">
        {isCompleted && (
          <motion.div
            className="w-full h-full rounded-full bg-white/50"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
          />
        )}
        {isActive && (
          <motion.div
            className="w-full h-full rounded-full bg-white"
            animate={{ opacity: [1, 0.2, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
        )}
      </div>
      <span
        className={`text-xs font-mono tracking-wider ${
          isCompleted
            ? "text-white/40"
            : isActive
              ? "text-white"
              : "text-white/15"
        }`}
      >
        {stage.label}
      </span>
    </motion.div>
  );
}

/* ── BOOT SEQUENCE ────────────────────────────────────────────────── */

export default function BootSequence({ onComplete }: { onComplete: () => void }) {
  const { bootProgress, currentStage, stages, advanceStage } = useBootStore();

  // Phase states
  const [phase, setPhase] = useState<"silence" | "title" | "loading" | "ready" | "greeting" | "done">("silence");
  const [showTitle, setShowTitle] = useState(false);
  const [showSubtitle, setShowSubtitle] = useState(false);
  const [showStages, setShowStages] = useState(false);
  const [greetingText, setGreetingText] = useState("");
  const [runtimeSummary, setRuntimeSummary] = useState("");
  const [showGreeting, setShowGreeting] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [canSkip, setCanSkip] = useState(false);
  const speechEndedRef = useRef(false);

  // ── Phase 1: Silence → Title ──────────────────────────────────

  useEffect(() => {
    const t1 = setTimeout(() => {
      setShowTitle(true);
      setPhase("title");
    }, 1200); // Full second of silence
    return () => clearTimeout(t1);
  }, []);

  // ── Phase 2: Title → Subtitle → Loading ───────────────────────

  useEffect(() => {
    if (!showTitle) return;
    const t2 = setTimeout(() => setShowSubtitle(true), 1800);
    return () => clearTimeout(t2);
  }, [showTitle]);

  useEffect(() => {
    if (!showSubtitle) return;
    const t3 = setTimeout(() => {
      setShowStages(true);
      setPhase("loading");
    }, 1200);
    return () => clearTimeout(t3);
  }, [showSubtitle]);

  // ── Phase 3: Loading stages (slower, more deliberate) ─────────

  useEffect(() => {
    if (phase !== "loading") return;
    if (currentStage >= stages.length) return;

    const stage = stages[currentStage];
    // Each stage takes 700-1400ms for a relaxed, deliberate pace
    const duration = (stage?.duration ?? 800) + 300;
    const t = setTimeout(() => {
      advanceStage();
      // When we hit the last stage "System Ready", transition to ready phase
      if (currentStage === stages.length - 1) {
        setTimeout(() => {
          setPhase("ready");
        }, 1800); // "System Ready" stays visible for 1.8s
      }
    }, duration);
    return () => clearTimeout(t);
  }, [phase, currentStage, stages, advanceStage]);

  // ── Phase 4: Ready → Fetch runtime → Prepare greeting ────────

  useEffect(() => {
    if (phase !== "ready") return;

    loadVoices();

    // Fetch runtime status
    const fetchData = async () => {
      const hour = new Date().getHours();
      const timeGreeting = hour < 12 ? "Good morning, sir." : hour < 17 ? "Good afternoon, sir." : "Good evening, sir.";
      setGreetingText(timeGreeting);

      try {
        const status = await system.status();
        const parts: string[] = [];
        if (status.health?.overall === "healthy") {
          parts.push("All systems are online and operational.");
        }
        const execCount = status.executives ?? 0;
        if (execCount > 0) {
          parts.push(`${execCount} executives online.`);
        }
        const wfCount = status.workflows_defined ?? 0;
        if (wfCount > 0) {
          parts.push(`${wfCount} workflows available.`);
        }
        parts.push("Ready to rock.");
        setRuntimeSummary(parts.join(" "));
      } catch {
        setRuntimeSummary("All systems are operational.");
      }

      // Transition to greeting after a deliberate pause
      setTimeout(() => {
        setPhase("greeting");
        setShowGreeting(true);
        setCanSkip(true);
      }, 800);
    };

    const t = setTimeout(fetchData, 1200);
    return () => clearTimeout(t);
  }, [phase, stages.length]);

  // ── Phase 5: AXIOM speaks ─────────────────────────────────────

  useEffect(() => {
    if (phase !== "greeting" || !showGreeting) return;
    if (!greetingText || !runtimeSummary) return;

    const fullGreeting = `${greetingText} ${runtimeSummary} What would you like to work on today?`;

    const t = setTimeout(async () => {
      setSpeaking(true);

      await speak(fullGreeting, {
        rate: 0.85,
        pitch: 1.08,
        onStart: () => setSpeaking(true),
        onEnd: () => {
          setSpeaking(false);
          speechEndedRef.current = true;
        },
        onError: () => {
          setSpeaking(false);
          speechEndedRef.current = true;
        },
      });
    }, 600);

    return () => clearTimeout(t);
  }, [phase, showGreeting, greetingText, runtimeSummary]);

  // ── Auto-transition after speech ends ─────────────────────────

  useEffect(() => {
    if (phase !== "greeting" || !speechEndedRef.current) return;

    const t = setTimeout(() => {
      onComplete();
    }, 1500); // Short pause after speech before transition

    return () => clearTimeout(t);
  }, [phase, onComplete]);

  // ── Cleanup ─────────────────────────────────────────────────────

  useEffect(() => {
    return () => {
      stopSpeaking();
    };
  }, []);

  // ── RENDER ──────────────────────────────────────────────────────

  return (
    <div className="fixed inset-0 bg-black flex flex-col items-center justify-center z-[9999] select-none">
      <BootParticles active={phase === "loading"} />

      {/* TITLE */}
      <AnimatePresence>
        {showTitle && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="flex flex-col items-center gap-3 mb-20"
          >
            <motion.span
              className="text-white/90 text-6xl font-light tracking-[0.35em]"
              animate={{ opacity: [0.8, 1, 0.8] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              AXIOM
            </motion.span>

            <AnimatePresence>
              {showSubtitle && (
                <motion.span
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 1.2, delay: 0.3 }}
                  className="text-white/30 text-xs font-mono tracking-[0.3em] uppercase"
                >
                  Artificial Executive Operating System
                </motion.span>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* LOADING */}
      <AnimatePresence>
        {showStages && (phase === "loading" || phase === "ready") && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
            className="flex flex-col items-center gap-6"
          >
            <LoadingLine progress={bootProgress} />

            <div className="flex flex-col gap-2.5 mt-4 min-w-[300px]">
              {stages.map((stage, i) => (
                <BootStageItem
                  key={stage.label}
                  stage={stage}
                  index={i}
                  currentStage={currentStage}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* GREETING */}
      <AnimatePresence>
        {showGreeting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
            className="flex flex-col items-center gap-8 absolute bottom-[28%]"
          >
            <AxiomWaveform active={true} speaking={speaking} />

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="text-center max-w-2xl"
            >
              <p className="text-white/90 text-xl font-light mb-2 tracking-wide">
                {greetingText}
              </p>
              <p className="text-white/50 text-sm font-light leading-relaxed">
                {runtimeSummary}
              </p>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.4 }}
                transition={{ duration: 1, delay: 1.5 }}
                className="text-white/30 text-xs mt-8 font-mono tracking-wider"
              >
                What would you like to work on today?
              </motion.p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* SKIP */}
      {canSkip && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 2 }}
          onClick={() => {
            stopSpeaking();
            onComplete();
          }}
          className="absolute bottom-8 text-white/15 text-[10px] font-mono tracking-[0.3em] uppercase hover:text-white/40 transition-all duration-500"
        >
          Click anywhere to continue
        </motion.button>
      )}

      {/* Click to skip overlay */}
      {canSkip && (
        <div
          className="absolute inset-0 cursor-pointer z-10"
          onClick={() => {
            stopSpeaking();
            onComplete();
          }}
        />
      )}
    </div>
  );
}