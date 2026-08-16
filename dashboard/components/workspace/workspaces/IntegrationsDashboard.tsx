"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { IntegrationService, IntegrationServiceType, ConnectionStatus } from "../../../lib/phase8c-types";

/* ── Mock Data ────────────────────────────────────────────────────── */

const MOCK_SERVICES: IntegrationService[] = [
  {
    id: "github", name: "GitHub", type: "github", description: "Source control, issue tracking, and CI/CD", status: "connected",
    permissions: ["read_repos", "write_issues"], health: "healthy", last_connected: new Date(Date.now() - 7200000).toISOString(),
    activity_count: 15, icon: "github", configurable: true,
    recent_events: [
      { id: "e1", type: "push", description: "feat/lead-scoring: 3 commits pushed", timestamp: new Date(Date.now() - 300000).toISOString(), status: "success" },
      { id: "e2", type: "pr", description: "PR #42: Update sales strategy docs", timestamp: new Date(Date.now() - 1800000).toISOString(), status: "success" },
      { id: "e3", type: "issue", description: "Issue #128: Lead scoring model accuracy", timestamp: new Date(Date.now() - 3600000).toISOString(), status: "warning" },
    ],
    logs: ["[22:14] Connected to github.com/bleval-inc", "[20:30] Synced repository list (12 repos)", "[18:00] Token refreshed successfully"],
  },
  {
    id: "claude-code", name: "Claude Code", type: "claude_code", description: "AI-powered coding assistant", status: "connected",
    permissions: ["read_write"], health: "healthy", last_connected: new Date(Date.now() - 60000).toISOString(),
    activity_count: 128, icon: "terminal", configurable: true,
    recent_events: [
      { id: "e4", type: "session", description: "Active coding session: lead scoring model", timestamp: new Date(Date.now() - 120000).toISOString(), status: "success" },
      { id: "e5", type: "completion", description: "Generated 3 test files for API routes", timestamp: new Date(Date.now() - 600000).toISOString(), status: "success" },
    ],
    logs: ["[22:13] Session started: lead-scoring-feature", "[21:45] Generated implementation plan", "[21:30] Context loaded: 14 files"],
  },
  {
    id: "vscode", name: "VS Code", type: "vscode", description: "Primary development environment", status: "connected",
    permissions: ["editor_access"], health: "healthy", last_connected: new Date(Date.now() - 300000).toISOString(),
    activity_count: 42, icon: "code2", configurable: false,
    recent_events: [
      { id: "e6", type: "workspace", description: "Opened workspace: bleval-ai-os", timestamp: new Date(Date.now() - 600000).toISOString(), status: "success" },
      { id: "e7", type: "extension", description: "AXIOM extension active", timestamp: new Date(Date.now() - 3600000).toISOString(), status: "success" },
    ],
    logs: ["[21:55] Workspace opened", "[21:30] Extension: axiom-vscode v2.1.0 loaded"],
  },
  {
    id: "tradingview", name: "TradingView", type: "tradingview", description: "Market analysis and charting platform", status: "pending",
    permissions: ["read_only"], health: "healthy", last_connected: null,
    activity_count: 0, icon: "trending-up", configurable: true,
    recent_events: [], logs: ["[22:00] Awaiting authorization...", "[21:00] Connection request sent"],
  },
  {
    id: "mt5", name: "MetaTrader 5", type: "mt5", description: "Forex and CFD trading platform", status: "disconnected",
    permissions: ["trade_execution"], health: "unhealthy", last_connected: new Date(Date.now() - 86400000 * 3).toISOString(),
    activity_count: 0, icon: "bar-chart-3", configurable: true,
    recent_events: [{ id: "e8", type: "error", description: "Session expired. Reconnect required.", timestamp: new Date(Date.now() - 7200000).toISOString(), status: "error" }],
    logs: ["[3 days ago] Session disconnected", "[3 days ago] Error: Authentication timeout", "[3 days ago] Connected successfully"],
  },
  {
    id: "gmail", name: "Gmail", type: "gmail", description: "Email communication and threading", status: "connected",
    permissions: ["send_read"], health: "healthy", last_connected: new Date(Date.now() - 3600000).toISOString(),
    activity_count: 234, icon: "mail", configurable: true,
    recent_events: [
      { id: "e9", type: "email", description: "Processed 47 emails in last hour", timestamp: new Date(Date.now() - 600000).toISOString(), status: "success" },
      { id: "e10", type: "thread", description: "New thread: Q3 budget approval", timestamp: new Date(Date.now() - 3600000).toISOString(), status: "success" },
    ],
    logs: ["[21:00] Mail sync completed (47 messages)", "[20:00] Mail sync completed (32 messages)"],
  },
  {
    id: "calendar", name: "Calendar", type: "calendar", description: "Schedule and event management", status: "connected",
    permissions: ["read_write"], health: "healthy", last_connected: new Date(Date.now() - 3600000).toISOString(),
    activity_count: 89, icon: "calendar", configurable: true,
    recent_events: [
      { id: "e11", type: "event", description: "Synced 14 upcoming events", timestamp: new Date(Date.now() - 1800000).toISOString(), status: "success" },
      { id: "e12", type: "reminder", description: "Q3 planning meeting in 30 min", timestamp: new Date(Date.now() - 600000).toISOString(), status: "warning" },
    ],
    logs: ["[21:30] Calendar sync completed", "[20:30] Event created: Q3 Planning Review"],
  },
  {
    id: "crm", name: "CRM Platform", type: "crm", description: "Customer relationship management", status: "connected",
    permissions: ["read_write"], health: "healthy", last_connected: new Date(Date.now() - 10800000).toISOString(),
    activity_count: 67, icon: "users", configurable: true,
    recent_events: [
      { id: "e13", type: "lead", description: "3 new leads imported from outreach", timestamp: new Date(Date.now() - 1200000).toISOString(), status: "success" },
      { id: "e14", type: "deal", description: "Deal stage updated: Acme Corp → Negotiation", timestamp: new Date(Date.now() - 7200000).toISOString(), status: "success" },
    ],
    logs: ["[19:00] CRM sync completed", "[18:00] Deal updated: Acme Corp ($50K)"],
  },
  {
    id: "whatsapp", name: "WhatsApp", type: "whatsapp", description: "Business messaging and notifications", status: "error",
    permissions: ["send_messages"], health: "unhealthy", last_connected: new Date(Date.now() - 3600000).toISOString(),
    activity_count: 12, icon: "message-circle", configurable: true,
    recent_events: [{ id: "e15", type: "error", description: "API rate limit exceeded. Retrying in 60s.", timestamp: new Date(Date.now() - 600000).toISOString(), status: "error" }],
    logs: ["[21:30] Error: 429 Rate limit exceeded", "[21:29] Message sent successfully", "[21:00] Connected to WhatsApp Business API"],
  },
];

/* ── Config ───────────────────────────────────────────────────────── */

const SERVICE_ICONS: Record<string, string> = {
  github: "github", terminal: "claude", "code2": "vscode", "trending-up": "tv", "bar-chart-3": "mt5", mail: "gmail", calendar: "cal", users: "crm", "message-circle": "wa",
};

const STATUS_CONFIG: Record<ConnectionStatus, { label: string; color: string; bg: string }> = {
  connected: { label: "Connected", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  disconnected: { label: "Disconnected", color: "text-zinc-400", bg: "bg-zinc-500/10" },
  error: { label: "Error", color: "text-red-400", bg: "bg-red-500/10" },
  pending: { label: "Pending", color: "text-amber-400", bg: "bg-amber-500/10" },
};

/* ── Sub-Components ───────────────────────────────────────────────── */

function ServiceCard({ service, onClick }: { service: IntegrationService; onClick: () => void }) {
  const status = STATUS_CONFIG[service.status];
  return (
    <motion.button onClick={onClick} whileHover={{ y: -2 }} className="glass-card p-4 text-left group">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--axiom-bg-elevated)] flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-secondary)]">
              {service.type === "github" ? <><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></> :
              service.type === "gmail" ? <><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></> :
              service.type === "calendar" ? <><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></> :
              service.type === "crm" ? <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></> :
              service.type === "whatsapp" ? <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></> :
              service.type === "tradingview" ? <><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></> :
              service.type === "mt5" ? <><line x1="22" y1="12" x2="2" y2="12"/><polyline points="12 2 2 12 12 22"/></> :
              <><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></>}
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-medium text-[var(--axiom-text-primary)]">{service.name}</h3>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">{service.description}</p>
          </div>
        </div>
        <span className={`text-[9px] px-2 py-0.5 rounded-full ${status.bg} ${status.color} font-medium`}>{status.label}</span>
      </div>
      {/* Status row */}
      <div className="flex items-center gap-3 mt-3 pt-3 border-t border-[var(--axiom-border)]">
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${service.health === "healthy" ? "bg-emerald-400" : service.health === "degraded" ? "bg-amber-400" : "bg-red-400"}`} />
          <span className="text-[10px] text-[var(--axiom-text-tertiary)]">
            {service.health === "healthy" ? "Healthy" : service.health === "degraded" ? "Degraded" : "Unhealthy"}
          </span>
        </div>
        <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{service.activity_count} events today</span>
        {service.last_connected && (
          <span className="text-[9px] text-[var(--axiom-text-tertiary)] ml-auto">
            {Math.floor((Date.now() - new Date(service.last_connected).getTime()) / 3600000)}h ago
          </span>
        )}
      </div>
      {/* Permissions */}
      <div className="flex flex-wrap gap-1 mt-2">
        {service.permissions.map((p) => (
          <span key={p} className="text-[8px] px-1.5 py-0.5 rounded bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)] font-mono">{p}</span>
        ))}
      </div>
      {/* Action */}
      {service.status !== "connected" && (
        <button onClick={(e) => { e.stopPropagation(); }} className="mt-3 w-full py-1.5 text-[11px] font-medium rounded-lg bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors">
          {service.status === "error" ? "Reconnect" : service.status === "pending" ? "Authorize" : "Connect"}
        </button>
      )}
    </motion.button>
  );
}

function ServiceDetail({ service, onClose }: { service: IntegrationService; onClose: () => void }) {
  const status = STATUS_CONFIG[service.status];
  return (
    <motion.div initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }} className="w-[400px] flex-shrink-0 border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-y-auto">
      <div className="px-5 py-4 border-b border-[var(--axiom-border)] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)]">{service.name}</h3>
          <span className={`text-[9px] px-2 py-0.5 rounded-full ${status.bg} ${status.color}`}>{status.label}</span>
        </div>
        <button onClick={onClose} className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>
      <div className="p-5 space-y-5">
        <p className="text-xs text-[var(--axiom-text-secondary)]">{service.description}</p>
        <div className="grid grid-cols-2 gap-3">
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Status</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{status.label}</p></div>
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Health</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5 capitalize">{service.health}</p></div>
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Activity</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{service.activity_count} events today</p></div>
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Configurable</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{service.configurable ? "Yes" : "No"}</p></div>
        </div>
        <div>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase mb-1">Permissions</p>
          <div className="flex flex-wrap gap-1">
            {service.permissions.map((p) => <span key={p} className="text-[10px] px-2 py-1 rounded bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] font-mono">{p}</span>)}
          </div>
        </div>
        {/* Recent Events */}
        <div>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase mb-2">Recent Events</p>
          <div className="space-y-1.5">
            {service.recent_events.map((e) => (
              <div key={e.id} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)]">
                <span className={`w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0 ${e.status === "success" ? "bg-emerald-400" : e.status === "error" ? "bg-red-400" : "bg-amber-400"}`} />
                <div>
                  <p className="text-[11px] text-[var(--axiom-text-primary)]">{e.description}</p>
                  <p className="text-[9px] text-[var(--axiom-text-tertiary)]">{new Date(e.timestamp).toLocaleTimeString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* Logs */}
        <div>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase mb-2">Recent Logs</p>
          <div className="bg-[var(--axiom-bg-base)] rounded-lg p-3 space-y-1">
            {service.logs.map((log, i) => (
              <p key={i} className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono leading-relaxed">{log}</p>
            ))}
          </div>
        </div>
        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <button className="flex-1 px-4 py-2 text-xs font-medium rounded-lg bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors">Configure</button>
          {service.status === "connected" ? (
            <button className="px-4 py-2 text-xs font-medium rounded-lg border border-red-400/30 text-red-400 hover:bg-red-500/10 transition-colors">Disconnect</button>
          ) : (
            <button className="flex-1 px-4 py-2 text-xs font-medium rounded-lg border border-[var(--axiom-border)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors">Reconnect</button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

/* ── Main Component ───────────────────────────────────────────────── */

export default function IntegrationsDashboard() {
  const [services] = useState(MOCK_SERVICES);
  const [activeService, setActiveService] = useState<IntegrationService | null>(null);

  const connected = services.filter((s) => s.status === "connected").length;
  const disconnected = services.filter((s) => s.status === "disconnected" || s.status === "error").length;

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-[var(--axiom-bg-base)]">
      <div className="flex-1 overflow-y-auto">
        <div className="p-5 max-w-[1400px] mx-auto space-y-5">
          {/* Header */}
          <div>
            <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Integrations</h2>
            <p className="text-[11px] text-[var(--axiom-text-tertiary)]">Connected services and external tools</p>
          </div>
          {/* Status bar */}
          <div className="glass-card px-4 py-3 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs text-[var(--axiom-text-primary)]">{connected} connected</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-400" />
              <span className="text-xs text-[var(--axiom-text-primary)]">{disconnected} disconnected</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span className="text-xs text-[var(--axiom-text-primary)]">{services.filter((s) => s.status === "pending").length} pending</span>
            </div>
            <div className="ml-auto text-[10px] text-[var(--axiom-text-tertiary)]">{services.length} total services</div>
          </div>
          {/* Grid */}
          <div className="grid grid-cols-3 gap-3">
            {services.map((s) => <ServiceCard key={s.id} service={s} onClick={() => setActiveService(s)} />)}
          </div>
        </div>
      </div>
      {/* Detail */}
      <AnimatePresence>
        {activeService && <ServiceDetail service={activeService} onClose={() => setActiveService(null)} />}
      </AnimatePresence>
    </div>
  );
}