"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type {
  Conversation,
  ConversationSource,
  Message,
  Participant,
  Attachment,
} from "../../../lib/phase8c-types";

/* ── Source Config ────────────────────────────────────────────────── */

const SOURCE_COLORS: Record<ConversationSource, string> = {
  founder: "bg-indigo-500",
  axiom: "bg-emerald-500",
  executive: "bg-amber-500",
  agent: "bg-blue-500",
  slack: "bg-purple-500",
  whatsapp: "bg-green-500",
  email: "bg-rose-500",
  voice: "bg-cyan-500",
  notification: "bg-orange-500",
};

const SOURCE_LABELS: Record<ConversationSource, string> = {
  founder: "Founder",
  axiom: "AXIOM",
  executive: "Executive",
  agent: "Agent",
  slack: "Slack",
  whatsapp: "WhatsApp",
  email: "Email",
  voice: "Voice",
  notification: "Notification",
};

const SOURCE_FILTERS: { key: ConversationSource | "all"; label: string }[] = [
  { key: "all", label: "All" },
  { key: "founder", label: "Founder" },
  { key: "axiom", label: "AXIOM" },
  { key: "executive", label: "Exec" },
  { key: "agent", label: "Agent" },
  { key: "slack", label: "Slack" },
  { key: "whatsapp", label: "WhatsApp" },
  { key: "email", label: "Email" },
  { key: "notification", label: "Notifications" },
];

/* ── Mock Data ────────────────────────────────────────────────────── */

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: "conv-1", title: "Q3 Strategy Alignment", source: "founder",
    participants: [{ id: "founder", name: "Tounga", role: "Founder", source: "founder" }],
    last_message: null, unread_count: 2, pinned: true, labels: ["urgent", "strategic"],
    timestamp: new Date().toISOString(), snippet: "We need to align on Q3 resource allocation and department priorities.",
    project_id: "q3-planning",
  },
  {
    id: "conv-2", title: "Morning Briefing", source: "axiom",
    participants: [{ id: "axiom", name: "AXIOM", role: "System", source: "axiom" }],
    last_message: null, unread_count: 0, pinned: false, labels: ["daily"],
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    snippet: "Good morning. All systems nominal. 3 workflows completed overnight. 2 approvals pending.",
    executive_id: "jenson",
  },
  {
    id: "conv-3", title: "Brand Identity Refresh", source: "executive",
    participants: [
      { id: "valta", name: "Valta Prime", role: "CEO - HOV", source: "executive" },
      { id: "jenson", name: "Jenson", role: "CEO - Bleval", source: "executive" },
    ],
    last_message: null, unread_count: 1, pinned: false, labels: ["brand", "creative"],
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    snippet: "The visual direction proposal is ready for review. Key changes to color palette and typography.",
  },
  {
    id: "conv-4", title: "Lead Discovery — Acme Corp", source: "agent",
    participants: [{ id: "atlas", name: "Atlas", role: "Lead Research", source: "agent" }],
    last_message: null, unread_count: 3, pinned: false, labels: ["lead", "high-value"],
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    snippet: "High-value lead identified. Company: Acme Corp. Estimated deal size: $50K+. Ready for qualification.",
  },
  {
    id: "conv-5", title: "#general", source: "slack",
    participants: [
      { id: "nova", name: "Nova", role: "Market Intel", source: "agent" },
      { id: "creator", name: "Creator", role: "Content", source: "agent" },
    ],
    last_message: null, unread_count: 5, pinned: false, labels: ["team"],
    timestamp: new Date(Date.now() - 600000).toISOString(),
    snippet: "New market report published. Key competitor launched similar product. Analysis pending.",
  },
  {
    id: "conv-6", title: "Urgent: Client Issue", source: "whatsapp",
    participants: [{ id: "client", name: "Sarah Chen", role: "Client", source: "whatsapp" }],
    last_message: null, unread_count: 1, pinned: true, labels: ["urgent", "client"],
    timestamp: new Date(Date.now() - 300000).toISOString(),
    snippet: "Need assistance with the deployment. System showing errors after update.",
  },
  {
    id: "conv-7", title: "Weekly Progress Report", source: "email",
    participants: [{ id: "board", name: "Board Members", role: "Stakeholders", source: "email" }],
    last_message: null, unread_count: 0, pinned: false, labels: ["report", "weekly"],
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    snippet: "Weekly progress report for July 24-31. Revenue pipeline: $2.1M. 3 new leads. 2 deals closed.",
  },
  {
    id: "conv-8", title: "System Alert: High CPU", source: "notification",
    participants: [{ id: "monitor", name: "System Monitor", role: "Monitoring", source: "notification" }],
    last_message: null, unread_count: 1, pinned: false, labels: ["alert", "system"],
    timestamp: new Date(Date.now() - 120000).toISOString(),
    snippet: "CPU usage at 94% on production instance. Auto-scaling triggered.",
  },
  {
    id: "conv-9", title: "Research Summary: AI Market", source: "axiom",
    participants: [{ id: "axiom", name: "AXIOM", role: "System", source: "axiom" }],
    last_message: null, unread_count: 0, pinned: false, labels: ["research"],
    timestamp: new Date(Date.now() - 14400000).toISOString(),
    snippet: "Market research complete. Key trends: Agentic AI adoption up 240%. New competitors entering space.",
  },
];

const MOCK_MESSAGES: Record<string, Message[]> = {
  "conv-1": [
    {
      id: "m1", conversation_id: "conv-1",
      sender: { id: "founder", name: "Tounga", role: "Founder", source: "founder" },
      content: "We need to align on Q3 strategy. Can you prepare a resource allocation plan?",
      timestamp: new Date(Date.now() - 7200000).toISOString(), source: "founder", read: true,
      attachments: [],
    },
    {
      id: "m2", conversation_id: "conv-1",
      sender: { id: "jenson", name: "Jenson", role: "CEO", source: "executive" },
      content: "Absolutely. I've drafted a preliminary plan. Key changes: increase sales headcount by 20%, shift marketing budget to content, defer non-critical dev projects.",
      timestamp: new Date(Date.now() - 5400000).toISOString(), source: "executive", read: true,
      attachments: [{ id: "a1", type: "document", name: "Q3_Allocation_Plan.pdf" }],
    },
    {
      id: "m3", conversation_id: "conv-1",
      sender: { id: "founder", name: "Tounga", role: "Founder", source: "founder" },
      content: "Good start. I want to see the revenue projections for each department before finalizing. Can you update by EOD?",
      timestamp: new Date(Date.now() - 1800000).toISOString(), source: "founder", read: false,
      attachments: [],
    },
    {
      id: "m4", conversation_id: "conv-1",
      sender: { id: "yamako", name: "Yamako", role: "Chief of Staff", source: "executive" },
      content: "I'll coordinate with department leads to gather the data. Expect the updated projections by 4pm.",
      timestamp: new Date(Date.now() - 600000).toISOString(), source: "executive", read: false,
      attachments: [],
    },
  ],
};

/* ── Helpers ──────────────────────────────────────────────────────── */

function formatTime(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60000) return "just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/* ── Sub-Components ───────────────────────────────────────────────── */

function AvatarCircle({ name, source, size = "md" }: { name: string; source: ConversationSource; size?: "sm" | "md" | "lg" }) {
  const sizeClass = size === "sm" ? "w-6 h-6 text-[9px]" : size === "lg" ? "w-10 h-10 text-sm" : "w-8 h-8 text-xs";
  return (
    <div className={`${sizeClass} rounded-full ${SOURCE_COLORS[source]} flex items-center justify-center text-white font-semibold flex-shrink-0`}>
      {name.charAt(0).toUpperCase()}
    </div>
  );
}

function SourceBadge({ source }: { source: ConversationSource }) {
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${SOURCE_COLORS[source].replace("bg-", "bg-").replace("500", "500/15")} ${SOURCE_COLORS[source].replace("bg-", "text-").replace("500", "400")}`}>
      {SOURCE_LABELS[source]}
    </span>
  );
}

function ConversationItem({ conv, isActive, onClick }: { conv: Conversation; isActive: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${isActive ? "bg-[var(--axiom-accent-subtle)]" : "hover:bg-[var(--axiom-bg-elevated)]"}`}>
      <div className="flex items-start gap-2.5">
        <AvatarCircle name={conv.title} source={conv.source} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-medium text-[var(--axiom-text-primary)] truncate flex items-center gap-1">
              {conv.pinned && <span className="text-[10px]">📌</span>}
              {conv.title}
            </span>
            <span className="text-[10px] text-[var(--axiom-text-tertiary)] whitespace-nowrap">{formatTime(conv.timestamp)}</span>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <SourceBadge source={conv.source} />
            {conv.unread_count > 0 && (
              <span className="text-[10px] font-bold text-white bg-[var(--axiom-accent)] px-1.5 rounded-full leading-4">{conv.unread_count}</span>
            )}
          </div>
          <p className="text-[12px] text-[var(--axiom-text-tertiary)] mt-1 line-clamp-1">{conv.snippet}</p>
        </div>
      </div>
    </button>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const isAxiom = msg.source === "axiom";
  return (
    <div className={`flex gap-2.5 ${isAxiom ? "" : "flex-row-reverse"}`}>
      <AvatarCircle name={msg.sender.name} source={msg.source} size="sm" />
      <div className={`max-w-[75%] ${isAxiom ? "" : "items-end"} flex flex-col`}>
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[11px] font-medium text-[var(--axiom-text-secondary)]">{msg.sender.name}</span>
          <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{formatTime(msg.timestamp)}</span>
          <SourceBadge source={msg.source} />
        </div>
        <div className={`rounded-2xl px-3.5 py-2.5 ${isAxiom ? "glass-panel" : "bg-[var(--axiom-accent-subtle)]"}`}>
          <p className="text-sm text-[var(--axiom-text-primary)] leading-relaxed">{msg.content}</p>
          {msg.attachments.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {msg.attachments.map((a) => (
                <div key={a.id} className="flex items-center gap-1 px-2 py-1 rounded-md bg-[var(--axiom-bg-elevated)] text-[11px] text-[var(--axiom-text-secondary)]">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  {a.name}
                </div>
              ))}
            </div>
          )}
        </div>
        {!msg.read && <span className="text-[9px] text-[var(--axiom-accent)] mt-0.5 ml-1">● Unread</span>}
      </div>
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────────────── */

export default function CommunicationsHub() {
  const [conversations] = useState(MOCK_CONVERSATIONS);
  const [activeConvId, setActiveConvId] = useState<string | null>("conv-1");
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState<ConversationSource | "all">("all");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [showContext, setShowContext] = useState(false);

  const filtered = useMemo(() => {
    let list = conversations;
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((c) => c.title.toLowerCase().includes(q) || c.snippet.toLowerCase().includes(q));
    }
    if (sourceFilter !== "all") list = list.filter((c) => c.source === sourceFilter);
    if (unreadOnly) list = list.filter((c) => c.unread_count > 0);
    return [...list].sort((a, b) => {
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });
  }, [conversations, search, sourceFilter, unreadOnly]);

  const activeConv = conversations.find((c) => c.id === activeConvId);
  const messages = activeConvId ? (MOCK_MESSAGES[activeConvId] ?? []) : [];

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-[var(--axiom-bg-base)]">
      {/* Left Sidebar — Conversation List */}
      <div className="w-[320px] flex-shrink-0 border-r border-[var(--axiom-border)] flex flex-col bg-[var(--axiom-bg-surface)]">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[var(--axiom-border)]">
          <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Inbox</h2>
          {/* Search */}
          <div className="relative mt-2">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--axiom-text-tertiary)] pointer-events-none">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
            </svg>
            <input
              value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search conversations..."
              className="w-full h-8 pl-8 pr-3 text-[12px] bg-[var(--axiom-bg-elevated)] rounded-lg text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] outline-none border border-[var(--axiom-border)] focus:border-[var(--axiom-accent)] transition-colors"
            />
          </div>
          {/* Filters */}
          <div className="flex items-center gap-1.5 mt-2 overflow-x-auto pb-1 scrollbar-none">
            {SOURCE_FILTERS.slice(0, 5).map((f) => (
              <button key={f.key} onClick={() => setSourceFilter(f.key)}
                className={`text-[10px] px-2 py-1 rounded-full whitespace-nowrap transition-colors ${sourceFilter === f.key ? "bg-[var(--axiom-accent)] text-white" : "bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"}`}>
                {f.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1.5 mt-1">
            {SOURCE_FILTERS.slice(5).map((f) => (
              <button key={f.key} onClick={() => setSourceFilter(f.key)}
                className={`text-[10px] px-2 py-1 rounded-full whitespace-nowrap transition-colors ${sourceFilter === f.key ? "bg-[var(--axiom-accent)] text-white" : "bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"}`}>
                {f.label}
              </button>
            ))}
            <button onClick={() => setUnreadOnly(!unreadOnly)}
              className={`text-[10px] px-2 py-1 rounded-full transition-colors ${unreadOnly ? "bg-amber-500/15 text-amber-400" : "bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)]"}`}>
              Unread only
            </button>
          </div>
        </div>
        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-tertiary)] mb-3">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <p className="text-sm text-[var(--axiom-text-tertiary)]">No conversations found</p>
            </div>
          ) : (
            filtered.map((conv) => (
              <ConversationItem key={conv.id} conv={conv} isActive={conv.id === activeConvId} onClick={() => setActiveConvId(conv.id)} />
            ))
          )}
        </div>
      </div>

      {/* Main Area — Message Thread */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeConv ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]">
              <div className="flex items-center gap-3">
                <AvatarCircle name={activeConv.title} source={activeConv.source} />
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)]">{activeConv.title}</h3>
                    <SourceBadge source={activeConv.source} />
                    {activeConv.pinned && <span className="text-[10px]">📌</span>}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    {activeConv.participants.map((p) => (
                      <span key={p.id} className="text-[10px] text-[var(--axiom-text-tertiary)]">{p.name}</span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => setShowContext(!showContext)}
                  className={`p-1.5 rounded-md transition-colors ${showContext ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"}`}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                </button>
              </div>
            </div>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-sm text-[var(--axiom-text-tertiary)]">No messages in this conversation yet.</p>
                </div>
              ) : (
                messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
              )}
            </div>
            {/* Input */}
            <div className="px-5 py-3 border-t border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]">
              <div className="flex items-center gap-2 glass-panel px-3 py-2">
                <button className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                </button>
                <input placeholder="Reply as AXIOM..." className="flex-1 bg-transparent text-sm text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] outline-none" />
                <button className="p-1.5 rounded-md bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-tertiary)] mx-auto mb-4 opacity-40">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <p className="text-sm text-[var(--axiom-text-tertiary)]">Select a conversation to view messages</p>
            </div>
          </div>
        )}
      </div>

      {/* Right Context Panel */}
      <AnimatePresence>
        {showContext && activeConv && (
          <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 300, opacity: 1 }} exit={{ width: 0, opacity: 0 }} className="border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-hidden flex-shrink-0">
            <div className="w-[300px] h-full flex flex-col">
              <div className="px-4 py-3 border-b border-[var(--axiom-border)]">
                <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Details</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <div>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide font-medium mb-1">Participants</p>
                  {activeConv.participants.map((p) => (
                    <div key={p.id} className="flex items-center gap-2 py-1">
                      <AvatarCircle name={p.name} source={p.source} size="sm" />
                      <div>
                        <p className="text-xs text-[var(--axiom-text-primary)]">{p.name}</p>
                        <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{p.role}</p>
                      </div>
                    </div>
                  ))}
                </div>
                {activeConv.project_id && (
                  <div>
                    <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide font-medium mb-1">Linked Project</p>
                    <div className="glass-card px-3 py-2 text-xs text-[var(--axiom-text-primary)]">{activeConv.project_id}</div>
                  </div>
                )}
                <div>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide font-medium mb-1">Labels</p>
                  <div className="flex flex-wrap gap-1">
                    {activeConv.labels.map((l) => (
                      <span key={l} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)]">{l}</span>
                    ))}
                  </div>
                </div>
                <div className="space-y-1">
                  <button className="w-full text-left text-xs px-3 py-2 rounded-md hover:bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] transition-colors">📌 Pin conversation</button>
                  <button className="w-full text-left text-xs px-3 py-2 rounded-md hover:bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] transition-colors">✓ Mark all read</button>
                  <button className="w-full text-left text-xs px-3 py-2 rounded-md hover:bg-red-500/10 text-red-400 transition-colors">🗑 Archive</button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}