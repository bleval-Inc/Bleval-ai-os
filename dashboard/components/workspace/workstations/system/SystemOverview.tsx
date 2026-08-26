"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { TelemetrySnapshot } from "@/lib/axiom/telemetry-types";
import { getTelemetry } from "@/lib/axiom/system-monitor";
import { useAxiomStore } from "@/lib/store/axiom-store";

type VitalTone = "healthy" | "warning" | "danger";

// ── Small presentational helpers (shared languages: glass panels, hairline
// borders, restrained blue/violet illumination — consistent with the shell) ─

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border flex flex-col min-w-0 min-h-0" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(13,16,20,0.4)" }}>
      <h4 className="px-4 pt-3 pb-1 text-[10px] font-semibold tracking-[0.18em] text-[var(--axiom-text-tertiary)] flex-shrink-0">
        {title}
      </h4>
      <div className="px-4 pb-4 pt-1 min-h-0">{children}</div>
    </section>
  );
}

function VitalStat({ label, value, sub, tone }: { label: string; value: string; sub: string; tone: VitalTone }) {
  const color =
    tone === "healthy" ? "#22d377" : tone === "warning" ? "#ffb830" : "#ff4d6a";
  return (
    <div className="rounded-xl border px-4 py-3 flex items-center justify-between gap-3 min-w-0" style={{ borderColor: "rgba(240,241,243,0.06)", background: "rgba(13,16,20,0.4)" }}>
      <div className="min-w-0">
        <div className="text-[9px] font-semibold uppercase tracking-[0.16em] text-[var(--axiom-text-tertiary)]">{label}</div>
        <div className="text-[22px] leading-none font-semibold text-[var(--axiom-text-primary)] tabular-nums mt-1">{value}</div>
        <div className="text-[10px] text-[var(--axiom-text-secondary)] truncate mt-0.5">{sub}</div>
      </div>
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color, boxShadow: `0 0 8px ${color}` }} />
    </div>
  );
}

function StatusRow({ label, status }: { label: string; status: "online" | "offline" | "degraded" }) {
  const color = status === "online" ? "#22d377" : status === "degraded" ? "#ffb830" : "#ff4d6a";
  const text = status === "online" ? "Online" : status === "degraded" ? "Degraded" : "Offline";
  return (
    <div className="flex items-center justify-between gap-2 py-1.5 min-w-0">
      <div className="flex items-center gap-2 min-w-0">
        <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
        <span className="text-[12px] text-[var(--axiom-text-secondary)] truncate">{label}</span>
      </div>
      <span className="text-[10px] font-semibold uppercase tracking-wider flex-shrink-0" style={{ color }}>{text}</span>
    </div>
  );
}

function ServiceBadge({ name, status }: { name: string; status: string }) {
  const running = status === "running";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-medium border ${running ? "border-green-500/15 bg-green-500/5 text-green-300" : "border-red-500/15 bg-red-500/5 text-red-300"}`}>
      <span className={`w-1 h-1 rounded-full ${running ? "bg-green-400" : "bg-red-400"}`} />
      {name.length > 16 ? name.slice(0, 16) + "…" : name}
    </span>
  );
}

// ── System Overview ──────────────────────────────────────────────────────────

export default function SystemOverview() {
  const runtime = useAxiomStore((s) => s.runtime);
  const health = useAxiomStore((s) => s.health);
  const executiveBoard = useAxiomStore((s) => s.executiveBoard);
  const notifications = useAxiomStore((s) => s.notifications);

  const [telemetry, setTelemetry] = useState<TelemetrySnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = useCallback(async () => {
    try {
      const data = await getTelemetry();
      setTelemetry(data);
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

  // Overall operating state — telemetry takes priority, store health as backup.
  const label = telemetry?.health_label ?? (runtime?.running && health?.overall === "healthy" ? "healthy" : null);
  const tone: "operational" | "degraded" | "critical" =
    label === "healthy" ? "operational" : label === "degraded" ? "degraded" : "critical";
  const toneColor = tone === "operational" ? "#22d377" : tone === "degraded" ? "#ffb830" : "#ff4d6a";
  const statusText = tone === "operational" ? "ALL SYSTEMS OPERATIONAL" : tone === "degraded" ? "OPERATIONAL · DEGRADED" : "SYSTEM CRITICAL";

  const engines = runtime?.components ? Object.entries(runtime.components) : [];
  const executiveEntries = executiveBoard ? Object.entries(executiveBoard) : [];
  const recentEvents = notifications.slice(0, 6);

  const fmtUptime = (sec: number) => `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;

  return (
    <div className="min-h-full flex flex-col gap-4 min-w-0 mx-auto max-w-[1240px]">
      {/* Hero — the first thing the eye should answer: is AXIOM operating? */}
      <div className="rounded-2xl border overflow-hidden flex flex-col" style={{ borderColor: "rgba(240,241,243,0.06)", background: "radial-gradient(ellipse 60% 90% at 20% 0%, rgba(109,124,255,0.08), transparent 60%), radial-gradient(ellipse 50% 80% at 90% 100%, rgba(168,140,255,0.06), transparent 60%), rgba(13,16,20,0.5)" }}>
        <div className="flex items-center justify-between gap-4 px-6 py-5 border-b" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center text-white flex-shrink-0 relative overflow-hidden" style={{ background: "linear-gradient(135deg,#6d7cff,#a88cff)", boxShadow: "0 0 26px -4px rgba(109,124,255,0.55)" }}>
              <div className="absolute inset-0 bg-gradient-to-br from-white/25 to-transparent" />
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="relative">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
            </div>
            <div className="min-w-0">
              <h3 className="text-lg font-semibold tracking-tight text-[var(--axiom-text-primary)] truncate">AXIOM SYSTEM</h3>
              <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--axiom-text-tertiary)]">Command &amp; configuration centre</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="relative flex w-2 h-2 flex-shrink-0">
              <span className="absolute inline-flex h-full w-full rounded-full opacity-40 animate-ping" style={{ background: toneColor, animationDuration: "2.4s" }} />
              <span className="relative inline-flex rounded-full w-2 h-2" style={{ background: toneColor, boxShadow: `0 0 8px ${toneColor}` }} />
            </span>
            <span className="text-[11px] font-semibold tracking-wider text-[var(--axiom-text-primary)]">{statusText}</span>
          </div>
        </div>

        <div className="px-6 py-4 flex flex-wrap items-center gap-x-6 gap-y-1 text-[11px]">
          <span><span className="text-[var(--axiom-text-tertiary)]">Node</span> <span className="font-mono text-[var(--axiom-text-secondary)]">{telemetry?.hostname ?? "—"}</span></span>
          <span><span className="text-[var(--axiom-text-tertiary)]">Uptime</span> <span className="font-mono text-[var(--axiom-text-secondary)]">{telemetry ? fmtUptime(telemetry.uptime_seconds) : "—"}</span></span>
          <span><span className="text-[var(--axiom-text-tertiary)]">Core</span> <span className="font-mono text-[var(--axiom-text-secondary)]">{telemetry?.cpu.count_logical ?? "—"} logical</span></span>
          {error && <span className="text-[var(--axiom-error)] ml-auto">Telemetry offline</span>}
        </div>
      </div>

      {/* Vital telemetry tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <VitalStat label="CPU" value={telemetry ? `${telemetry.cpu.percent.toFixed(0)}%` : "—"} sub={telemetry ? `${telemetry.cpu.load_avg[0].toFixed(2)} load` : "N/A"} tone={telemetry && telemetry.cpu.percent >= 95 ? "danger" : telemetry && telemetry.cpu.percent >= 80 ? "warning" : "healthy"} />
        <VitalStat label="Memory" value={telemetry ? `${telemetry.memory.percent.toFixed(0)}%` : "—"} sub={telemetry ? `${telemetry.memory.used_gb.toFixed(1)} / ${telemetry.memory.total_gb.toFixed(1)} GB` : "N/A"} tone={telemetry && telemetry.memory.percent >= 90 ? "danger" : telemetry && telemetry.memory.percent >= 75 ? "warning" : "healthy"} />
        <VitalStat label="Storage" value={telemetry ? `${telemetry.disk.percent.toFixed(0)}%` : "—"} sub={telemetry ? `${telemetry.disk.used_gb.toFixed(0)} / ${telemetry.disk.total_gb.toFixed(0)} GB` : "N/A"} tone={telemetry && telemetry.disk.percent >= 92 ? "danger" : telemetry && telemetry.disk.percent >= 80 ? "warning" : "healthy"} />
        <VitalStat label="Health" value={telemetry ? `${telemetry.health_score.toFixed(0)}` : health ? `${health.healthy}/${health.total}` : "—"} sub={telemetry ? "score" : "healthy / total"} tone={toneVa(telemetry?.health_score, tone)} />
      </div>

      {/* Status rails */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        <div className="flex flex-col gap-4 min-w-0">
          <Panel title="Runtime">
            {runtime ? (
              <div className="divide-y divide-[rgba(240,241,243,0.04)]">
                <StatusLine label="Version" value={`v${runtime.version}`} />
                <StatusLine label="State" value={runtime.running ? "Running" : "Stopped"} />
                <StatusLine label="Workflows defined" value={`${runtime.workflows_defined}`} />
                <StatusLine label="Executives" value={`${runtime.executives}`} />
                <StatusLine label="Organisations" value={`${runtime.org_count}`} />
              </div>
            ) : (
              <div className="flex items-center gap-2 py-2 text-[11px] text-[var(--axiom-text-tertiary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-pulse" /> Awaiting runtime data
              </div>
            )}
          </Panel>

          <Panel title="Engines">
            {engines.length ? (
              <div className="grid grid-cols-1 gap-1">
                {engines.map(([name, on]) => (
                  <StatusRow key={name} label={name} status={on ? "online" : "offline"} />
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-[var(--axiom-text-tertiary)] py-1">No engine data yet</p>
            )}
          </Panel>
        </div>

        <div className="flex flex-col gap-4 min-w-0">
          <Panel title="Executive board">
            {executiveEntries.length ? (
              <div className="grid grid-cols-1 gap-1">
                {executiveEntries.map(([id, e]) => (
                  <StatusRow key={id} label={id} status={e.status === "running" ? "online" : e.status === "error" ? "degraded" : "offline"} />
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-[var(--axiom-text-tertiary)] py-1">No executive data yet</p>
            )}
          </Panel>

          <Panel title="Services">
            {telemetry?.services.length ? (
              <div className="flex flex-wrap gap-2">
                {telemetry.services.slice(0, 12).map((s) => (
                  <ServiceBadge key={s.name} name={s.name} status={s.status} />
                ))}
                {telemetry.services.length > 12 && (
                  <span className="text-[9px] text-[var(--axiom-text-tertiary)] self-center">+{telemetry.services.length - 12}</span>
                )}
              </div>
            ) : (
              <p className="text-[11px] text-[var(--axiom-text-tertiary)] py-1">No service data yet</p>
            )}
          </Panel>
        </div>
      </div>

      <Panel title="Recent system events">
        {recentEvents.length ? (
          <div className="divide-y divide-[rgba(240,241,243,0.04)]">
            {recentEvents.map((n) => (
              <div key={n.id} className="flex items-start gap-3 py-2 min-w-0">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${n.type === "error" ? "bg-[var(--axiom-error)]" : n.type === "warning" ? "bg-[var(--axiom-warning)]" : "bg-[var(--axiom-accent)]"}`} />
                <div className="min-w-0 flex-1">
                  <div className="text-[12px] text-[var(--axiom-text-secondary)] truncate">{n.title}</div>
                  {n.message && <div className="text-[10px] text-[var(--axiom-text-tertiary)] line-clamp-1">{n.message}</div>}
                </div>
                <span className="text-[9px] font-mono text-[var(--axiom-text-tertiary)] flex-shrink-0">{new Date(n.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-[var(--axiom-text-tertiary)] py-1">No recent events</p>
        )}
      </Panel>
    </div>
  );
}

function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2 py-1.5">
      <span className="text-[12px] text-[var(--axiom-text-secondary)]">{label}</span>
      <span className="text-[12px] font-mono text-[var(--axiom-text-primary)]">{value}</span>
    </div>
  );
}

function toneVa(score?: number, fallback?: "operational" | "degraded" | "critical"): VitalTone {
  if (score == null) return fallback === "critical" ? "danger" : fallback === "degraded" ? "warning" : "healthy";
  return score >= 90 ? "danger" : score >= 75 ? "warning" : "healthy";
}