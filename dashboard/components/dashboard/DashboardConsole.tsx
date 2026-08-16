"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface Metric {
  label: string;
  value: string | number;
}

interface DashboardConsoleProps {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  metrics: Metric[];
  accentColor: string;
  onClick: () => void;
  isHovered: boolean;
  onHover: (hovered: boolean) => void;
  loading: boolean;
}

export default function DashboardConsole({
  id,
  title,
  subtitle,
  icon,
  metrics,
  accentColor,
  onClick,
  isHovered,
  onHover,
  loading,
}: DashboardConsoleProps) {
  // Holographic blue gradient for all consoles
  const holographicGradient = "from-[#00d4ff] via-[#0099ff] to-[#7c3aed]";
  const holographicBorder = "rgba(0, 212, 255, 0.4)";
  const holographicGlow = "rgba(0, 212, 255, 0.3)";

  // Minimal scroll indicator (hidden default scrollbar, clean right-edge line)
  const scrollRef = useRef<HTMLDivElement>(null);
  const [thumb, setThumb] = useState({ progress: 0, size: 100, visible: false });

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const max = el.scrollHeight - el.clientHeight;
    const visible = max > 0;
    const size = visible ? Math.max(12, (el.clientHeight / el.scrollHeight) * 100) : 100;
    const progress = visible ? el.scrollTop / max : 0;
    setThumb({ progress, size, visible });
  };

  // Recompute the indicator once data arrives so the thumb tracks the real content.
  useEffect(() => {
    handleScroll();
  }, [loading, metrics.length]);

  return (
    <motion.button
      onClick={onClick}
      onMouseEnter={() => onHover(true)}
      onMouseLeave={() => onHover(false)}
      className={cn(
        "relative group w-full h-full min-h-[300px] rounded-2xl overflow-hidden",
        "backdrop-blur-xl",
        "transition-all duration-500 ease-out",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--axiom-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--axiom-bg-base)]",
        "flex flex-col"
      )}
      whileHover={{ y: -6, scale: 1.008 }}
      whileTap={{ scale: 0.992 }}
      style={{
        background: `
          linear-gradient(135deg,
            rgba(0, 212, 255, 0.03) 0%,
            rgba(0, 153, 255, 0.05) 50%,
            rgba(124, 58, 237, 0.04) 100%
          ),
          radial-gradient(ellipse at top left, rgba(0, 212, 255, 0.08) 0%, transparent 60%),
          radial-gradient(ellipse at bottom right, rgba(124, 58, 237, 0.06) 0%, transparent 50%)
        `,
        border: "1px solid rgba(0, 212, 255, 0.15)",
        boxShadow: `
          0 4px 24px -4px rgba(0, 212, 255, 0.08),
          0 0 0 1px rgba(255,255,255,0.02) inset,
          0 1px 0 rgba(255,255,255,0.03) inset
        `,
      }}
      aria-label={`Open ${title} workstation`}
    >
      {/* Holographic edge glow - animated on hover */}
      <motion.div
        className="absolute inset-0 pointer-events-none -z-10 rounded-2xl"
        animate={{
          opacity: isHovered ? 1 : 0.3,
          scale: isHovered ? 1.02 : 1,
          borderColor: holographicBorder,
        }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        style={{
          border: "1px solid rgba(0, 212, 255, 0.1)",
          boxShadow: `
            0 0 40px -5px ${holographicGlow},
            inset 0 0 60px -10px rgba(0, 212, 255, 0.05),
            inset 0 1px 0 rgba(255,255,255,0.03)
          `,
          borderRadius: "inherit",
        }}
      />

      {/* Subtle scanline overlay for holographic feel */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl" style={{ opacity: 0.06, zIndex: 1 }}>
        <div className="absolute inset-0" style={{
          backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 212, 255, 0.15) 2px, rgba(0, 212, 255, 0.15) 4px)`,
          backgroundSize: '100% 4px',
        }} />

        {/* Corner accents */}
        <div className="absolute top-3 left-3 w-8 h-8 border-t border-l border-[var(--axiom-accent)]/30 rounded-tl-xl" />
        <div className="absolute top-3 right-3 w-8 h-8 border-t border-r border-[var(--axiom-accent)]/30 rounded-tr-xl" />
        <div className="absolute bottom-3 left-3 w-8 h-8 border-b border-l border-[var(--axiom-accent)]/30 rounded-bl-xl" />
        <div className="absolute bottom-3 right-3 w-8 h-8 border-b border-r border-[var(--axiom-accent)]/30 rounded-br-xl" />
      </div>

      {/* Content */}
      <div className="relative p-5 flex flex-col h-full z-10">

        {/* Header */}
        <div className="flex items-start justify-between mb-4 pb-3 border-b border-[rgba(0,212,255,0.12)]">
          <div className="flex items-center gap-3">
            {/* Icon with holographic blue gradient */}
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 relative overflow-hidden",
              "bg-gradient-to-br",
              holographicGradient,
              "shadow-[0_0_25px_-5px_rgba(0,212,255,0.5)]"
            )}>
              {/* Inner glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
              <div className="relative z-10">
                {icon}
              </div>
            </div>
            <div>
              <h3 className="text-base md:text-lg font-medium text-[var(--axiom-text-primary)] tracking-tight">
                {title}
              </h3>
              <p className="text-[11px] text-[var(--axiom-text-tertiary)] font-medium uppercase tracking-wider">
                {subtitle}
              </p>
            </div>
          </div>

          {/* Navigate arrow indicator */}
          <motion.div
            className="hidden md:block w-8 h-8 rounded-lg flex items-center justify-center backdrop-blur-sm"
            style={{
              background: "rgba(0, 212, 255, 0.08)",
              border: "1px solid rgba(0, 212, 255, 0.15)",
            }}
            animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : 8 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]/60">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </motion.div>
        </div>

        {/* Metrics Grid - scrollable region (hidden default scrollbar) */}
        <div className="flex-1 min-h-0 relative mt-2">
          <div ref={scrollRef} onScroll={handleScroll} className="absolute inset-0 overflow-y-auto hide-scrollbar pr-1.5">
            <div className="grid grid-cols-2 gap-3 md:gap-4">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <motion.div
                key={i}
                className="h-20 rounded-xl backdrop-blur-sm"
                style={{
                  background: "linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(0, 153, 255, 0.08) 100%)",
                  border: "1px solid rgba(0, 212, 255, 0.1)",
                }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 * i }}
              />
            ))
          ) : metrics.length > 0 ? (
            metrics.map((metric, i) => (
              <motion.div
                key={metric.label}
                className="relative p-3 md:p-4 rounded-xl backdrop-blur-sm group-hover-animate flex flex-col min-h-[96px]"
                style={{
                  background: "linear-gradient(135deg, rgba(0, 212, 255, 0.04) 0%, rgba(0, 153, 255, 0.06) 100%)",
                  border: "1px solid rgba(0, 212, 255, 0.12)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.02)",
                }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.1 + i * 0.05, ease: "easeOut" }}
                whileHover={{
                  borderColor: "rgba(0, 212, 255, 0.35)",
                  boxShadow: `
                    inset 0 1px 0 rgba(255,255,255,0.02),
                    0 8px 32px -8px rgba(0, 212, 255, 0.15)
                  `,
                }}
              >
                {/* Metric accent line top */}
                <div className="absolute top-0 left-4 right-4 h-0.5" style={{
                  background: "linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent)",
                }} />
                <p className="text-[10px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wider mb-1.5">
                  {metric.label}
                </p>
                <p className="text-xl md:text-2xl font-light text-[var(--axiom-text-primary)] tabular-nums mt-auto">
                  {typeof metric.value === "number" ? metric.value.toLocaleString() : metric.value}
                </p>
              </motion.div>
            ))
          ) : (
            <div className="col-span-2 row-span-2 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3" style={{
                background: "linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)",
                border: "1px solid rgba(0, 212, 255, 0.15)",
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]/70">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v6l4 2" />
                </svg>
              </div>
              <p className="text-sm text-[var(--axiom-text-tertiary)]">
                Loading analytics...
              </p>
              <p className="text-[11px] text-[var(--axiom-text-tertiary)]/50 mt-1">
                Connecting to backend...
              </p>
            </div>
          )}
            </div>
          </div>

          {/* Right-edge scroll indicator - minimal line, highlights scroll position */}
          <div className="absolute right-0.5 top-1 bottom-1 w-[2px] rounded-full bg-[var(--axiom-border-hover)]/80 z-20 pointer-events-none overflow-hidden">
            <motion.div
              className="absolute left-0 w-full rounded-full bg-[var(--axiom-accent)]"
              style={{
                height: `${thumb.size}%`,
                top: `${thumb.progress * (100 - thumb.size)}%`,
                boxShadow: "0 0 8px rgba(0,212,255,0.55)",
              }}
              animate={{ opacity: thumb.visible && !loading ? 1 : 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Bottom holographic accent line */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-px"
          style={{
            background: "linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.6), rgba(124, 58, 237, 0.4), transparent)",
          }}
          initial={{ scaleX: 0, opacity: 0 }}
          animate={{ scaleX: isHovered ? 1 : 0, opacity: isHovered ? 1 : 0.3 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </div>
    </motion.button>
  );
}