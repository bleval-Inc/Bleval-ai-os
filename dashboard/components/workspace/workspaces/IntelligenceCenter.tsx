"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* Types */

interface ReasoningStep {
  id: string; type: string; title: string; description: string; duration_ms: number; confidence: number;
}

interface ActiveReasoning {
  id: string; agent_id: string; task: string; status: string; model: string; provider: string;
  tokens_used: number; confidence: number; reasoning_chain: ReasoningStep[];
}

interface ProviderUsage {
  provider: string; model: string; tokens_in: number; tokens_out: number;
  requests: number; avg_latency_ms: number; cost_estimate: number;
}

/* Mock Data */

const MOCK_REASONING: ActiveReasoning[] = [
  {
    id: "r1", agent_id: "Jenson", task: "Strategic resource allocation for Q3", status: "reasoning",
    model: "Claude Sonnet 4", provider: "Anthropic", tokens_used: 12450, confidence: 0.87,
    reasoning_chain: [
      { id: "rs1", type: "analysis", title: "Analyzing department requests", description: "Reviewing budget proposals from all 5 departments", duration_ms: 2340, confidence: 0.92 },
      { id: "rs2", type: "memory_check", title: "Checking past allocations", description: "Retrieving Q2 allocation data from memory", duration_ms: 890, confidence: 0.95 },
      { id: "rs3", type: "tool_call", title: "Running financial model", description: "Calculating ROI projections per department", duration_ms: 4200, confidence: 0.78 },
      { id: "rs4", type: "decision", title: "Drafting recommendation", description: "Formulating optimal allocation split", duration_ms: 1800, confidence: 0.83 },
    ],
  },
  {
    id: "r2", agent_id: "Valta Prime", task: "Brand identity refresh strategy", status: "executing",
    model: "GPT-4o", provider: "OpenAI", tokens_used: 8930, confidence: 0.91,
    reasoning_chain: [
      { id: "rs5", type: "analysis", title: "Analyzing brand audit results", description: "Reviewing competitor brand analysis", duration_ms: 3100, confidence: 0.94 },
      { id: "rs6", type: "tool_call", title: "Generating color palette", description: "Creating 3 color palette options", duration_ms: 5600, confidence: 0.88 },
    ],
  },
  {
    id: "r3", agent_id: "Yamako", task: "Optimize founder schedule for next week", status: "reasoning",
    model: "GLM-5.2", provider: "NVIDIA", tokens_used: 4200, confidence: 0.76,
    reasoning_chain: [
      { id: "rs7", type: "analysis", title: "Analyzing calendar conflicts", description: "Cross-referencing 14 meetings", duration_ms: 1500, confidence: 0.85 },
      { id: "rs8", type: "memory_check", title: "Checking priority tasks", description: "Retrieving founder's priority list", duration_ms: 600, confidence: 0.90 },
    ],
  },
];

const MOCK_PROVIDERS: ProviderUsage[] = [
  { provider: "Anthropic", model: "Claude Sonnet 4", tokens_in: 245000, tokens_out: 32000, requests: 156, avg_latency_ms: 1240, cost_estimate: 4.68 },
  { provider: "Anthropic", model: "Claude Haiku 4", tokens_in: 89000, tokens_out: 12000, requests: 89, avg_latency_ms: 580, cost_estimate: 0.45 },
  { provider: "OpenAI", model: "GPT-4o", tokens_in: 178000, tokens_out: 24000, requests: 112, avg_latency_ms: 980, cost_estimate: 3.20 },
  { provider: "NVIDIA", model: "GLM-5.2", tokens_in: 56000, tokens_out: 8000, requests: 34, avg_latency_ms: 2100, cost_estimate: 0.00 },
];

/* Helpers */

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = { reasoning: "bg-blue-400 animate-pulse", executing: "bg-amber-400", complete: "bg-emerald-400", error: "bg-red-400" };
  return <span className={`w-2 h-2 rounded-full ${colors[status] ?? "bg-zinc-500"}`} />;
}

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 0.9 ? "bg-emerald-500" : value >= 0.8 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-[var(--axiom-bg-elevated)] overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
      <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] w-8 text-right">{Math.round(value * 100)}%</span>
    </div>
  );
}

function StatCard({ label, value, sub, pulse }: { label: string; value: string; sub?: string; pulse?: boolean }) {
  return (
    <div className="glass-card px-3 py-2.5 flex-1 min-w-[120px]">
      <div className="flex items-center gap-1.5">
        {pulse && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
        <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wide">{label}</p>
      </div>
      <p className="text-lg font-semibold text-[var(--axiom-text-primary)] mt-0.5 font-mono tabular-nums">{value}</p>
      {sub && <p className="text-[9px] text-[var(--axiom-text-tertiary)] mt-0.5">{sub}</p>}
    </div>
  );
}

/* Reasoning Detail */

function ReasoningDetail({ item }: { item: ActiveReasoning }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="glass-card">
      <button onClick={() => setExpanded(!expanded)} className="w-full text-left px-4 py-3 flex items-center gap-3">
        <StatusDot status={item.status} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-[var(--axiom-text-primary)]">{item.agent_id}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
              item.status === "reasoning" ? "bg-blue-500/15 text-blue-400" :
              item.status === "executing" ? "bg-amber-500/15 text-amber-400" :
              item.status === "complete" ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"
            }`}>{item.status}</span>
          </div>
          <p className="text-[11px] text-[var(--axiom-text-secondary)] mt-0.5 line-clamp-1">{item.task}</p>
        </div>
        <div className="text-right text-[10px] text-[var(--axiom-text-tertiary)]">
          <p>{item.model}</p>
          <p>{item.tokens_used.toLocaleString()} tokens</p>
        </div>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={`text-[var(--axiom-text-tertiary)] transition-transform ${expanded ? "rotate-180" : ""}`}><polyline points="6 9 12 15 18 9"/></svg>
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="px-4 pb-4 border-t border-[var(--axiom-border)] pt-3 space-y-3">
              {item.reasoning_chain.map((step, i) => (
                <div key={step.id} className="flex gap-3">
                  {/* Timeline */}
                  <div className="flex flex-col items-center">
                    <div className={`w-2.5 h-2.5 rounded-full border-2 ${i < item.reasoning_chain.length - 1 ? "border-[var(--axiom-accent)]" : "border-emerald-400"} flex-shrink-0`} />
                    {i < item.reasoning_chain.length - 1 && <div className="w-px flex-1 bg-[var(--axiom-border)] my-1" />}
                  </div>
                  <div className="flex-1 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-[var(--axiom-text-primary)]">{step.title}</span>
                      <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">{step.duration_ms}ms</span>
                    </div>
                    <p className="text-[11px] text-[var(--axiom-text-secondary)] mt-0.5">{step.description}</p>
                    <ConfidenceBar value={step.confidence} />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* Main Component */

export default function IntelligenceCenter() {
  const [activeReasoning] = useState(MOCK_REASONING);
  const [providers] = useState(MOCK_PROVIDERS);
  const [lastUpdated, setLastUpdated] = useState(Date.now());
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(() => setLastUpdated(Date.now()), 10000);
    return () => clearInterval(interval);
  }, []);

  const totalTokens = MOCK_PROVIDERS.reduce((s, p) => s + p.tokens_in + p.tokens_out, 0);
  const totalRequests = MOCK_PROVIDERS.reduce((s, p) => s + p.requests, 0);
  const avgLatency = Math.round(MOCK_PROVIDERS.reduce((s, p) => s + p.avg_latency_ms, 0) / MOCK_PROVIDERS.length);
  const avgConfidence = activeReasoning.length > 0 ? Math.round(activeReasoning.reduce((s, r) => s + r.confidence, 0) / activeReasoning.length * 100) : 0;

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-[var(--axiom-bg-base)]">
      <div className="flex-1 overflow-y-auto">
        <div className="p-5 max-w-[1400px] mx-auto space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-[var(--axiom-text-primary)]">Intelligence Center</h2>
              <p className="text-[11px] text-[var(--axiom-text-tertiary)]">Live reasoning, model selection, and execution metrics — updated {(Date.now() - lastUpdated) / 1000 < 60 ? "moments ago" : `${Math.floor((Date.now() - lastUpdated) / 60000)}m ago`}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] text-[var(--axiom-text-tertiary)]">Live</span>
            </div>
          </div>

          {/* Overview Stats */}
          <div className="flex flex-wrap gap-3">
            <StatCard label="Active Reasoning" value={activeReasoning.length.toString()} sub={`${activeReasoning.filter(r => r.status === "reasoning").length} reasoning, ${activeReasoning.filter(r => r.status === "executing").length} executing`} pulse />
            <StatCard label="Tokens Today" value={(totalTokens / 1000).toFixed(0) + "K"} sub={`${totalRequests} requests`} />
            <StatCard label="Avg Latency" value={`${avgLatency}ms`} sub={avgLatency < 1000 ? "Fast" : avgLatency < 2000 ? "Moderate" : "Slow"} />
            <StatCard label="Avg Confidence" value={`${avgConfidence}%`} sub={avgConfidence >= 85 ? "High confidence" : "Needs review"} />
            <StatCard label="P95 Latency" value="2.1s" sub="Last 24h" />
            <StatCard label="P99 Latency" value="4.3s" sub="Last 24h" />
          </div>

          {/* Active Reasoning Section */}
          <div>
            <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-3 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              Active Reasoning Chains
              <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-normal">({activeReasoning.length})</span>
            </h3>
            <div className="space-y-2">
              {activeReasoning.map((r) => <ReasoningDetail key={r.id} item={r} />)}
            </div>
          </div>

          {/* Tool Executions + Memory Retrievals */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-3">Recent Tool Executions</h3>
              <div className="space-y-1.5">
                {["get_telemetry", "system_diagnostics", "launch_application", "send_notification", "check_connectivity"].map((tool, i) => (
                  <div key={tool} className="glass-card px-3 py-2 flex items-center gap-2.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${i < 4 ? "bg-emerald-400" : "bg-red-400"}`} />
                    <span className="flex-1 text-xs text-[var(--axiom-text-primary)] font-mono">{tool}</span>
                    <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{Math.floor(Math.random() * 3000 + 200)}ms</span>
                    <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{Math.floor(Math.random() * 10 + 1)}m ago</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-3">Memory Retrievals</h3>
              <div className="space-y-1.5">
                {[
                  { agent: "Jenson", query: "Q2 allocation data", results: 4, conf: 0.95 },
                  { agent: "Valta Prime", query: "Brand guidelines", results: 6, conf: 0.88 },
                  { agent: "Jenson", query: "Department budget requests", results: 8, conf: 0.92 },
                ].map((m, i) => (
                  <div key={i} className="glass-card px-3 py-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-[var(--axiom-text-primary)]">{m.agent}</span>
                      <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{m.results} results · {Math.round(m.conf * 100)}%</span>
                    </div>
                    <p className="text-[11px] text-[var(--axiom-text-secondary)] line-clamp-1 mt-0.5">"{m.query}"</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Decision Chains */}
          <div>
            <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)] mb-3">Decision Chains</h3>
            <div className="space-y-2">
              {[
                { agent: "Jenson", decision: "Increase sales headcount by 20% for Q3", confidence: 0.88, alts: 3 },
                { agent: "Valta Prime", decision: "Adopt minimalist brand direction with warm palette", confidence: 0.92, alts: 2 },
                { agent: "Jenson", decision: "Defer non-critical feature development to Q4", confidence: 0.85, alts: 2 },
                { agent: "Yamako", decision: "Block 2hr deep work slots daily for founder", confidence: 0.79, alts: 4 },
              ].map((d, i) => (
                <div key={i} className="glass-card px-4 py-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-[var(--axiom-text-primary)]">{d.agent}</span>
                      <span className="text-[10px] text-[var(--axiom-text-tertiary)]">decided</span>
                    </div>
                    <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{d.alts} alternatives</span>
                  </div>
                  <p className="text-sm text-[var(--axiom-text-primary)] mt-1">{d.decision}</p>
                  <div className="mt-1.5">
                    <ConfidenceBar value={d.confidence} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Provider Usage Sidebar */}
      <div className="w-[300px] flex-shrink-0 border-l border-[var(--axiom-border)] bg-[var(--axiom-bg-surface)] overflow-y-auto">
        <div className="px-4 py-3 border-b border-[var(--axiom-border)]">
          <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Provider Usage</h3>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">Today's consumption</p>
        </div>
        <div className="p-4 space-y-3">
          {providers.map((p) => (
            <button key={`${p.provider}-${p.model}`} onClick={() => setSelectedProvider(selectedProvider === `${p.provider}-${p.model}` ? null : `${p.provider}-${p.model}`)}
              className={`w-full text-left glass-card p-3 transition-colors ${selectedProvider === `${p.provider}-${p.model}` ? "ring-1 ring-[var(--axiom-accent)]" : "hover:bg-[var(--axiom-bg-elevated)]"}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-[var(--axiom-text-primary)]">{p.provider}</span>
                <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">${p.cost_estimate.toFixed(2)}</span>
              </div>
              <p className="text-[10px] text-[var(--axiom-text-tertiary)] mb-2">{p.model}</p>
              {/* Tokens bar */}
              <div className="mb-1.5">
                <div className="flex items-center justify-between text-[9px] text-[var(--axiom-text-tertiary)] mb-0.5">
                  <span>In: {(p.tokens_in / 1000).toFixed(0)}K</span>
                  <span>Out: {(p.tokens_out / 1000).toFixed(0)}K</span>
                </div>
                <div className="h-2 rounded-full bg-[var(--axiom-bg-elevated)] overflow-hidden flex">
                  <div className="h-full bg-blue-500/60 rounded-l-full" style={{ width: `${p.tokens_in / (p.tokens_in + p.tokens_out) * 100}%` }} />
                  <div className="h-full bg-green-500/60 rounded-r-full" style={{ width: `${p.tokens_out / (p.tokens_in + p.tokens_out) * 100}%` }} />
                </div>
              </div>
              <div className="flex items-center justify-between text-[9px] text-[var(--axiom-text-tertiary)]">
                <span>{p.requests} requests</span>
                <span>{p.avg_latency_ms}ms avg</span>
              </div>
            </button>
          ))}
          {/* Summary */}
          <div className="glass-card p-3 bg-[var(--axiom-accent-subtle)]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--axiom-text-primary)]">Total Today</span>
              <span className="text-[10px] text-[var(--axiom-text-tertiary)]">${MOCK_PROVIDERS.reduce((s, p) => s + p.cost_estimate, 0).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between mt-1 text-[10px] text-[var(--axiom-text-tertiary)]">
              <span>{(totalTokens / 1000).toFixed(0)}K tokens</span>
              <span>{totalRequests} requests</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}