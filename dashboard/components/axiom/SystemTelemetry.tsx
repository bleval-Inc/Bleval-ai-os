"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { TelemetrySnapshot } from "../../lib/axiom/telemetry-types";
import { getTelemetry } from "../../lib/axiom/system-monitor";

// ── Gauge Component ──────────────────────────────────────────────────────

function Gauge({
  value,
  label,
  unit = "%",
  color = "var(--axiom-accent)",
  warnAt = 80,
  critAt = 95,
  size = "sm",
}: {
  value: number;
  label: string;
  unit?: string;
  color?: string;
  warnAt?: number;
  critAt?: number;
  size?: "sm" | "md";
}) {
  const radius = size === "md" ? 28 : 20;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const strokeColor =
    value >= critAt
      ? "var(--axiom-error)"
      : value >= warnAt
        ? "var(--axiom-warning)"
        : color;

  return (
    <div className="flex flex-col items-center gap-0.5">
      <svg
        width={(radius + 6) * 2}
        height={(radius + 6) * 2}
        className="transform -rotate-90"
      >
        <circle
          cx={radius + 6}
          cy={radius + 6}
          r={radius}
          fill="none"
          stroke="var(--axiom-bg-elevated)"
          strokeWidth={4}
        />
        <circle
          cx={radius + 6}
          cy={radius + 6}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={4}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.3s" }}
        />
      </svg>
      <span
        className={`font-mono font-semibold ${
          size === "md" ? "text-[13px]" : "text-[11px]"
        }`}
        style={{ color: strokeColor }}
      >
        {value.toFixed(0)}
        {unit}
      </span>
      <span className="text-[8px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}

// ── Metric Bar ────────────────────────────────────────────────────────────

function MetricBar({
  value,
  label,
  detail,
  warnAt = 80,
  critAt = 95,
}: {
  value: number;
  label: string;
  detail: string;
  warnAt?: number;
  critAt?: number;
}) {
  const barColor =
    value >= critAt
      ? "var(--axiom-error)"
      : value >= warnAt
        ? "var(--axiom-warning)"
        : "var(--axiom-accent)";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-[var(--axiom-text-secondary)]">{label}</span>
        <span className="font-mono text-[var(--axiom-text-primary)]">
          {detail}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--axiom-bg-elevated)] overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="h-full rounded-full"
          style={{
            backgroundColor: barColor,
            boxShadow: `0 0 6px ${barColor}`,
          }}
        />
      </div>
    </div>
  );
}

// ── Service Badge ─────────────────────────────────────────────────────────

function ServiceBadge({
  name,
  status,
}: {
  name: string;
  status: string;
}) {
  const isRunning = status === "running";
  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-medium ${
        isRunning
          ? "bg-green-500/10 text-green-400"
          : "bg-red-500/10 text-red-400"
      }`}
    >
      <span
        className={`w-1 h-1 rounded-full ${
          isRunning ? "bg-green-400" : "bg-red-400"
        }`}
      />
      {name.length > 14 ? name.slice(0, 14) + "…" : name}
    </span>
  );
}

// ── SystemTelemetry Component ─────────────────────────────────────────────

interface SystemTelemetryProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export default function SystemTelemetry({
  collapsed,
  onToggle,
}: SystemTelemetryProps) {
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [open, setOpen] = useState(!collapsed);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await getTelemetry();
      setSnapshot(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Offline");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      await fetch();
      if (mounted) {
        intervalRef.current = setInterval(() => {
          fetch();
        }, 5000);
      }
    };
    load();
    return () => {
      mounted = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetch]);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    onToggle?.();
  };

  const healthColor =
    snapshot?.health_label === "healthy"
      ? "var(--axiom-success)"
      : snapshot?.health_label === "degraded"
        ? "var(--axiom-warning)"
        : "var(--axiom-error)";

  return (
    <div className="fixed top-16 right-4 z-40">
      {/* Toggle button */}
      <button
        onClick={toggle}
        className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg glass-panel text-[10px] font-medium
          hover:bg-[var(--axiom-bg-elevated)] transition-colors mb-1 ml-auto"
      >
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: healthColor }}
        />
        <span className="text-[var(--axiom-text-secondary)]">
          {open ? "Hide Telemetry" : "System"}
        </span>
        {snapshot && !open && (
          <span className="font-mono text-[9px] text-[var(--axiom-text-tertiary)]">
            {snapshot.cpu.percent.toFixed(0)}%
          </span>
        )}
      </button>

      {/* Panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="glass-panel w-[280px] overflow-hidden"
          >
            {/* Header */}
            <div className="px-3 py-2 border-b border-[var(--axiom-border)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold text-[var(--axiom-text-primary)] tracking-wide uppercase">
                  System Telemetry
                </span>
                <span
                  className="text-[8px] font-mono font-semibold px-1.5 py-0.5 rounded"
                  style={{
                    color: healthColor,
                    backgroundColor: `${healthColor}15`,
                  }}
                >
                  {snapshot?.health_label || "—"}
                </span>
              </div>
              <button
                onClick={fetch}
                className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                  <path d="M3 3v5h5" />
                  <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                  <path d="M21 21v-5h-5" />
                </svg>
              </button>
            </div>

            {/* Loading */}
            {loading && (
              <div className="p-6 flex items-center justify-center">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse"
                      style={{ animationDelay: `${i * 200}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Error */}
            {error && !snapshot && !loading && (
              <div className="p-4 text-center">
                <p className="text-[10px] text-[var(--axiom-error)] mb-2">
                  {error}
                </p>
                <button
                  onClick={fetch}
                  className="text-[9px] text-[var(--axiom-accent)] underline"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Data */}
            {snapshot && (
              <div className="p-3 space-y-3">
                {/* Gauges row */}
                <div className="flex justify-around">
                  <Gauge
                    value={snapshot.cpu.percent}
                    label="CPU"
                    color="var(--axiom-accent)"
                    size="sm"
                  />
                  <Gauge
                    value={snapshot.memory.percent}
                    label="RAM"
                    color="var(--axiom-info)"
                    warnAt={75}
                    size="sm"
                  />
                  <Gauge
                    value={snapshot.disk.percent}
                    label="DISK"
                    color="var(--axiom-success)"
                    warnAt={80}
                    critAt={92}
                    size="sm"
                  />
                  {snapshot.temperature.cpu_temp_c != null && (
                    <Gauge
                      value={Math.min(
                        100,
                        ((snapshot.temperature.cpu_temp_c - 30) / 60) * 100
                      )}
                      label="TEMP"
                      unit="°"
                      color="var(--axiom-warning)"
                      warnAt={60}
                      critAt={80}
                      size="sm"
                    />
                  )}
                </div>

                {/* Detailed bars */}
                <div className="space-y-2 pt-2 border-t border-[var(--axiom-border)]">
                  <MetricBar
                    value={snapshot.memory.percent}
                    label="RAM"
                    detail={`${snapshot.memory.used_gb.toFixed(1)} / ${snapshot.memory.total_gb.toFixed(1)} GB`}
                    warnAt={75}
                  />
                  <MetricBar
                    value={snapshot.disk.percent}
                    label="Disk"
                    detail={`${snapshot.disk.used_gb.toFixed(1)} / ${snapshot.disk.total_gb.toFixed(1)} GB`}
                    warnAt={80}
                    critAt={92}
                  />
                </div>

                {/* Network & Processes */}
                <div className="flex justify-between text-[9px] text-[var(--axiom-text-tertiary)] font-mono pt-1 border-t border-[var(--axiom-border)]">
                  <span>
                    ↓{snapshot.network.bytes_recv_mb.toFixed(0)} MB
                  </span>
                  <span>
                    ↑{snapshot.network.bytes_sent_mb.toFixed(0)} MB
                  </span>
                  <span>{snapshot.processes} proc</span>
                  <span>
                    {Math.floor(snapshot.uptime_seconds / 3600)}h{" "}
                    {Math.floor((snapshot.uptime_seconds % 3600) / 60)}m
                  </span>
                </div>

                {/* Services */}
                {snapshot.services.length > 0 && (
                  <div className="pt-1 border-t border-[var(--axiom-border)]">
                    <div className="text-[8px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider mb-1">
                      Services
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {snapshot.services.slice(0, 8).map((s) => (
                        <ServiceBadge
                          key={s.name}
                          name={s.name}
                          status={s.status}
                        />
                      ))}
                      {snapshot.services.length > 8 && (
                        <span className="text-[8px] text-[var(--axiom-text-tertiary)] self-center">
                          +{snapshot.services.length - 8}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Hostname footer */}
                <div className="text-[7px] text-[var(--axiom-text-tertiary)] text-center pt-1 border-t border-[var(--axiom-border)] font-mono">
                  {snapshot.hostname} &middot;{" "}
                  {new Date(snapshot.timestamp * 1000).toLocaleTimeString()}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}