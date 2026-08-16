"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { axiom } from "../../../lib/api";
import type {
  ResearchWorkspaceSummary,
  ResearchWorkspace,
  ResearchFinding,
  ConversationEntry,
} from "../../../lib/api-types";

/* ── Sub-components ───────────────────────────────────────────────── */

function WorkspaceCard({
  ws,
  onSelect,
  onArchive,
}: {
  ws: ResearchWorkspaceSummary;
  onSelect: () => void;
  onArchive: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className="w-full text-left p-4 rounded-xl bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] hover:border-[var(--axiom-accent)] transition-colors group"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-[var(--axiom-text-primary)] truncate">
            {ws.title}
          </h3>
          <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1 truncate">
            {ws.query}
          </p>
        </div>
        <span
          className={`text-[10px] font-mono px-1.5 py-0.5 rounded border flex-shrink-0 ml-2 ${
            ws.status === "active"
              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
              : ws.status === "archived"
              ? "bg-neutral-500/20 text-neutral-400 border-neutral-500/30"
              : "bg-amber-500/20 text-amber-400 border-amber-500/30"
          }`}
        >
          {ws.status}
        </span>
      </div>
      <div className="flex items-center gap-4 mt-3 text-[10px] text-[var(--axiom-text-tertiary)]">
        <span>📄 {ws.sources_count} sources</span>
        <span>🔍 {ws.findings_count} findings</span>
        <span>💬 {ws.conversation_length} messages</span>
      </div>
      <div className="flex justify-end mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onArchive();
          }}
          className="text-[10px] text-red-400 hover:text-red-300 px-2 py-0.5 rounded hover:bg-red-500/10 transition-colors"
        >
          Archive
        </button>
      </div>
    </button>
  );
}

function CreateForm({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!title.trim() || !query.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      await axiom.research.create(title.trim(), query.trim());
      onCreated();
    } catch {
      setError("Failed to create workspace. Is the backend running?");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg bg-[var(--axiom-bg-surface)] border border-[var(--axiom-border)] rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)] mb-4">
          New Research Workspace
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wide mb-1">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Market Analysis Q3"
              className="w-full bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] rounded-lg px-3 py-2 text-sm text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] focus:outline-none focus:border-[var(--axiom-accent)]"
            />
          </div>

          <div>
            <label className="block text-[10px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wide mb-1">
              Research Query
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe what you want to research..."
              rows={3}
              className="w-full bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] rounded-lg px-3 py-2 text-sm text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] focus:outline-none focus:border-[var(--axiom-accent)] resize-none"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-[var(--axiom-text-secondary)] border border-[var(--axiom-border)] rounded-lg hover:bg-[var(--axiom-bg-elevated)] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !title.trim() || !query.trim()}
              className="px-4 py-2 text-xs font-medium bg-[var(--axiom-accent)] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? "Creating..." : "Create Workspace"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────────────── */

export default function ResearchWorkspaceView() {
  const [workspaces, setWorkspaces] = useState<ResearchWorkspaceSummary[]>([]);
  const [selectedWs, setSelectedWs] = useState<ResearchWorkspace | null>(null);
  const [detailTab, setDetailTab] = useState<"conversation" | "findings" | "sources">("conversation");
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWorkspaces = async () => {
    try {
      const list = await axiom.research.list();
      setWorkspaces(list);
      setError(null);
    } catch {
      setError("Could not reach AXIOM backend.");
    }
    setLoading(false);
  };

  useEffect(() => {
    loadWorkspaces();
  }, []);

  // Refetch periodically
  useEffect(() => {
    const interval = setInterval(loadWorkspaces, 30_000);
    return () => clearInterval(interval);
  }, []);

  const openWorkspace = async (id: string) => {
    try {
      const detail = await axiom.research.get(id);
      setSelectedWs(detail);
    } catch {
      setError("Failed to load workspace details.");
    }
  };

  const archiveWorkspace = async (id: string) => {
    try {
      await axiom.research.archive(id);
      setWorkspaces((prev) => prev.filter((w) => w.id !== id));
    } catch {
      setError("Failed to archive workspace.");
    }
  };

  const addConversation = async (role: string, content: string) => {
    if (!selectedWs) return;
    try {
      const updated = await axiom.research.addConversation(selectedWs.id, role, content);
      setSelectedWs(updated);
    } catch {
      setError("Failed to add conversation entry.");
    }
  };

  const addFinding = async (content: string, title?: string) => {
    if (!selectedWs) return;
    try {
      const updated = await axiom.research.addFinding(selectedWs.id, content, title);
      setSelectedWs(updated);
    } catch {
      setError("Failed to add finding.");
    }
  };

  // Detail view header
  if (selectedWs) {
    return (
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Detail Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedWs(null)}
              className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 12H5" />
                <path d="m12 19-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">
                {selectedWs.title}
              </h2>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{selectedWs.query}</p>
            </div>
          </div>
          <span className="text-[10px] text-[var(--axiom-text-tertiary)]">
            {new Date(selectedWs.created_at).toLocaleDateString()}
          </span>
        </div>

        {/* Detail Tabs */}
        <div className="flex border-b border-[var(--axiom-border)] px-6">
          {(["conversation", "findings", "sources"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setDetailTab(t)}
              className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors capitalize ${
                detailTab === t
                  ? "border-[var(--axiom-accent)] text-[var(--axiom-accent)]"
                  : "border-transparent text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
              }`}
            >
              {t} {t === "findings" ? `(${selectedWs.findings.length})` : t === "sources" ? `(${selectedWs.sources.length})` : `(${selectedWs.conversation.length})`}
            </button>
          ))}
        </div>

        {/* Detail Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {detailTab === "conversation" && (
            <div className="space-y-3">
              {selectedWs.conversation.length === 0 && (
                <p className="text-sm text-[var(--axiom-text-tertiary)] text-center py-8">
                  No conversation entries yet. Use AXIOM to populate this workspace.
                </p>
              )}
              {selectedWs.conversation.map((entry: ConversationEntry, i: number) => (
                <div
                  key={i}
                  className={`flex gap-2 ${entry.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] mt-1 flex-shrink-0">
                    {entry.role === "user" ? "U" : "A"}
                  </span>
                  <div
                    className={`rounded-lg px-3 py-2 text-sm max-w-[80%] ${
                      entry.role === "user"
                        ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-text-primary)]"
                        : "bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)] text-[var(--axiom-text-secondary)]"
                    }`}
                  >
                    {entry.content}
                    {entry.timestamp && (
                      <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-1">
                        {new Date(entry.timestamp).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {detailTab === "findings" && (
            <div className="space-y-3">
              {selectedWs.findings.length === 0 && (
                <p className="text-sm text-[var(--axiom-text-tertiary)] text-center py-8">
                  No findings yet.
                </p>
              )}
              {selectedWs.findings.map((f: ResearchFinding, i: number) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)]"
                >
                  {f.title && (
                    <h4 className="text-xs font-medium text-[var(--axiom-text-primary)] mb-1">
                      {f.title}
                    </h4>
                  )}
                  <p className="text-sm text-[var(--axiom-text-secondary)]">{f.content}</p>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-[var(--axiom-text-tertiary)]">
                    {f.confidence !== undefined && (
                      <span>Confidence: {Math.round(f.confidence * 100)}%</span>
                    )}
                    {f.source && <span>Source: {f.source}</span>}
                    <span>{new Date(f.added_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {detailTab === "sources" && (
            <div className="space-y-2">
              {selectedWs.sources.length === 0 && (
                <p className="text-sm text-[var(--axiom-text-tertiary)] text-center py-8">
                  No sources added yet.
                </p>
              )}
              {selectedWs.sources.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg bg-[var(--axiom-bg-elevated)] border border-[var(--axiom-border)]"
                >
                  <div>
                    <p className="text-xs font-medium text-[var(--axiom-text-primary)]">
                      {s.title || "Untitled"}
                    </p>
                    <p className="text-[10px] text-[var(--axiom-text-tertiary)]">
                      {s.type}
                      {s.url && ` — ${s.url}`}
                    </p>
                  </div>
                  <span className="text-[10px] text-[var(--axiom-text-tertiary)]">
                    {new Date(s.added_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── List view ─────────────────────────────────────────────────────

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-3">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Research Workspaces</h2>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-3 py-1.5 bg-[var(--axiom-accent)] text-white rounded-lg text-xs font-medium hover:opacity-90 transition-opacity flex items-center gap-1.5"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14" />
            <path d="M12 5v14" />
          </svg>
          New Research
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400 mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-2 border-[var(--axiom-accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : workspaces.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] mb-3">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <p className="text-sm text-[var(--axiom-text-tertiary)]">No research workspaces yet</p>
            <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">
              Create one to start researching with AXIOM
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="mt-4 px-4 py-2 bg-[var(--axiom-accent)] text-white rounded-lg text-xs font-medium hover:opacity-90 transition-opacity"
            >
              Create Workspace
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {workspaces.map((ws) => (
              <WorkspaceCard
                key={ws.id}
                ws={ws}
                onSelect={() => openWorkspace(ws.id)}
                onArchive={() => archiveWorkspace(ws.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <CreateForm
            onClose={() => setShowCreate(false)}
            onCreated={() => {
              setShowCreate(false);
              loadWorkspaces();
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}