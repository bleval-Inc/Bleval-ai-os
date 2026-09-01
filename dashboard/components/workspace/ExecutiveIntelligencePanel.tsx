"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { executiveIntelligence, learning } from "../../lib/api";

type ExecutiveId = "jenson" | "valta_prime" | "yamako";

interface ExecutiveIntelligenceData {
  exec_id: string;
  patterns: Array<{
    pattern_id: string;
    title: string;
    severity: string;
    frequency: number;
    impact_score: number;
    pattern_type: string;
  }>;
  recommendations: Array<{
    recommendation_id: string;
    title: string;
    priority: string;
    confidence: number;
    status: string;
  }>;
  knowledge_count: number;
  workflow_insights: Array<{
    workflow_id: string;
    success_rate: number;
    avg_duration: number;
    recommendation: string;
  }>;
}

interface DecisionSupportData {
  workflow_id: string;
  priority: string;
  analysis: {
    risk_factors: string[];
    success_probability: number;
    recommended_approach: string;
    resource_estimate: string;
  };
  similar_workflows: Array<{
    workflow_id: string;
    outcome: "success" | "failed" | "partial";
    similarity: number;
  }>;
  learning_patterns: Array<{
    pattern_id: string;
    title: string;
    relevance: number;
  }>;
}

interface ExecutiveBranding {
  name: string;
  shortName: string;
  colorFrom: string;
  colorTo: string;
  org: string;
  icon: React.ReactNode;
}

const EXECUTIVE_BRANDING: Record<ExecutiveId, ExecutiveBranding> = {
  jenson: {
    name: "BLEVAL INC",
    shortName: "Jenson",
    colorFrom: "sky-400",
    colorTo: "blue-600",
    org: "Bleval Inc",
    icon: <span className="text-[7px] font-bold text-white">B</span>,
  },
  valta_prime: {
    name: "HOUSE OF VALTA",
    shortName: "Valta Prime",
    colorFrom: "amber-400",
    colorTo: "amber-600",
    org: "House of Valta",
    icon: <span className="text-[7px] font-bold text-white">V</span>,
  },
  yamako: {
    name: "PERSONAL OPS",
    shortName: "Yamako",
    colorFrom: "violet-400",
    colorTo: "purple-600",
    org: "Personal Operations",
    icon: <span className="text-[7px] font-bold text-white">P</span>,
  },
};

const severityColors: Record<string, string> = {
  info: "bg-blue-400/10 text-blue-400",
  warning: "bg-amber-400/10 text-amber-400",
  critical: "bg-red-400/10 text-red-400",
};

const priorityColors: Record<string, string> = {
  high: "bg-red-400/10 text-red-400",
  medium: "bg-amber-400/10 text-amber-400",
  low: "bg-emerald-400/10 text-emerald-400",
};

const statusColors: Record<string, string> = {
  pending: "text-amber-400",
  approved: "text-emerald-400",
  implemented: "text-blue-400",
  rejected: "text-red-400",
};

export default function ExecutiveIntelligencePanel() {
  const { selectedExecutive, activeWorkstationView } = useAxiomStore();
  const [isLoading, setIsLoading] = useState(true);
  const [intelligence, setIntelligence] = useState<ExecutiveIntelligenceData | null>(null);
  const [decisionSupport, setDecisionSupport] = useState<DecisionSupportData | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "patterns" | "recommendations" | "workflows" | "decisions">("overview");

  const execId = selectedExecutive as ExecutiveId | null;
  const branding = execId ? EXECUTIVE_BRANDING[execId] : null;

  const handleRunLearningCycle = async () => {
    if (!execId) return;
    try {
      await executiveIntelligence.runLearningCycle(execId);
      // Refresh intelligence data
      const data = await executiveIntelligence.get(execId);
      setIntelligence(data as unknown as ExecutiveIntelligenceData);
    } catch (error) {
      console.warn(`Failed to run learning cycle for ${execId}:`, error);
    }
  };

  // Load intelligence data on executive change
  useEffect(() => {
    if (!execId) {
      setIntelligence(null);
      setDecisionSupport(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    const loadData = async () => {
      try {
        const data = await executiveIntelligence.get(execId);
        setIntelligence(data as unknown as ExecutiveIntelligenceData);
      } catch (error) {
        console.warn(`Failed to load intelligence for ${execId}:`, error);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [execId]);

  if (!branding || !intelligence) {
    return (
      <div className="flex-1 p-6">
        <div className="glass-panel p-8 rounded-2xl text-center">
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-${branding?.colorFrom || "gray-400"} to-${branding?.colorTo || "gray-600"} flex items-center justify-center mx-auto mb-4`}>
            {branding?.icon}
          </div>
          <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)] mb-2">
            {branding?.shortName || "Executive"} Intelligence
          </h3>
          <p className="text-xs text-[var(--axiom-text-tertiary)]">
            Select an executive workstation to view intelligence insights
          </p>
        </div>
      </div>
    );
  }


  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br from-${branding.colorFrom} to-${branding.colorTo} flex items-center justify-center`}>
            {branding.icon}
          </div>
          <div>
            <p className="text-[10px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wider">
              {branding.org}
            </p>
            <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)]">
              {branding.shortName} Intelligence
            </h3>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1">
          {[
            { id: "overview", label: "Overview" },
            { id: "patterns", label: "Patterns" },
            { id: "recommendations", label: "Recommendations" },
            { id: "workflows", label: "Workflows" },
            { id: "decisions", label: "Decisions" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-3 py-1.5 text-[11px] font-medium rounded-md transition-all duration-150 ${
                activeTab === tab.id
                  ? "text-[var(--axiom-accent)] bg-[var(--axiom-accent-subtle)]"
                  : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)]"
              }`}
            >
              {tab.label}
              {tab.id === "patterns" && intelligence.patterns.length > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 text-[9px] font-semibold rounded-full bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]">
                  {intelligence.patterns.length}
                </span>
              )}
              {tab.id === "recommendations" && intelligence.recommendations.length > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 text-[9px] font-semibold rounded-full bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]">
                  {intelligence.recommendations.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && (
          <div className="flex items-center justify-center h-32">
            <div className="w-6 h-6 border-2 border-[var(--axiom-accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!isLoading && activeTab === "overview" && (
          <div className="space-y-4">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                label="Patterns"
                value={intelligence.patterns.length}
                icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>}
                color={branding.colorFrom}
              />
              <StatCard
                label="Recommendations"
                value={intelligence.recommendations.length}
                icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6"/><path d="M18 18l-6-6 6-6"/></svg>}
                color={branding.colorTo}
              />
              <StatCard
                label="Knowledge"
                value={intelligence.knowledge_count}
                icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>}
                color="emerald-400"
              />
              <StatCard
                label="Workflows"
                value={intelligence.workflow_insights.length}
                icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M8 21h8M12 17v4"/></svg>}
                color="violet-400"
              />
            </div>

            {/* Quick Actions */}
            <div className="glass-panel p-4 rounded-xl">
              <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wider mb-3">Actions</h4>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={handleRunLearningCycle}
                  disabled={isLoading}
                  className="px-3 py-1.5 text-[11px] font-medium rounded-lg bg-[var(--axiom-accent)] text-white hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  Run Learning Cycle
                </button>
                <button className="px-3 py-1.5 text-[11px] font-medium rounded-lg bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-border)] transition-colors">
                  View All Patterns
                </button>
                <button className="px-3 py-1.5 text-[11px] font-medium rounded-lg bg-[var(--axiom-bg-elevated)] text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-border)] transition-colors">
                  View Recommendations
                </button>
              </div>
            </div>

            {/* Top Patterns */}
            {intelligence.patterns.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wider mb-2">Top Patterns</h4>
                <div className="space-y-2">
                  {intelligence.patterns.slice(0, 3).map((pattern) => (
                    <PatternCard key={pattern.pattern_id} pattern={pattern} />
                  ))}
                </div>
              </div>
            )}

            {/* Top Recommendations */}
            {intelligence.recommendations.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wider mb-2">Top Recommendations</h4>
                <div className="space-y-2">
                  {intelligence.recommendations.slice(0, 3).map((rec) => (
                    <RecommendationCard key={rec.recommendation_id} recommendation={rec} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!isLoading && activeTab === "patterns" && (
          <div className="space-y-2">
            {intelligence.patterns.length === 0 ? (
              <EmptyState message="No patterns detected yet. Run a learning cycle to discover patterns." />
            ) : (
              intelligence.patterns.map((pattern) => (
                <PatternCard key={pattern.pattern_id} pattern={pattern} />
              ))
            )}
          </div>
        )}

        {!isLoading && activeTab === "recommendations" && (
          <div className="space-y-2">
            {intelligence.recommendations.length === 0 ? (
              <EmptyState message="No recommendations generated yet." />
            ) : (
              intelligence.recommendations.map((rec) => (
                <RecommendationCard key={rec.recommendation_id} recommendation={rec} />
              ))
            )}
          </div>
        )}

        {!isLoading && activeTab === "workflows" && (
          <div className="space-y-2">
            {intelligence.workflow_insights.length === 0 ? (
              <EmptyState message="No workflow insights available." />
            ) : (
              intelligence.workflow_insights.map((wf) => (
                <WorkflowInsightCard key={wf.workflow_id} insight={wf} />
              ))
            )}
          </div>
        )}

        {!isLoading && activeTab === "decisions" && (
          <div className="space-y-4">
            {decisionSupport ? (
              <DecisionSupportCard support={decisionSupport} />
            ) : (
              <EmptyState
                message="Select a workflow from the Operations or Projects view to see decision support analysis."
                action={{
                  label: "View Workflows",
                  onClick: () => setActiveTab("workflows"),
                }}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------
// Sub-components

function StatCard({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color: string }) {
  return (
    <div className="glass-panel p-4 rounded-xl">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-semibold text-[var(--axiom-text-primary)] tabular-nums">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br from-${color} to-${color}/60 flex items-center justify-center text-white`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function PatternCard({ pattern }: { pattern: ExecutiveIntelligenceData["patterns"][0] }) {
  const severityClass = severityColors[pattern.severity] || severityColors.info;
  return (
    <div className="glass-panel p-3 rounded-lg border border-[var(--axiom-border)]">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-1.5 py-0.5 text-[9px] font-medium rounded ${severityClass}`}>
              {pattern.pattern_type}
            </span>
            <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{pattern.frequency} occurrences</span>
          </div>
          <p className="text-sm text-[var(--axiom-text-secondary)] truncate">{pattern.title}</p>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 h-1.5 bg-[var(--axiom-bg-elevated)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--axiom-accent)] rounded-full"
                style={{ width: `${Math.min(100, pattern.impact_score * 100)}%` }}
              />
            </div>
            <span className="text-[10px] text-[var(--axiom-text-tertiary)] font-mono tabular-nums">
              {(pattern.impact_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function RecommendationCard({ recommendation }: { recommendation: ExecutiveIntelligenceData["recommendations"][0] }) {
  const priorityClass = priorityColors[recommendation.priority] || priorityColors.medium;
  const statusClass = statusColors[recommendation.status] || statusColors.pending;
  return (
    <div className="glass-panel p-3 rounded-lg border border-[var(--axiom-border)]">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-1.5 py-0.5 text-[9px] font-medium rounded ${priorityClass}`}>
              {recommendation.priority}
            </span>
            <span className={`text-[10px] font-medium ${statusClass}`}>{recommendation.status}</span>
          </div>
          <p className="text-sm text-[var(--axiom-text-secondary)] truncate">{recommendation.title}</p>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-1">Confidence: {(recommendation.confidence * 100).toFixed(0)}%</p>
        </div>
      </div>
    </div>
  );
}

function WorkflowInsightCard({ insight }: { insight: ExecutiveIntelligenceData["workflow_insights"][0] }) {
  const successColor = insight.success_rate >= 0.8 ? "emerald-400" : insight.success_rate >= 0.5 ? "amber-400" : "red-400";
  return (
    <div className="glass-panel p-4 rounded-xl">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--axiom-text-primary)] truncate">{insight.workflow_id}</p>
          <p className="text-[11px] text-[var(--axiom-text-tertiary)] mt-1">{insight.recommendation}</p>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <div className="flex items-center gap-1">
            <span className={`text-[11px] font-semibold ${successColor}`}>{(insight.success_rate * 100).toFixed(0)}%</span>
            <span className="text-[10px] text-[var(--axiom-text-tertiary)]">success</span>
          </div>
          <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{insight.avg_duration.toFixed(1)}min avg</span>
        </div>
      </div>
    </div>
  );
}

function DecisionSupportCard({ support }: { support: DecisionSupportData }) {
  return (
    <div className="space-y-4">
      <div className="glass-panel p-4 rounded-xl border border-[var(--axiom-border)]">
        <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wider mb-3">
          Workflow Analysis: {support.workflow_id}
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider mb-1">Success Probability</p>
            <p className="text-2xl font-semibold text-[var(--axiom-text-primary)]">
              {(support.analysis.success_probability * 100).toFixed(0)}%
            </p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--axiom-text-tertiary)] uppercase tracking-wider mb-1">Resource Estimate</p>
            <p className="text-sm font-medium text-[var(--axiom-text-secondary)]">{support.analysis.resource_estimate}</p>
          </div>
        </div>
      </div>

      {support.analysis.risk_factors.length > 0 && (
        <div className="glass-panel p-4 rounded-xl">
          <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">Risk Factors</h4>
          <ul className="space-y-1">
            {support.analysis.risk_factors.map((risk, i) => (
              <li key={i} className="text-sm text-[var(--axiom-text-secondary)] flex items-center gap-2">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-400 flex-shrink-0">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                {risk}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="glass-panel p-4 rounded-xl">
        <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wider mb-2">
          Recommended Approach
        </h4>
        <p className="text-sm text-[var(--axiom-text-secondary)]">{support.analysis.recommended_approach}</p>
      </div>

      {support.similar_workflows.length > 0 && (
        <div className="glass-panel p-4 rounded-xl">
          <h4 className="text-xs font-semibold text-[var(--axiom-text-primary)] uppercase tracking-wider mb-2">
            Similar Workflows
          </h4>
          <div className="space-y-2">
            {support.similar_workflows.map((wf) => (
              <div key={wf.workflow_id} className="flex items-center justify-between text-sm">
                <span className="text-[var(--axiom-text-secondary)]">{wf.workflow_id}</span>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-1.5 py-0.5 text-[9px] font-medium rounded ${
                      wf.outcome === "success"
                        ? "text-emerald-400 bg-emerald-400/10"
                        : wf.outcome === "failed"
                        ? "text-red-400 bg-red-400/10"
                        : "text-amber-400 bg-amber-400/10"
                    }`}
                  >
                    {wf.outcome}
                  </span>
                  <span className="text-[10px] text-[var(--axiom-text-tertiary)]">
                    {(wf.similarity * 100).toFixed(0)}% similar
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState({ message, action }: { message: string; action?: { label: string; onClick: () => void } }) {
  return (
    <div className="glass-panel p-8 rounded-2xl text-center">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 text-[var(--axiom-text-tertiary)]">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4M12 8h.01" />
      </svg>
      <p className="text-sm text-[var(--axiom-text-tertiary)] mb-4">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-3 py-1.5 text-[11px] font-medium rounded-lg bg-[var(--axiom-accent)] text-white hover:opacity-90 transition-opacity"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}