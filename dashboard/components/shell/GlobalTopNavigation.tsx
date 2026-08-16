"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type WorkstationId } from "../../lib/store/axiom-store";
import type { FounderAvailability } from "../../lib/api-types";
import { cn } from "../../lib/utils";
import NotificationCenter from "../workspace/NotificationCenter";

const WORKSTATION_CONFIG: Record<WorkstationId, { label: string; shortLabel: string; icon: React.ReactNode }> = {
  axiom: {
    label: "AXIOM",
    shortLabel: "AXIOM",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    ),
  },
  bleval: {
    label: "BLEVAL INC",
    shortLabel: "BLEVAL",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
  },
  valta: {
    label: "HOUSE OF VALTA",
    shortLabel: "VALTA",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12V7H5V2H1v5H1" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  personal: {
    label: "PERSONAL",
    shortLabel: "PERSONAL",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  boardroom: {
    label: "BOARDROOM",
    shortLabel: "BOARDROOM",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  system: {
    label: "SYSTEM",
    shortLabel: "SYSTEM",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
    ),
  },
  settings: {
    label: "SETTINGS",
    shortLabel: "SETTINGS",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
      </svg>
    ),
  },
};

const AVAILABILITY_CONFIG: Record<FounderAvailability, { label: string; color: string; dot: string }> = {
  available: { label: "Online", color: "text-emerald-400", dot: "bg-emerald-400" },
  in_meeting: { label: "Away", color: "text-amber-400", dot: "bg-amber-400" },
  in_trade: { label: "Busy", color: "text-blue-400", dot: "bg-blue-400" },
  sleeping: { label: "Offline", color: "text-violet-400", dot: "bg-violet-400" },
  training: { label: "Busy", color: "text-orange-400", dot: "bg-orange-400" },
  studying: { label: "Busy", color: "text-cyan-400", dot: "bg-cyan-400" },
  do_not_disturb: { label: "DND", color: "text-red-400", dot: "bg-red-400" },
  unknown: { label: "Offline", color: "text-zinc-500", dot: "bg-zinc-500" },
};

// ── Holographic Weather Icons ────────────────────────────────────────────
function HolographicWeatherIcon({ condition, temp }: { condition: string; temp: string }) {
  const [time, setTime] = useState(0);

  useEffect(() => {
    const id = requestAnimationFrame(function animate(t) {
      setTime(t / 1000);
      requestAnimationFrame(animate);
    });
    return () => cancelAnimationFrame(id);
  }, []);

  const c = condition.toLowerCase();
  const isSunny = c.includes("sunny") || c.includes("clear") || c === "☀";
  const isCloudy = c.includes("cloud") || c.includes("overcast") || c === "☁";
  const isRainy = c.includes("rain") || c.includes("drizzle") || c === "🌧";
  const isStormy = c.includes("storm") || c.includes("thunder") || c === "⛈";
  const isSnowy = c.includes("snow") || c.includes("flake") || c === "❄";
  const isPartlyCloudy = c.includes("partly") || (isSunny && isCloudy);

  const glowColor = "rgba(120, 170, 255, 0.6)";
  const pulse = Math.sin(time * 2) * 0.15 + 1;

  return (
    <span className="inline-flex items-center gap-1" style={{ filter: `drop-shadow(0 0 ${2 * pulse}px ${glowColor})` }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]/80">
        {/* Sunny / Partly Cloudy */}
        {(isSunny || isPartlyCloudy) && (
          <g>
            <circle cx="12" cy="12" r="4" className="text-yellow-300/90" style={{ filter: `drop-shadow(0 0 ${3 * pulse}px rgba(255, 220, 100, 0.8))` }} />
            {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => (
              <line
                key={angle}
                x1={12 + Math.cos((angle * Math.PI) / 180) * 6}
                y1={12 + Math.sin((angle * Math.PI) / 180) * 6}
                x2={12 + Math.cos((angle * Math.PI) / 180) * 10}
                y2={12 + Math.sin((angle * Math.PI) / 180) * 10}
                className="text-yellow-300/60"
                style={{
                  transformOrigin: "12px 12px",
                  animation: `spin ${20}s linear infinite`,
                  opacity: 0.5 + 0.3 * Math.sin(time + angle * 0.1),
                }}
              />
            ))}
          </g>
        )}

        {/* Cloudy / Partly Cloudy */}
        {(isCloudy || isPartlyCloudy) && (
          <g style={{ opacity: isPartlyCloudy ? 0.7 : 1 }}>
            <path d="M18 16a4 4 0 0 0-8 0" strokeWidth="1.5" className="text-slate-300/60" />
            <path d="M8 16c0-2.5 2-4 5-4s5 1.5 5 4" strokeWidth="1.5" className="text-slate-300/60" />
            <ellipse cx="12" cy="18" rx="6" ry="2" fill="url(#cloudGradient)" opacity="0.3" />
            <defs>
              <linearGradient id="cloudGradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#7aa0ff" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.2" />
              </linearGradient>
            </defs>
            {/* Drifting particles */}
            {[1, 2, 3].map((i) => (
              <circle
                key={i}
                cx={10 + i * 3 + Math.sin(time * 0.5 + i) * 2}
                cy={16 + Math.cos(time * 0.3 + i) * 1.5}
                r={0.8}
                fill="#7aa0ff"
                opacity={0.3 + 0.2 * Math.sin(time + i)}
              />
            ))}
          </g>
        )}

        {/* Rain */}
        {isRainy && (
          <g>
            <path d="M8 14c0-2.5 2-4 5-4s5 1.5 5 4" strokeWidth="1.5" className="text-slate-300/60" />
            {[1, 2, 3, 4].map((i) => (
              <motion.line
                key={i}
                x1={6 + i * 3.5}
                y1={16}
                x2={6 + i * 3.5 - 1}
                y2={22}
                stroke="#7aa0ff"
                strokeWidth="1"
                opacity={0.5 + 0.3 * Math.sin(time * 3 + i)}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: [0.5, 1, 0.5], y: [0, 6, 0] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15, ease: "linear" }}
              />
            ))}
          </g>
        )}

        {/* Storm */}
        {isStormy && (
          <g>
            <path d="M8 14c0-2.5 2-4 5-4s5 1.5 5 4" strokeWidth="1.5" className="text-slate-400/70" />
            <motion.path
              d="M10 16l2 4-1.5 3 3-4"
              stroke="#fbbf24"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0, 1, 0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: [0, 0, 1, 1] }}
            />
            <motion.path
              d="M16 16l-2 4 1.5 3-3-4"
              stroke="#fbbf24"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 0, 1, 0, 1, 0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.5, ease: [0, 0, 1, 1] }}
            />
          </g>
        )}

        {/* Snow */}
        {isSnowy && (
          <g>
            <path d="M8 14c0-2.5 2-4 5-4s5 1.5 5 4" strokeWidth="1.5" className="text-slate-200/60" />
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <motion.circle
                key={i}
                cx={6 + i * 2.5 + Math.sin(time * 0.7 + i * 2) * 1.5}
                cy={16 + ((time * 30 + i * 40) % 12)}
                r={1}
                fill="#ffffff"
                opacity={0.4 + 0.3 * Math.sin(time + i)}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: [0.4, 1, 0.4], y: [0, 12, 0] }}
                transition={{ duration: 2, repeat: Infinity, delay: i * 0.2, ease: "easeInOut" }}
              />
            ))}
          </g>
        )}

        {/* Default / Unknown */}
        {!isSunny && !isCloudy && !isRainy && !isStormy && !isSnowy && !isPartlyCloudy && (
          <g>
            <circle cx="12" cy="12" r="4" className="text-[var(--axiom-accent)]/50" style={{ filter: `drop-shadow(0 0 ${2 * pulse}px ${glowColor})` }} />
            <path d="M12 8v4M12 16h.01" strokeWidth="2" className="text-[var(--axiom-accent)]/60" />
          </g>
        )}
      </svg>
      <span className="text-[11px] font-medium font-mono tabular-nums text-[var(--axiom-text-secondary)]">
        {temp}
      </span>
    </span>
  );
}

// ── Holographic Date/Time ────────────────────────────────────────────────
function HolographicDateTime({ date, time }: { date: string; time: string }) {
  const [t, setT] = useState(0);

  useEffect(() => {
    const id = requestAnimationFrame(function animate(ts) {
      setT(ts / 1000);
      requestAnimationFrame(animate);
    });
    return () => cancelAnimationFrame(id);
  }, []);

  const pulse = Math.sin(t * 1.5) * 0.08 + 1;
  const glow = `rgba(120, 170, 255, ${0.15 + 0.1 * Math.sin(t * 0.7)})`;

  return (
    <>
      <span
        className="text-[11px] font-medium font-mono tabular-nums hidden sm:inline-flex items-center gap-1"
        style={{
          color: "var(--axiom-text-tertiary)",
          textShadow: `0 0 ${2 * pulse}px ${glow}, 0 0 ${4 * pulse}px ${glow}`,
          transition: "text-shadow 0.5s ease-out",
        }}
        suppressHydrationWarning
      >
        {date}
      </span>
      <span
        className="text-sm font-mono tabular-nums font-medium hidden lg:inline-flex items-center gap-1"
        style={{
          color: "var(--axiom-text-primary)",
          textShadow: `0 0 ${2 * pulse}px ${glow}, 0 0 ${4 * pulse}px ${glow}`,
          transition: "text-shadow 0.5s ease-out",
        }}
        suppressHydrationWarning
      >
        {time}
      </span>
    </>
  );
}

export function GlobalTopNavigation() {
  const {
    activeWorkstation,
    setActiveWorkstation,
    voiceActive,
    setVoiceActive,
    isAwake,
    isListening,
    isSpeaking,
    notifications,
    notificationPanelOpen,
    toggleNotificationPanel,
    founderAvailability,
    founderManualOverride,
    emergencyActive,
    emergencyLevel,
    clearEmergency,
  } = useAxiomStore();

  const [currentTime, setCurrentTime] = useState<Date | null>(null);
  const [weather, setWeather] = useState({ condition: "Partly Cloudy", temp: "22°C" });
  const [mounted, setMounted] = useState(false);
  const notificationRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const [notificationMenuOpen, setNotificationMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  // Update time every second - client side only
  useEffect(() => {
    setMounted(true);
    const now = new Date();
    setCurrentTime(now);
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Click outside handlers
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(e.target as Node)) {
        setNotificationMenuOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const formatTime = (date: Date | null) => {
    if (!date) return "";
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  };

  const formatDate = (date: Date | null) => {
    if (!date) return "";
    return date.toLocaleDateString([], { month: "short", day: "numeric" }).toUpperCase();
  };

  // Fallback for activeWorkstation if not in config
  const activeConfig = WORKSTATION_CONFIG[activeWorkstation as keyof typeof WORKSTATION_CONFIG] || WORKSTATION_CONFIG.axiom;
  const unreadCount = notifications.filter((n) => !n.read && (!n.snoozedUntil || n.snoozedUntil <= Date.now())).length;
  const availabilityConfig = AVAILABILITY_CONFIG[founderAvailability] ?? AVAILABILITY_CONFIG.unknown;
  const isDnd = founderManualOverride === "do_not_disturb";

  // Voice status - no OFFLINE text label, just icon state
  const getVoiceStatus = () => {
    if (isListening) return { color: "text-[var(--axiom-success)]", pulse: true, icon: "listening" as const };
    if (isSpeaking) return { color: "text-[var(--axiom-accent)]", pulse: true, icon: "speaking" as const };
    if (isAwake) return { color: "text-[var(--axiom-accent)]", pulse: true, icon: "awake" as const };
    if (voiceActive) return { color: "text-[var(--axiom-accent)]", pulse: false, icon: "ready" as const };
    return { color: "text-[var(--axiom-text-tertiary)]", pulse: false, icon: "offline" as const };
  };

  const voiceStatus = getVoiceStatus();

  // SSR-safe date/time that matches client after hydration
  const ssrSafeDate = mounted && currentTime ? formatDate(currentTime) : "--";
  const ssrSafeTime = mounted && currentTime ? formatTime(currentTime) : "--:--";

  return (
    <div>
      {/* Emergency banner (fixed at top) */}
      <AnimatePresence>
        {emergencyActive && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 28 }}
            exit={{ opacity: 0, height: 0 }}
            className="fixed top-0 left-0 right-0 z-50 h-7 bg-red-500/90 backdrop-blur-md flex items-center justify-between px-4"
          >
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              <span className="text-[10px] font-semibold text-white uppercase tracking-wider">
                {emergencyLevel === "critical" ? "🚨 Emergency" : "⚠️ Alert"}
              </span>
            </div>
            <button
              onClick={clearEmergency}
              className="px-2 py-0.5 text-[9px] font-medium text-white bg-white/20 rounded-md hover:bg-white/30 transition-colors"
            >
              Acknowledge
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main navigation bar - single seamless glass surface, establishes the top boundary */}
      <div className="relative z-40 flex-shrink-0 h-11">
        <div className="h-full flex items-center justify-between px-4 bg-[var(--axiom-bg-glass)] backdrop-blur-xl border-b border-[var(--axiom-border)]/50">
          {/* LEFT: AXIOM Symbol + Identity */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveWorkstation("axiom")}
              className="flex items-center gap-2 group px-2 py-1.5 rounded-lg transition-all duration-150 hover:bg-[var(--axiom-bg-elevated)]/50"
              title="AXIOM Workstation"
              aria-label="AXIOM Workstation"
            >
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-[var(--axiom-accent)] to-[var(--axiom-violet)]">
                {activeConfig.icon}
              </div>
              <span className="text-xs font-semibold text-[var(--axiom-text-primary)] tracking-widest uppercase hidden sm:block">
                {activeConfig.shortLabel}
              </span>
            </button>
          </div>

          {/* RIGHT: Weather | Date | Time | Voice | Notifications | Founder Profile */}
          <div className="flex items-center gap-3">
            {/* Weather - Holographic */}
            <HolographicWeatherIcon condition={weather.condition} temp={weather.temp} />

            {/* Date & Time - Holographic */}
            <HolographicDateTime date={ssrSafeDate} time={ssrSafeTime} />

            {/* Voice Status - Icon only, no OFFLINE text label */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setVoiceActive(!voiceActive)}
                className="relative flex items-center gap-1.5 p-1.5 rounded-lg transition-all duration-150"
                title={`AXIOM Voice: ${voiceStatus.icon.toUpperCase()}`}
                aria-label={`AXIOM Voice: ${voiceStatus.icon.toUpperCase()}`}
              >
                <div className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200"
                  style={{ background: voiceStatus.pulse ? "var(--axiom-accent-glow)" : "transparent" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                    className={cn("transition-colors duration-200", voiceStatus.color)}>
                    {voiceActive ? (
                      <>
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                        <line x1="12" y1="19" x2="12" y2="22" />
                      </>
                    ) : (
                      <>
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                        <line x1="9" y1="9" x2="15" y2="15" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                        <line x1="12" y1="19" x2="12" y2="22" />
                        <line x1="8" y1="22" x2="16" y2="22" />
                      </>
                    )}
                  </svg>
                </div>
                {voiceStatus.pulse && (
                  <motion.span
                    className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[var(--axiom-accent)]"
                    animate={{ scale: [1, 1.3, 1], opacity: [0.8, 0.4, 0.8] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                  />
                )}
              </button>
            </div>

            {/* Vertical divider */}
            <div className="w-px h-6 bg-[var(--axiom-border)] hidden sm:block" />

            {/* Notifications */}
            <div className="relative" ref={notificationRef}>
              <button
                onClick={() => setNotificationMenuOpen(!notificationMenuOpen)}
                className={cn(
                  "relative p-1.5 rounded-lg transition-all duration-150",
                  notificationMenuOpen
                    ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
                )}
                title="Notifications"
                aria-label="Notifications"
                aria-expanded={notificationMenuOpen}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
                {unreadCount > 0 && (
                  <motion.span
                    key={unreadCount}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-400 rounded-full text-[8px] font-bold text-white flex items-center justify-center"
                  >
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </motion.span>
                )}
              </button>

              <AnimatePresence>
                {notificationMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.95 }}
                    transition={{ duration: 0.15, ease: "easeOut" }}
                    className="absolute right-0 top-full mt-2 w-80 glass-panel border border-[var(--axiom-border)] rounded-xl shadow-xl overflow-hidden z-50"
                    role="menu"
                  >
                    <NotificationCenter />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Founder Profile */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                className="flex items-center gap-2 p-1 rounded-lg transition-all duration-150 hover:bg-[var(--axiom-bg-elevated)]"
                title={`Founder: ${availabilityConfig.label}`}
                aria-label={`Founder: ${availabilityConfig.label}`}
                aria-expanded={profileMenuOpen}
              >
                <div className="relative w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-[var(--axiom-accent)] to-[var(--axiom-violet)]">
                  <span className="text-[11px] font-semibold text-white">F</span>
                  <span className={`absolute bottom-0 right-0 w-2 h-2 rounded-full border-2 border-[var(--axiom-bg-base)] ${availabilityConfig.dot}`} />
                </div>
                <span className={`text-[11px] font-medium hidden md:inline ${availabilityConfig.color}`}>
                  {isDnd ? "DND" : availabilityConfig.label}
                </span>
              </button>

              <AnimatePresence>
                {profileMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.95 }}
                    transition={{ duration: 0.15, ease: "easeOut" }}
                    className="absolute right-0 top-full mt-2 w-56 glass-panel border border-[var(--axiom-border)] rounded-xl shadow-xl overflow-hidden z-50"
                    role="menu"
                  >
                    <div className="p-3 border-b border-[var(--axiom-border)]">
                      <p className="text-sm font-semibold text-[var(--axiom-text-primary)]">Founder</p>
                      <p className="text-[11px] text-[var(--axiom-text-tertiary)]">Tounga Saidou</p>
                    </div>
                    <div className="p-2 space-y-1">
                      {Object.entries(AVAILABILITY_CONFIG).map(([key, config]) => (
                        <button
                          key={key}
                          onClick={() => useAxiomStore.getState().setFounderAvailability(key as FounderAvailability)}
                          className={cn(
                            "w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors",
                            founderAvailability === key
                              ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                              : "text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] hover:text-[var(--axiom-text-primary)]"
                          )}
                          role="menuitem"
                        >
                          <span className={`w-2 h-2 rounded-full ${config.dot}`} />
                          <span className={config.color}>{config.label}</span>
                        </button>
                      ))}
                    </div>
                    <div className="p-2 border-t border-[var(--axiom-border)]">
                      <button
                        onClick={() => useAxiomStore.getState().setFounderManualOverride(isDnd ? null : "do_not_disturb")}
                        className={cn(
                          "w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors",
                          isDnd
                            ? "text-red-400 bg-red-400/10 hover:bg-red-400/20"
                            : "text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] hover:text-[var(--axiom-text-primary)]"
                        )}
                        role="menuitem"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                        </svg>
                        {isDnd ? "Disable Do Not Disturb" : "Enable Do Not Disturb"}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GlobalTopNavigation;