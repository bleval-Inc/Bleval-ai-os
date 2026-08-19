"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion } from "framer-motion";
import type { TelemetrySnapshot } from "@/lib/axiom/telemetry-types";
import { getTelemetry } from "@/lib/axiom/system-monitor";

// ── Inline telemetry renderer for the SYSTEM control centre. Reads the same
// live source as the floating SystemTelemetry widget, but laid out fluidly to
// fill the workstation rather than a fixed popover. —──────────────────────

function Gauge({ value, label, warnAt = 80, critAt = 95 }: { value: number; label: string; warnAt?: number; critAt?: number }) {
  const color =
    value >= critAt ? "var(--axiom-error)" : value >= warnAt ? "var(--axiom-warning)" : "var(--axiom-accent)";
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border px-3 py-4" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(13,16,20,0.4)" }}>
      <div className="relative w-16 h-16">
        <svg viewBox="0 0 64 64" className="w-16 h-16 -rotate-90">
          <circle cx="32" cy="32" r="26" fill="none" stroke="var(--axiom-bg-elevated)" strokeWidth="6" />
          <motion.circle
            cx="32" cy="32" r="26" fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
            initial={{ strokeDashoffset: 2 * Math.PI * 26 }}
            animate={{ strokeDashoffset: 2 * Math.PI * 26 * (1 - Math.min(value, 100) / 100) }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            strokeDasharray={2 * Math.PI * 26}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-[15px] font-semibold font-mono" style={{ color }}>{value.toFixed(0)}<span className="text-[9px]">%</span></span>
      </div>
      <span className="text-[9px] font-semibold uppercase tracking-[0.18em] text-[var(--axiom-text-tertiary)]">{label}</span>
    </div>
  );
}

function MetricBar({ value, label, detail, warnAt = 80, critAt = 95 }: { value: number; label: string; detail: string; warnAt?: number; critAt?: number }) {
  const color =
    value >= critAt ? "var(--axiom-error)" : value >= warnAt ? "var(--axiom-warning)" : "var(--axiom-accent)";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-[var(--axiom-text-secondary)]">{label}</span>
        <span className="font-mono text-[var(--axiom-text-primary)]">{detail}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--axiom-bg-elevated)] overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="h-full rounded-full"
          style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
        />
      </div>
    </div>
  );
}

export default function SystemTelemetryView() {
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = useCallback(async () => {
    try {
      const data = await getTelemetry();
      setSnapshot(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Offline");
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      await poll();
      if (mounted) intervalRef.current = setInterval(() => poll(), 5000);
    };
    load();
    return () => {
      mounted = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [poll]);

  return (
    <div className="min-h-full flex flex-col gap-4 min-w-0 mx-auto max-w-[1240px]">
      {/* Status strip */}
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Telemetry</h3>
        <div className="flex items-center gap-2 text-[10px]">
          {snapshot && (
            <span className="font-mono text-[var(--axiom-text-tertiary)]">{snapshot.hostname} · {new Date(snapshot.timestamp * 1000).toLocaleTimeString()}</span>
          )}
          <button
            onClick={poll}
            className="px-2.5 py-1 rounded-md border text-[10px] font-semibold text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-text-primary)] transition-colors"
            style={{ borderColor: "rgba(109,124,255,0.18)", background: "rgba(109,124,255,0.05)" }}
          >
            Refresh
          </button>
        </div>
      </div>

      {error && !snapshot && (
        <div className="rounded-xl border border-[rgba(255,77,106,0.15)] bg-[rgba(255,77,106,0.04)] px-4 py-6 flex flex-col items-center gap-2">
          <p className="text-[11px] text-[var(--axiom-error)]">{error}</p>
          <button onClick={poll} className="text-[10px] text-[var(--axiom-accent)] underline">Retry</button>
        </div>
      )}

      {!snapshot && !error && (
        <div className="flex items-center justify-center py-16 gap-1">
          {[0, 1, 2].map((i) => (
            <span key={i} className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-dot-pulse" style={{ animationDelay: `${i * 200}ms` }} />
          ))}
        </div>
      )}

      {snapshot && (
        <>
          {/* Gauges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Gauge value={snapshot.cpu.percent} label="CPU" warnAt={80} critAt={95} />
            <Gauge value={snapshot.memory.percent} label="RAM" warnAt={75} critAt={90} />
            <Gauge value={snapshot.disk.percent} label="Storage" warnAt={80} critAt={92} />
            {/* Temperature mapped onto 30–90°C window */}
            <Gauge
              value={snapshot.temperature.cpu_temp_c != null ? Math.min(100, Math.max(0, ((snapshot.temperature.cpu_temp_c - 30) / 60) * 100)) : 0}
              label="Temperature"
              warnAt={60}
              critAt={80}
            />
          </div>

          {/* Detailed bars */}
          <section className="rounded-xl border" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(13,16,20,0.4)" }}>
            <h4 className="px-4 pt-3 pb-1 text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)]">Resource usage</h4>
            <div className="px-4 py-3 space-y-3">
              <MetricBar value={snapshot.memory.percent} label="Memory" detail={`${snapshot.memory.used_gb.toFixed(1)} / ${snapshot.memory.total_gb.toFixed(1)} GB`} warnAt={75} critAt={90} />
              <MetricBar value={snapshot.disk.percent} label="Disk" detail={`${snapshot.disk.used_gb.toFixed(1)} / ${snapshot.disk.total_gb.toFixed(1)} GB`} warnAt={80} critAt={92} />
              <div className="grid grid-cols-2 gap-4 pt-1 text-[11px] font-mono text-[var(--axiom-text-secondary)]">
                <span>↧ {snapshot.network.bytes_recv_mb.toFixed(0)} MB recv</span>
                <span>↥ {snapshot.network.bytes_sent_mb.toFixed(0)} MB sent</span>
                <span>{snapshot.processes} processes</span>
                <span>{Math.floor(snapshot.uptime_seconds / 3600)}h {Math.floor((snapshot.uptime_seconds % 3600) / 60)}m uptime</span>
              </div>
            </div>
          </section>

          {/* Services */}
          <section className="rounded-xl border" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(13,16,20,0.4)" }}>
            <h4 className="px-4 pt-3 pb-1 text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)]">Services</h4>
            {snapshot.services.length ? (
              <div className="px-4 py-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
                {snapshot.services.map((s) => (
                  <div key={s.name} className="flex items-center justify-between gap-2 py-1">
                    <span className={`flex items-center gap-1.5 text-[11px] text-[var(--axiom-text-secondary)] truncate`}>
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.status === "running" ? "bg-green-400" : "bg-red-400"}`} />
                      <span className="truncate">{s.name.length > 22 ? s.name.slice(0, 22) + "…" : s.name}</span>
                    </span>
                    <span className="font-mono text-[9px] text-[var(--axiom-text-tertiary)]">{s.status !== "running" ? "down" : `${s.cpu_percent.toFixed(0)}% · ${s.memory_mb.toFixed(0)}MB`}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="px-4 py-3 text-[11px] text-[var(--axiom-text-tertiary)]">No service data</p>
            )}
          </section>
        </>
      )}
    </div>
  );
}