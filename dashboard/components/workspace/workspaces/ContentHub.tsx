"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { ContentAsset, AssetType } from "../../../lib/phase8c-types";

/* ── Config ───────────────────────────────────────────────────────── */

const TYPE_COLORS: Record<AssetType, string> = {
  research: "bg-violet-500", document: "bg-blue-500", image: "bg-pink-500",
  video: "bg-rose-500", audio: "bg-cyan-500", code: "bg-emerald-500",
  report: "bg-amber-500", presentation: "bg-orange-500", spreadsheet: "bg-green-500",
};

const TYPE_ICONS: Record<AssetType, string> = {
  research: "\u{1F50D}", document: "\u{1F4C4}", image: "\u{1F5BC}",
  video: "\u{1F3AC}", audio: "\u{1F399}", code: "\u{1F4BB}",
  report: "\u{1F4CA}", presentation: "\u{1F4CA}", spreadsheet: "\u{1F4D1}",
};

const TYPE_LABELS: Record<AssetType, string> = {
  research: "Research", document: "Document", image: "Image",
  video: "Video", audio: "Audio", code: "Code",
  report: "Report", presentation: "Presentation", spreadsheet: "Spreadsheet",
};

const ALL_TYPES: AssetType[] = ["research", "document", "image", "video", "audio", "code", "report", "presentation", "spreadsheet"];

/* ── Mock Data ────────────────────────────────────────────────────── */

const MOCK_ASSETS: ContentAsset[] = [
  { id: "a1", type: "research", title: "AI Market Trends Q3 2026", description: "Comprehensive analysis of AI market trends, competitive landscape, and emerging technologies for Q3 2026 planning.", tags: ["strategic", "ai", "market"], project_id: "q3-planning", executive_id: "jenson", executive_name: "Jenson", memory_refs: ["mem-1", "mem-2"], current_version: 3, created_at: new Date(Date.now() - 86400000 * 2).toISOString(), updated_at: new Date().toISOString(), size: 2450000, starred: true, version_history: [], preview_type: "markdown",
  },
  { id: "a2", type: "document", title: "Bleval Sales Strategy v3", description: "Updated sales playbook with new outreach sequences, qualification criteria, and closing frameworks.", tags: ["sales", "strategy", "final"], project_id: "q3-planning", executive_id: "jenson", executive_name: "Jenson", memory_refs: ["mem-3"], current_version: 3, created_at: new Date(Date.now() - 86400000 * 5).toISOString(), updated_at: new Date(Date.now() - 86400000).toISOString(), size: 890000, starred: true, version_history: [], preview_type: "markdown",
  },
  { id: "a3", type: "code", title: "Feature Implementation: Lead Scoring", description: "Machine learning model for automated lead scoring based on company fit, engagement signals, and historical conversion data.", tags: ["development", "ml", "in-progress"], project_id: "lead-scoring", executive_id: "jenson", executive_name: "Jenson", memory_refs: ["mem-4"], current_version: 7, created_at: new Date(Date.now() - 86400000 * 3).toISOString(), updated_at: new Date(Date.now() - 3600000).toISOString(), size: 15600000, starred: false, version_history: [], preview_type: "code",
  },
  { id: "a4", type: "report", title: "Weekly Executive Summary — Jul 31", description: "Weekly summary of executive decisions, workflow completions, and key metrics across all departments.", tags: ["weekly", "executive", "report"], executive_id: "jenson", executive_name: "Jenson", memory_refs: ["mem-5"], current_version: 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), size: 340000, starred: false, version_history: [], preview_type: "text",
  },
  { id: "a5", type: "image", title: "Brand Guidelines — Cover Page", description: "Updated brand guidelines cover with new color palette and typography system.", tags: ["brand", "design", "draft"], executive_id: "valta", executive_name: "Valta Prime", memory_refs: [], current_version: 4, created_at: new Date(Date.now() - 86400000 * 7).toISOString(), updated_at: new Date(Date.now() - 86400000 * 2).toISOString(), size: 4200000, starred: true, version_history: [], preview_type: "image",
  },
  { id: "a6", type: "presentation", title: "Q4 Board Deck", description: "Quarterly board presentation covering performance, strategy, and outlook for Q4 2026.", tags: ["board", "quarterly", "draft"], executive_id: "jenson", executive_name: "Jenson", memory_refs: ["mem-6"], current_version: 2, created_at: new Date(Date.now() - 86400000 * 10).toISOString(), updated_at: new Date(Date.now() - 86400000 * 3).toISOString(), size: 8900000, starred: false, version_history: [], preview_type: "markdown",
  },
  { id: "a7", type: "spreadsheet", title: "Budget Allocation FY2027", description: "Annual budget allocation spreadsheet with departmental breakdowns, projections, and scenario analysis.", tags: ["finance", "budget", "final"], executive_id: "yamako", executive_name: "Yamako", memory_refs: ["mem-7"], current_version: 5, created_at: new Date(Date.now() - 86400000 * 14).toISOString(), updated_at: new Date(Date.now() - 86400000).toISOString(), size: 2300000, starred: false, version_history: [], preview_type: "text",
  },
  { id: "a8", type: "audio", title: "Jenson Strategy Session Recording", description: "Recording of Jenson's strategic planning session covering Q3 priorities and resource allocation.", tags: ["meeting", "strategy"], executive_id: "jenson", executive_name: "Jenson", memory_refs: [], current_version: 1, created_at: new Date(Date.now() - 86400000 * 3).toISOString(), updated_at: new Date(Date.now() - 86400000 * 3).toISOString(), size: 45000000, starred: false, version_history: [], preview_type: "text",
  },
  { id: "a9", type: "video", title: "Product Demo Walkthrough", description: "Walkthrough demo of the AXIOM operating system highlighting key features and workflows.", tags: ["demo", "product", "final"], executive_id: "jenson", executive_name: "Jenson", memory_refs: [], current_version: 2, created_at: new Date(Date.now() - 86400000 * 21).toISOString(), updated_at: new Date(Date.now() - 86400000 * 14).toISOString(), size: 128000000, starred: true, version_history: [], preview_type: "image",
  },
];

/* ── Sub-Components ───────────────────────────────────────────────── */

function TypeBadge({ type }: { type: AssetType }) {
  return <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${TYPE_COLORS[type].replace("bg-", "bg-").replace("500", "500/15")} ${TYPE_COLORS[type].replace("bg-", "text-").replace("500", "400")}`}>{TYPE_LABELS[type]}</span>;
}

function AssetCard({ asset, onClick }: { asset: ContentAsset; onClick: () => void }) {
  const gradients: Record<AssetType, string> = {
    research: "from-violet-500/20 to-violet-800/10",
    document: "from-blue-500/20 to-blue-800/10",
    image: "from-pink-500/20 to-pink-800/10",
    video: "from-rose-500/20 to-rose-800/10",
    audio: "from-cyan-500/20 to-cyan-800/10",
    code: "from-emerald-500/20 to-emerald-800/10",
    report: "from-amber-500/20 to-amber-800/10",
    presentation: "from-orange-500/20 to-orange-800/10",
    spreadsheet: "from-green-500/20 to-green-800/10",
  };
  return (
    <motion.button onClick={onClick} whileHover={{ y: -2 }} className="glass-card overflow-hidden text-left group">
      {/* Preview */}
      <div className={`h-24 bg-gradient-to-br ${gradients[asset.type]} flex items-center justify-center relative`}>
        <span className="text-3xl">{TYPE_ICONS[asset.type]}</span>
        <button onClick={(e) => { e.stopPropagation(); }} className="absolute top-2 right-2 text-lg opacity-0 group-hover:opacity-100 transition-opacity">{asset.starred ? "★" : "☆"}</button>
      </div>
      {/* Content */}
      <div className="p-3">
        <TypeBadge type={asset.type} />
        <h4 className="text-sm font-medium text-[var(--axiom-text-primary)] mt-1 line-clamp-1">{asset.title}</h4>
        <p className="text-[11px] text-[var(--axiom-text-tertiary)] mt-0.5 line-clamp-2">{asset.description}</p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-[10px] text-[var(--axiom-text-secondary)]">{asset.executive_name ?? "Unknown"}</span>
          <span className="text-[9px] text-[var(--axiom-text-tertiary)]">{Math.round(asset.size / 1024 / (asset.size > 1048576 ? 1024 : 1))}{asset.size > 1048576 ? "MB" : "KB"}</span>
        </div>
        {asset.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {asset.tags.slice(0, 3).map((t) => <span key={t} className="text-[8px] px-1.5 py-0.5 rounded bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-tertiary)]">{t}</span>)}
            {asset.tags.length > 3 && <span className="text-[8px] text-[var(--axiom-text-tertiary)]">+{asset.tags.length - 3}</span>}
          </div>
        )}
      </div>
    </motion.button>
  );
}

function AssetDetail({ asset, onClose }: { asset: ContentAsset; onClose: () => void }) {
  return (
    <motion.div initial={{ x: 420 }} animate={{ x: 0 }} exit={{ x: 420 }} transition={{ type: "spring", damping: 25, stiffness: 200 }} className="w-[420px] flex-shrink-0 border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-y-auto">
      <div className="px-5 py-4 border-b border-[var(--axiom-border)] flex items-center justify-between">
        <TypeBadge type={asset.type} />
        <button onClick={onClose} className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>
      <div className="p-5 space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-[var(--axiom-text-primary)]">{asset.title}</h2>
          <p className="text-sm text-[var(--axiom-text-secondary)] mt-2">{asset.description}</p>
        </div>
        <div className="flex flex-wrap gap-1">
          {asset.tags.map((t) => <span key={t} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)]">{t}</span>)}
        </div>
        {/* Version History */}
        <div>
          <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-2">Version History</h4>
          <div className="space-y-2">
            {Array.from({ length: asset.current_version }, (_, i) => i + 1).reverse().map((v) => (
              <div key={v} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--axiom-bg-elevated)]">
                <span className={`w-5 h-5 rounded-full ${v === asset.current_version ? "bg-[var(--axiom-accent)]" : "bg-zinc-500"} text-[9px] text-white flex items-center justify-center font-bold`}>{v}</span>
                <div className="flex-1">
                  <span className="text-xs text-[var(--axiom-text-primary)]">Version {v}</span>
                  <p className="text-[10px] text-[var(--axiom-text-tertiary)]">{v === asset.current_version ? "Current version" : `Updated ${Math.floor(Math.random() * 10 + 1)}d ago`}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Executive</p>
            <p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{asset.executive_name}</p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Created</p>
            <p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{new Date(asset.created_at).toLocaleDateString()}</p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Size</p>
            <p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{Math.round(asset.size / 1024 / (asset.size > 1048576 ? 1024 : 1))}{asset.size > 1048576 ? "MB" : "KB"}</p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase">Versions</p>
            <p className="text-xs text-[var(--axiom-text-primary)] mt-0.5">{asset.current_version}</p>
          </div>
        </div>
        {/* Actions */}
        <div className="flex gap-2">
          <button className="flex-1 px-4 py-2 text-xs font-medium rounded-lg bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors">Preview</button>
          <button className="flex-1 px-4 py-2 text-xs font-medium rounded-lg border border-[var(--axiom-border)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors">Export</button>
        </div>
        {asset.memory_refs.length > 0 && (
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase mb-1">Memory References</p>
            <div className="space-y-1">
              {asset.memory_refs.map((ref) => (
                <div key={ref} className="text-xs text-[var(--axiom-accent)] font-mono">{ref}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

/* ── Main Component ───────────────────────────────────────────────── */

export default function ContentHub() {
  const [assets] = useState(MOCK_ASSETS);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<AssetType | "all">("all");
  const [starredOnly, setStarredOnly] = useState(false);
  const [activeAsset, setActiveAsset] = useState<ContentAsset | null>(null);
  const [sort, setSort] = useState<"newest" | "oldest" | "name">("newest");

  const filtered = useMemo(() => {
    let list = assets;
    if (typeFilter !== "all") list = list.filter((a) => a.type === typeFilter);
    if (search.trim()) { const q = search.toLowerCase(); list = list.filter((a) => a.title.toLowerCase().includes(q) || a.description.toLowerCase().includes(q)); }
    if (starredOnly) list = list.filter((a) => a.starred);
    return [...list].sort((a, b) => {
      if (sort === "newest") return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      if (sort === "oldest") return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
      return a.title.localeCompare(b.title);
    });
  }, [assets, search, typeFilter, starredOnly, sort]);

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-[var(--axiom-bg-base)]">
      {/* Left Panel — Library Navigation */}
      <div className="w-[260px] flex-shrink-0 border-r border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-y-auto">
        <div className="px-4 py-3 border-b border-[var(--axiom-border)]">
          <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Content Library</h2>
          <div className="relative mt-2">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--axiom-text-tertiary)]"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search assets..." className="w-full h-8 pl-8 pr-3 text-[12px] bg-[var(--axiom-bg-elevated)] rounded-lg text-[var(--axiom-text-primary)] placeholder:text-[var(--axiom-text-tertiary)] outline-none border border-[var(--axiom-border)] focus:border-[var(--axiom-accent)]" />
          </div>
        </div>
        <div className="p-3 space-y-1">
          <button onClick={() => setTypeFilter("all")} className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex items-center gap-2 ${typeFilter === "all" ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]" : "text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"}`}>
            <span>📋</span> All <span className="text-[10px] text-[var(--axiom-text-tertiary)]">({assets.length})</span>
          </button>
          {ALL_TYPES.map((t) => (
            <button key={t} onClick={() => setTypeFilter(t)} className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex items-center gap-2 ${typeFilter === t ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]" : "text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"}`}>
              <span>{TYPE_ICONS[t]}</span> {TYPE_LABELS[t]}
            </button>
          ))}
          <div className="border-t border-[var(--axiom-border)] my-2" />
          <button onClick={() => setStarredOnly(!starredOnly)} className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex items-center gap-2 ${starredOnly ? "bg-amber-500/15 text-amber-400" : "text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"}`}>
            <span>{starredOnly ? "★" : "☆"}</span> Starred
          </button>
        </div>
      </div>

      {/* Main Content — Asset Grid */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Sort */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)]">
          <p className="text-[11px] text-[var(--axiom-text-tertiary)]">{filtered.length} asset{filtered.length !== 1 ? "s" : ""}</p>
          <div className="flex gap-1">
            {(["newest", "oldest", "name"] as const).map((s) => (
              <button key={s} onClick={() => setSort(s)} className={`text-[10px] px-2 py-1 rounded ${sort === s ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"}`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
            ))}
          </div>
        </div>
        {/* Grid */}
        <div className="flex-1 overflow-y-auto p-5">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <span className="text-4xl mb-3">📁</span>
              <p className="text-sm text-[var(--axiom-text-tertiary)]">No generated assets yet</p>
              <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">Start a conversation to create assets</p>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {filtered.map((a) => <AssetCard key={a.id} asset={a} onClick={() => setActiveAsset(a)} />)}
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      <AnimatePresence>
        {activeAsset && <AssetDetail asset={activeAsset} onClose={() => setActiveAsset(null)} />}
      </AnimatePresence>
    </div>
  );
}