"use client";
import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system } from "../../../lib/api";
import type { RuntimeStatus, IntelligenceProvidersResponse } from "../../../lib/api-types";

type SectionId = "quick-stats" | "system-info" | "component-status" | "provider-status";

function ChevronDown({ open }: { open: boolean }) {
  const r = `rotate(${open ? 0 : -90}deg)`;
  return (<svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ transform: r, transition: "transform 0.2s var(--axiom-ease-smooth)" }}>
    <path d="M3.5 5.25L7 8.75l3.5-3.5" stroke="var(--axiom-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>);
}

function StatusDot({ active, small }: { active: boolean; small?: boolean }) {
  const s = small ? 6 : 8;
  return (<span style={{
    display: "inline-block", width: s, height: s, borderRadius: "50%", flexShrink: 0,
    backgroundColor: active ? "var(--axiom-success)" : "var(--axiom-error)",
    transition: "background-color 0.3s",
    boxShadow: active ? "0 0 6px var(--axiom-success)" : "none",
  }} />);
}

function Panel({ id, title, count, expanded, onToggle, children }: {
  id: SectionId; title: string; count?: number;
  expanded: boolean; onToggle: (id: SectionId) => void; children: React.ReactNode;
}) {
  const b = { borderBottom: "1px solid var(--axiom-border)" };
  const btn = {
    width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "14px 20px", background: "none", border: "none", color: "var(--axiom-text-primary)",
    cursor: "pointer", fontSize: 12, fontWeight: 600, letterSpacing: "0.04em",
    textTransform: "uppercase" as const, fontFamily: "var(--axiom-font-sans)",
  };
  return (<div style={b}>
    <button onClick={() => onToggle(id)} style={btn}>
      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {title}
        {count !== undefined && <span style={{
          fontSize: 10, padding: "1px 6px", borderRadius: "var(--axiom-radius-full)",
          background: "var(--axiom-accent-muted)", color: "var(--axiom-accent)",
        }}>{count}</span>}
      </span>
      <ChevronDown open={expanded} />
    </button>
    <AnimatePresence initial={false}>
      {expanded && <motion.div key={id}
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: "auto", opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.2, ease: "easeInOut" as const }}
        style={{ overflow: "hidden" }}>
        <div style={{ padding: "0 20px 16px" }}>{children}</div>
      </motion.div>}
    </AnimatePresence>
  </div>);
}

function Row({ label, value }: { label: string; value: string }) {
  return (<div style={{
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "8px 12px", borderRadius: "var(--axiom-radius-sm)",
    background: "var(--axiom-accent-subtle)", fontSize: 12,
  }}>
    <span style={{ color: "var(--axiom-text-secondary)" }}>{label}</span>
    <span style={{ color: "var(--axiom-text-primary)", fontWeight: 500, fontFamily: "var(--axiom-font-mono)" }}>{value}</span>
  </div>);
}

export default function FounderConsole() {
  const storeKey = "console";
  const workspaceState = useAxiomStore((s) => s.workspaceStates[storeKey]);
  const setWorkspaceState = useAxiomStore((s) => s.setWorkspaceState);
  const expandedSections = workspaceState?.expandedSections ?? {};

  const isExpanded = useCallback((id: SectionId) => expandedSections[id] !== false, [expandedSections]);
  const toggleSection = useCallback((id: SectionId) => {
    setWorkspaceState(storeKey, { expandedSections: { ...expandedSections, [id]: !isExpanded(id) } });
  }, [expandedSections, isExpanded, setWorkspaceState]);

  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [providerData, setProviderData] = useState<IntelligenceProvidersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bootTime] = useState(Date.now());
  const [uptime, setUptime] = useState("0m 0s");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [rt, prov] = await Promise.all([
        system.getRuntimeStatus(), system.getIntelligenceProviders(),
      ]);
      setRuntime(rt);
      setProviderData(prov);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load system data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    const interval = setInterval(() => {
      const el = Math.floor((Date.now() - bootTime) / 1000);
      setUptime(`${Math.floor(el / 60)}m ${el % 60}s`);
    }, 1000);
    return () => clearInterval(interval);
  }, [bootTime]);

  const g = { display: "flex", alignItems: "center", gap: 8 };
  const c = { fontSize: 12, fontWeight: 500 };

  return (
    <div className="glass-panel" style={{ margin: 16, overflow: "hidden" }}>
      {/* Header */}
      <div style={{
        padding: "18px 20px 14px", borderBottom: "1px solid var(--axiom-border)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="4" stroke="var(--axiom-accent)" strokeWidth="1.5" />
            <path d="M8 8h8M8 12h8M8 16h5" stroke="var(--axiom-accent)" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span style={{ fontSize: 14, fontWeight: 600 }}>Founder Console</span>
        </div>
        {runtime && <div style={g}>
          <StatusDot active={runtime.running} small />
          <span style={{ fontSize: 11, color: runtime.running ? "var(--axiom-success)" : "var(--axiom-error)" }}>
            {runtime.running ? "ONLINE" : "OFFLINE"}
          </span>
        </div>}
      </div>

      {/* Content */}
      {loading && <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
        {[1, 2, 3, 4].map((i) => <div key={i} style={{
          height: 36, borderRadius: "var(--axiom-radius-md)",
          background: "var(--axiom-bg-elevated)", opacity: 0.4,
          animation: "pulse-subtle 1.5s ease-in-out infinite",
        }} />)}
      </div>}

      {error && <div style={{ padding: 32, textAlign: "center" }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" style={{ marginBottom: 12, opacity: 0.5 }}>
          <circle cx="12" cy="12" r="10" stroke="var(--axiom-error)" strokeWidth="1.5" />
          <path d="M12 8v4M12 16h0" stroke="var(--axiom-error)" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <p style={{ margin: "0 0 12", fontSize: 13, color: "var(--axiom-text-secondary)" }}>{error}</p>
        <button onClick={fetchData} style={{
          padding: "8px 20px", fontSize: 12, fontWeight: 600, borderRadius: "var(--axiom-radius-md)",
          background: "var(--axiom-accent)", color: "#fff", border: "none", cursor: "pointer",
        }}>Retry</button>
      </div>}

      {!loading && !error && !runtime && (
        <div style={{ padding: 32, textAlign: "center" }}>
          <p style={{ color: "var(--axiom-text-secondary)", fontSize: 14 }}>No system data available.</p>
        </div>
      )}

      {!loading && !error && runtime && (<>
        {/* Quick Stats */}
        <Panel id="quick-stats" title="Quick Stats" expanded={isExpanded("quick-stats")} onToggle={toggleSection}>
          <div style={{ display: "flex", gap: 10 }}>
            {[{ l: "Workflows", v: runtime.workflows_defined }, { l: "Executives", v: runtime.executives }, { l: "Orgs", v: runtime.org_count }].map((s) => (
              <div key={s.l} style={{
                flex: 1, padding: "14px 16px", borderRadius: "var(--axiom-radius-md)",
                background: "var(--axiom-bg-surface)", border: "1px solid var(--axiom-border)", textAlign: "center",
              }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: "var(--axiom-accent)", marginBottom: 2 }}>{s.v}</div>
                <div style={{ fontSize: 11, color: "var(--axiom-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>{s.l}</div>
              </div>
            ))}
          </div>
        </Panel>

        {/* System Info */}
        <Panel id="system-info" title="System Info" expanded={isExpanded("system-info")} onToggle={toggleSection}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <Row label="Version" value={runtime.version} />
            <Row label="Status" value={runtime.initialised ? "Initialised" : "Initialising"} />
            <Row label="Running" value={runtime.running ? "Yes" : "No"} />
            <Row label="Uptime" value={uptime} />
          </div>
        </Panel>

        {/* Component Status */}
        <Panel id="component-status" title="Components"
          count={Object.keys(runtime.components ?? {}).length}
          expanded={isExpanded("component-status")} onToggle={toggleSection}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {Object.entries(runtime.components ?? {}).map(([name, active]) => (
              <div key={name} style={{
                ...g, ...c, padding: "10px 12px", borderRadius: "var(--axiom-radius-sm)",
                background: "var(--axiom-accent-subtle)",
              }}>
                <StatusDot active={active} small />
                <span style={{ color: "var(--axiom-text-primary)", textTransform: "capitalize" }}>{name.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
        </Panel>

        {/* Provider Status */}
        <Panel id="provider-status" title="Intelligence Providers"
          count={providerData?.total_providers}
          expanded={isExpanded("provider-status")} onToggle={toggleSection}>
          {(!providerData || providerData.providers.length === 0) ? (
            <p style={{ fontSize: 12, color: "var(--axiom-text-tertiary)", textAlign: "center", padding: 16 }}>
              No intelligence providers configured.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {providerData.providers.map((p) => (
                <div key={p.name} style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "10px 14px", borderRadius: "var(--axiom-radius-md)",
                  background: "var(--axiom-bg-surface)", border: "1px solid var(--axiom-border)",
                }}>
                  <StatusDot active={p.available} small />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--axiom-text-primary)" }}>{p.label || p.name}</div>
                    <div style={{ fontSize: 11, color: "var(--axiom-text-tertiary)", marginTop: 1 }}>{p.type} &middot; {p.model}</div>
                  </div>
                  <div style={{
                    fontSize: 10, padding: "2px 8px", borderRadius: "var(--axiom-radius-full)",
                    background: p.available ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                    color: p.available ? "var(--axiom-success)" : "var(--axiom-error)",
                    fontWeight: 600, whiteSpace: "nowrap",
                  }}>{p.role}</div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </>)}
    </div>
  );
}