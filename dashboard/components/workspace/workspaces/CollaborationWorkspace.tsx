"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
/* ── Types ────────────────────────────────────────────────────────── */

type SessionStatus = "active" | "scheduled" | "completed";
type ParticipantRole = "owner" | "editor" | "viewer";
type SessionType = "code" | "brainstorm" | "review" | "design";

interface TeamMember {
  id: string;
  name: string;
  role: ParticipantRole;
  avatar: string;
  status: "online" | "idle" | "offline";
  email: string;
}

interface CollaborationSession {
  id: string;
  title: string;
  type: SessionType;
  status: SessionStatus;
  participants: TeamMember[];
  messages: number;
  lastActivity: string;
  startedAt: string;
  branch?: string;
}

/* ── Mock Data ────────────────────────────────────────────────────── */

const AVATARS = [
  "https://api.dicebear.com/7.x/avataaars/svg?seed",
  "https://api.dicebear.com/7.x/avataaars/svg?seed",
  "https://api.dicebear.com/7.x/avataaars/svg?seed",
];

const MOCK_MEMBERS: TeamMember[] = [
  { id: "u1", name: "Alex Chen", role: "owner", avatar: `${AVATARS[0]}=Alex`, status: "online", email: "alex@bleval.io" },
  { id: "u2", name: "Sarah Park", role: "editor", avatar: `${AVATARS[1]}=Sarah`, status: "online", email: "sarah@bleval.io" },
  { id: "u3", name: "Marcus Webb", role: "editor", avatar: `${AVATARS[2]}=Marcus`, status: "idle", email: "marcus@bleval.io" },
  { id: "u4", name: "Priya Sharma", role: "viewer", avatar: `${AVATARS[1]}=Priya`, status: "offline", email: "priya@bleval.io" },
  { id: "u5", name: "Dan Wilson", role: "editor", avatar: `${AVATARS[2]}=Dan`, status: "online", email: "dan@bleval.io" },
  { id: "u6", name: "Emily Torres", role: "viewer", avatar: `${AVATARS[0]}=Emily`, status: "idle", email: "emily@bleval.io" },
];

const MOCK_SESSIONS: CollaborationSession[] = [
  {
    id: "s1", title: "Lead Scoring Model Architecture", type: "code", status: "active",
    participants: [MOCK_MEMBERS[0], MOCK_MEMBERS[1], MOCK_MEMBERS[2]],
    lastActivity: new Date(Date.now() - 60000).toISOString(),
    messages: 87, branch: "feat/lead-scoring", startedAt: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: "s2", title: "Q3 Strategy Brainstorm", type: "brainstorm", status: "active",
    participants: [MOCK_MEMBERS[0], MOCK_MEMBERS[1], MOCK_MEMBERS[3], MOCK_MEMBERS[5]],
    lastActivity: new Date(Date.now() - 300000).toISOString(),
    messages: 42, startedAt: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "s3", title: "API Route Design Review", type: "review", status: "scheduled",
    participants: [MOCK_MEMBERS[0], MOCK_MEMBERS[2], MOCK_MEMBERS[4]],
    lastActivity: new Date(Date.now() - 3600000).toISOString(),
    messages: 0, branch: "review/api-routes", startedAt: new Date(Date.now() + 3600000).toISOString(),
  },
  {
    id: "s4", title: "Performance Optimization Sprint", type: "code", status: "completed",
    participants: [MOCK_MEMBERS[0], MOCK_MEMBERS[1], MOCK_MEMBERS[4]],
    lastActivity: new Date(Date.now() - 86400000).toISOString(),
    messages: 134, branch: "sprint/perf-opt", startedAt: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: "s5", title: "UX Audit — Dashboard Redesign", type: "design", status: "active",
    participants: [MOCK_MEMBERS[1], MOCK_MEMBERS[2], MOCK_MEMBERS[3]],
    lastActivity: new Date(Date.now() - 120000).toISOString(),
    messages: 23, startedAt: new Date(Date.now() - 3600000).toISOString(),
  },
];

const SESSION_ICONS: Record<string, string> = {
  code: "code2", brainstorm: "lightbulb", review: "search", design: "palette",
};

/* ── Sub-Components ───────────────────────────────────────────────── */

function OnlineDot({ status }: { status: string }) {
  const colors: Record<string, string> = { online: "bg-emerald-400", idle: "bg-amber-400", offline: "bg-zinc-500" };
  return <span className={`w-2 h-2 rounded-full ${colors[status] || colors.offline}`} />;
}

function SessionIcon({ type }: { type: string }) {
  if (type === "code") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-secondary)]">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    );
  }
  if (type === "brainstorm") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-secondary)]">
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <path d="M12 17h0" />
      </svg>
    );
  }
  if (type === "review") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-secondary)]">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    );
  }
  if (type === "design") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-secondary)]">
        <path d="M4 6h16" />
        <path d="M6 12h12" />
        <path d="M8 18h8" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-secondary)]">
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );
}

function ParticipantAvatar({ member, size = "sm" }: { member: TeamMember; size?: "sm" | "md" }) {
  const dim = size === "md" ? 40 : 28;
  return (
    <div className="relative group cursor-pointer" title={`${member.name} (${member.role})`}>
      <img src={member.avatar} alt={member.name} width={dim} height={dim} className="rounded-full border-2 border-[var(--axiom-bg-surface)]" />
      <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[var(--axiom-bg-surface)]
        ${member.status === "online" ? "bg-emerald-400" : member.status === "idle" ? "bg-amber-400" : "bg-zinc-500"}`} />
    </div>
  );
}

function SessionCard({ session, onClick }: { session: CollaborationSession; onClick: () => void }) {
  const active = session.status === "active";
  const minutesAgo = Math.floor((Date.now() - new Date(session.lastActivity).getTime()) / 60000);
  return (
    <motion.button onClick={onClick} whileHover={{ y: -1 }} className={`glass-card p-4 text-left group ${!active && session.status !== "scheduled" ? "opacity-60" : ""}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <SessionIcon type={session.type} />
          <span className="text-xs font-medium text-[var(--axiom-text-primary)]">{session.title}</span>
        </div>
        {active && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />}
      </div>
      <div className="flex items-center gap-1.5 mb-2">
        {session.type === "code" && session.branch && (
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)] font-mono">{session.branch}</span>
        )}
        <span className="text-[9px] text-[var(--axiom-text-tertiary)] capitalize">{session.type}</span>
        {session.status === "scheduled" && <span className="text-[9px] text-amber-400">Upcoming</span>}
        {session.status === "completed" && <span className="text-[9px] text-zinc-500">Concluded</span>}
      </div>
      <div className="flex items-center gap-2">
        <div className="flex -space-x-1.5">
          {session.participants.slice(0, 4).map((p) => (
            <img key={p.id} src={p.avatar} alt={p.name} title={p.name} width={22} height={22} className="rounded-full border-2 border-[var(--axiom-bg-surface)]" />
          ))}
          {session.participants.length > 4 && (
            <span className="w-[22px] h-[22px] rounded-full bg-[var(--axiom-bg-elevated)] text-[9px] text-[var(--axiom-text-tertiary)] flex items-center justify-center border-2 border-[var(--axiom-bg-surface)]">
              +{session.participants.length - 4}
            </span>
          )}
        </div>
        <span className="text-[10px] text-[var(--axiom-text-tertiary)] ml-auto">{minutesAgo < 1 ? "Just now" : `${minutesAgo}m ago`}</span>
        <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{session.messages} msgs</span>
      </div>
    </motion.button>
  );
}

function ActivityFeed({ sessions }: { sessions: CollaborationSession[] }) {
  const active = sessions.filter((s) => s.status === "active").slice(0, 3);
  return (
    <div className="glass-card p-4">
      <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-3">Recent Activity</h3>
      <div className="space-y-2">
        {active.map((s) => (
          <div key={s.id} className="flex items-start gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 mt-1 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] text-[var(--axiom-text-primary)] truncate">{s.title}</p>
              <p className="text-[9px] text-[var(--axiom-text-tertiary)]">{s.participants.map((p) => p.name).join(", ")}</p>
            </div>
          </div>
        ))}
        {active.length === 0 && <p className="text-[11px] text-[var(--axiom-text-tertiary)]">No recent activity</p>}
      </div>
    </div>
  );
}

function TeamRoster() {
  const [filter, setFilter] = useState<string>("all");
  const online = MOCK_MEMBERS.filter((m) => m.status === "online").length;
  const filtered = filter === "all" ? MOCK_MEMBERS : MOCK_MEMBERS.filter((m) => m.status === filter);
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Team</h3>
        <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{online} online</span>
      </div>
      <div className="flex gap-1 mb-3">
        {["all", "online", "idle", "offline"].map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-2 py-1 text-[9px] rounded-md capitalize transition-colors ${filter === f ? "bg-[var(--axiom-accent)] text-white" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"}`}
          >{f}</button>
        ))}
      </div>
      <div className="space-y-2">
        {filtered.map((m) => (
          <div key={m.id} className="flex items-center gap-2">
            <OnlineDot status={m.status} />
            <img src={m.avatar} alt={m.name} width={24} height={24} className="rounded-full" />
            <span className="text-[11px] text-[var(--axiom-text-primary)]">{m.name}</span>
            <span className="text-[9px] text-[var(--axiom-text-tertiary)] ml-auto capitalize">{m.role}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuickActions() {
  return (
    <div className="glass-card p-4">
      <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-3">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-2">
        <button className="flex items-center gap-2 px-3 py-2 text-[11px] rounded-lg bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-accent)] hover:text-white transition-all">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
          New Session
        </button>
        <button className="flex items-center gap-2 px-3 py-2 text-[11px] rounded-lg bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-accent)] hover:text-white transition-all">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m22 2-7 20-4-9-9-4Z"/></svg>
          Start Huddle
        </button>
        <button className="flex items-center gap-2 px-3 py-2 text-[11px] rounded-lg bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-accent)] hover:text-white transition-all">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Schedule
        </button>
        <button className="flex items-center gap-2 px-3 py-2 text-[11px] rounded-lg bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-accent)] hover:text-white transition-all">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Share
        </button>
      </div>
    </div>
  );
}

function SessionDetail({ session, onClose }: { session: CollaborationSession; onClose: () => void }) {
  return (
    <motion.div initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }} className="w-[400px] flex-shrink-0 border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-y-auto">
      <div className="px-5 py-4 border-b border-[var(--axiom-border)] flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)]">{session.title}</h3>
        <button onClick={onClose} className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>
      <div className="p-5 space-y-5">
        <div className="grid grid-cols-2 gap-3">
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Type</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5 capitalize">{session.type}</p></div>
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Status</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5 capitalize">{session.status}</p></div>
          <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Messages</p><p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{session.messages}</p></div>
          {session.branch && <div><p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Branch</p><p className="text-xs font-mono text-[var(--axiom-accent)] mt-0.5">{session.branch}</p></div>}
        </div>
        <div>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase mb-2">Participants ({session.participants.length})</p>
          <div className="space-y-2">
            {session.participants.map((p) => (
              <div key={p.id} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)]">
                <img src={p.avatar} alt={p.name} width={28} height={28} className="rounded-full" />
                <div>
                  <p className="text-[11px] text-[var(--axiom-text-primary)]">{p.name}</p>
                  <p className="text-[9px] text-[var(--axiom-text-tertiary)] capitalize">{p.role}</p>
                </div>
                <OnlineDot status={p.status} />
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-2 pt-2">
          {session.status === "active" && <button className="flex-1 px-4 py-2 text-xs font-medium rounded-lg bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors">Join Session</button>}
          {session.status === "scheduled" && <button className="flex-1 px-4 py-2 text-xs font-medium rounded-lg bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 transition-colors">Start Early</button>}
          <button className="px-4 py-2 text-xs font-medium rounded-lg border border-[var(--axiom-border)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors">Details</button>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Main Component ───────────────────────────────────────────────── */

export default function CollaborationWorkspace() {
  const [sessions] = useState(MOCK_SESSIONS);
  const [activeSession, setActiveSession] = useState<CollaborationSession | null>(null);

  const activeSessions = sessions.filter((s) => s.status === "active");
  const pastSessions = sessions.filter((s) => s.status !== "active");

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-[var(--axiom-bg-base)]">
      <div className="flex-1 overflow-y-auto">
        <div className="p-5 max-w-[1400px] mx-auto space-y-5">
          {/* Header */}
          <div>
            <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Collaboration</h2>
            <p className="text-[11px] text-[var(--axiom-text-tertiary)]">Real-time team sessions and shared workspaces</p>
          </div>
          <div className="flex gap-3">
            {/* Main content */}
            <div className="flex-1 space-y-4">
              {/* Active Sessions */}
              <div>
                <h3 className="text-xs font-medium text-[var(--axiom-text-primary)] mb-2">Active Sessions ({activeSessions.length})</h3>
                <div className="grid grid-cols-2 gap-3">
                  {activeSessions.map((s) => <SessionCard key={s.id} session={s} onClick={() => setActiveSession(s)} />)}
                </div>
              </div>
              {/* Past Sessions */}
              <div>
                <h3 className="text-xs font-medium text-[var(--axiom-text-primary)] mb-2">Past Sessions ({pastSessions.length})</h3>
                <div className="grid grid-cols-2 gap-3">
                  {pastSessions.map((s) => <SessionCard key={s.id} session={s} onClick={() => setActiveSession(s)} />)}
                </div>
              </div>
            </div>
            {/* Sidebar */}
            <div className="w-64 flex-shrink-0 space-y-3">
              <QuickActions />
              <TeamRoster />
              <ActivityFeed sessions={sessions} />
            </div>
          </div>
        </div>
      </div>
      {/* Detail */}
      <AnimatePresence>
        {activeSession && <SessionDetail session={activeSession} onClose={() => setActiveSession(null)} />}
      </AnimatePresence>
    </div>
  );
}