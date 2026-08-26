"use client";

import { cn } from "@/lib/utils";
import type { BrExecutive, BrVoiceState } from "./boardroom-data";

// ── Shared Boardroom presentational primitives ────────────────────────
// Minimal, premium, AXIOM-consistent. No gaming chrome, no oversized glow.

/** Elegant voice-activity waveform — static low bars idle, pulse when active. */
export function Waveform({
  active,
  color,
  bars = 9,
  className,
}: {
  active: boolean;
  color?: string;
  bars?: number;
  className?: string;
}) {
  return (
    <div className={cn("flex items-end gap-[3px] h-4", className)} aria-hidden="true">
      {Array.from({ length: bars }).map((_, i) => (
        <span
          key={i}
          className={cn("w-[3px] rounded-full transition-all duration-300", color ?? "bg-[var(--axiom-text-tertiary)]")}
          style={
            active
              ? { animation: `waveform 0.9s ease-in-out ${i * 0.09}s infinite`, height: "16px" }
              : { height: i % 3 === 0 ? "7px" : "4px", transform: "none" }
          }
        />
      ))}
    </div>
  );
}

/** Executive monogram in a tinted ring. */
export function ExecutiveAvatar({
  exec,
  active,
  size = "md",
}: {
  exec: BrExecutive;
  active?: boolean;
  size?: "sm" | "md" | "lg";
}) {
  const dim = size === "lg" ? "w-12 h-12 text-sm" : size === "sm" ? "w-7 h-7 text-[10px]" : "w-9 h-9 text-xs";
  return (
    <div
      className={cn(
        "relative flex-shrink-0 rounded-full flex items-center justify-center font-semibold tracking-wide",
        dim,
        active ? cn("ring-1 ring-offset-2", exec.ring) : "ring-1 ring-[var(--axiom-border)] dark:ring-white/10",
      )}
      style={{ background: "var(--axiom-bg-elevated)", boxShadow: active ? `0 0 18px -4px var(--axiom-accent-glow)` : undefined }}
    >
      <span className={cn(exec.text)}>{exec.initials}</span>
      <span
        className={cn(
          "absolute -right-0.5 -bottom-0.5 w-2.5 h-2.5 rounded-full border-2 border-[var(--axiom-bg-base)]",
          exec.dot,
        )}
        style={{ opacity: active ? 1 : 0.35 }}
      />
    </div>
  );
}

const STATUS_STYLE: Record<BrVoiceState, string> = {
  IDLE: "text-[var(--axiom-text-tertiary)] border-[var(--axiom-border-hover)] bg-white/5",
  LISTENING: "text-[var(--axiom-info)] border-[#4da3ff]/25 bg-[#4da3ff]/10",
  THINKING: "text-[var(--axiom-warning)] border-[#ffb830]/25 bg-[#ffb830]/10",
  SPEAKING: "text-[var(--axiom-accent)] border-[#6d7cff]/30 bg-[#6d7cff]/10",
  CONNECTING: "text-[var(--axiom-text-tertiary)] border-[var(--axiom-border-hover)] bg-white/5",
};

const STATUS_DOT: Record<BrVoiceState, string> = {
  IDLE: "bg-[var(--axiom-text-tertiary)]",
  LISTENING: "bg-[var(--axiom-info)]",
  THINKING: "bg-[var(--axiom-warning)]",
  SPEAKING: "bg-[var(--axiom-accent)]",
  CONNECTING: "bg-[var(--axiom-text-tertiary)] animate-pulse",
};

/** Small pill showing an executive's live voice state. */
export function StatusChip({ state, label }: { state: BrVoiceState; label?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[9px] font-medium tracking-wide", STATUS_STYLE[state])}>
      <span className={cn("w-1 h-1 rounded-full", STATUS_DOT[state], (state === "SPEAKING" || state === "CONNECTING") && "animate-pulse")} />
      {label ?? state}
    </span>
  );
}

/** Labeled section panel used across landing / meeting / notes. */
export function BdSection({ title, children, right, className }: { title: string; children: React.ReactNode; right?: React.ReactNode; className?: string }) {
  return (
    <section
      className={cn("rounded-xl border flex flex-col min-w-0 min-h-0", className)}
      style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(13,16,20,0.4)" }}
    >
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)] flex-shrink-0">
        <h3 className="text-[10px] font-semibold tracking-[0.14em] text-[var(--axiom-text-tertiary)] uppercase">{title}</h3>
        {right}
      </header>
      {children}
    </section>
  );
}

/** Quiet primary button. */
export function BdButton({
  children,
  onClick,
  variant = "ghost",
  disabled,
  className,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost" | "danger";
  disabled?: boolean;
  className?: string;
}) {
  const base =
    "inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg text-[11px] font-medium tracking-wide transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none";
  const variants: Record<string, string> = {
    primary:
      "text-white shadow-sm active:scale-[0.98]",
    ghost:
      "text-[var(--axiom-text-secondary)] border border-[var(--axiom-border-hover)] hover:text-[var(--axiom-text-primary)] hover:bg-white/5 active:scale-[0.98]",
    danger:
      "text-[var(--axiom-error)] border border-[var(--axiom-error)]/30 hover:bg-[var(--axiom-error)]/10 active:scale-[0.98]",
  };
  return (
    <button onClick={onClick} disabled={disabled} className={cn(base, variants[variant], className)} style={variant === "primary" ? { background: "linear-gradient(135deg, var(--axiom-accent), var(--axiom-violet))" } : undefined}>
      {children}
    </button>
  );
}

/** Squared icon control-button used in the meeting control bar. */
export function IconButton({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      aria-label={label}
      className={cn(
        "flex flex-col items-center justify-center gap-1 w-14 py-2 rounded-xl border transition-all duration-150 active:scale-95",
        active
          ? "border-[#6d7cff]/30 bg-[#6d7cff]/10 text-[var(--axiom-accent)]"
          : "border-[var(--axiom-border-hover)] bg-white/[0.02] text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-text-primary)] hover:bg-white/5",
      )}
    >
      {children}
    </button>
  );
}

/** Terminal-style divider label. */
export function MonoLabel({ children }: { children: React.ReactNode }) {
  return <span className="font-mono text-[9px] tracking-[0.18em] text-[var(--axiom-text-tertiary)]">{children}</span>;
}