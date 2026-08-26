"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system, executives as execApi, approvals as approvalsApi, learning } from "../../../lib/api";
import { CommandCenterSkeleton } from "../Skeletons";
import { ErrorState } from "../States";
import CommandCenterBriefing from "./CommandCenterBriefing";
import CommandCenterExecutives from "./CommandCenterExecutives";
import CommandCenterApprovals from "./CommandCenterApprovals";
import CommandCenterHealth from "./CommandCenterHealth";
import CommandCenterLearning from "./CommandCenterLearning";
import CommandCenterActions from "./CommandCenterActions";
import type { HealthSummary, ExecutiveBoardStatus, Approval, LearningRecommendation, LearningPattern, KnowledgeEntry } from "../../../lib/api-types";

/* Staggered entry animation */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
};

/* Main Component */

export default function CommandCenter() {
  const { setRuntime, setHealth, setExecutiveBoard } = useAxiomStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [version, setVersion] = useState("—");
  const [orgCount, setOrgCount] = useState(0);
  const [executiveCount, setExecutiveCount] = useState(0);
  const [workflowCount, setWorkflowCount] = useState(0);
  const [health, setLocalHealth] = useState<HealthSummary | null>(null);
  const [execBoard, setLocalExecBoard] = useState<ExecutiveBoardStatus | null>(null);
  const [approvals, setApprovals] = useState<{ id: string; approval_id: string; workflow_id: string; step_name: string; requested_by: string; requested_at: string }[]>([]);
  const [recommendations, setRecommendations] = useState<{ id: string; title: string; confidence: number; expected_impact: string }[]>([]);
  const [patterns, setPatterns] = useState<{ id: string; title: string; severity: string; frequency: number }[]>([]);
  const [knowledge, setKnowledge] = useState<{ id: string; title: string }[]>([]);
  const [approvalsError, setApprovalsError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, h, eb, app, recs, pats, know] = await Promise.all([
        system.status().catch(() => null),
        system.health().catch(() => null),
        execApi.boardStatus().catch(() => null),
        approvalsApi.list("pending").catch(() => [] as Approval[]),
        learning.recommendations().catch(() => [] as LearningRecommendation[]),
        learning.patterns().catch(() => [] as LearningPattern[]),
        learning.knowledge().catch(() => [] as KnowledgeEntry[]),
      ]);

      if (s) { setRuntime(s); setVersion(s.version); setOrgCount(s.org_count ?? 0); setExecutiveCount(s.executives ?? 0); setWorkflowCount(s.workflows_defined ?? 0); }
      if (h) { setHealth(h); setLocalHealth(h); }
      if (eb) { setExecutiveBoard(eb); setLocalExecBoard(eb); }
      if (Array.isArray(app)) setApprovals(app.map((a: Approval) => ({
        id: `app-${a.approval_id}`,
        approval_id: a.approval_id,
        workflow_id: a.workflow_id,
        step_name: a.step_name,
        requested_by: a.requested_by,
        requested_at: a.requested_at,
      })));
      if (Array.isArray(recs)) setRecommendations(recs.map((r: LearningRecommendation) => ({
        id: r.recommendation_id, title: r.title, confidence: r.confidence, expected_impact: r.expected_impact,
      })));
      if (Array.isArray(pats)) setPatterns(pats.map((p: LearningPattern) => ({
        id: p.pattern_id, title: p.title, severity: p.severity, frequency: p.frequency,
      })));
      if (Array.isArray(know)) setKnowledge(know.map((k: KnowledgeEntry) => ({
        id: k.entry_id, title: k.title,
      })));
      setApprovalsError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, [setRuntime, setHealth, setExecutiveBoard]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const navigate = useCallback((view: string) => {
    const { setActiveView } = useAxiomStore.getState();
    setActiveView(view as Parameters<typeof setActiveView>[0]);
  }, []);

  const handleApprove = useCallback(async (id: string) => {
    try {
      await approvalsApi.respond(id, { approval_id: id, approved: true, approved_by: "Founder", notes: "" });
      setApprovals((prev) => prev.filter((a) => a.approval_id !== id));
    } catch {
      setApprovalsError("Failed to approve");
    }
  }, []);

  const handleReject = useCallback(async (id: string) => {
    try {
      await approvalsApi.respond(id, { approval_id: id, approved: false, approved_by: "Founder", notes: "" });
      setApprovals((prev) => prev.filter((a) => a.approval_id !== id));
    } catch {
      setApprovalsError("Failed to reject");
    }
  }, []);

  /* Loading state */
  if (loading && !health && !execBoard) {
    return (
      <div className="flex-1 overflow-y-auto">
        <CommandCenterSkeleton />
      </div>
    );
  }

  /* Error state (no data at all) */
  if (error && !health && !execBoard) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <ErrorState message={error} onRetry={fetchAll} />
      </div>
    );
  }

  const hOverall: "healthy" | "unhealthy" = health?.overall ?? "healthy";

  return (
    <div className="flex-1 overflow-y-auto">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-6 max-w-5xl mx-auto"
      >
        {/* Row 1: Briefing (full width) */}
        <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} className="lg:col-span-2">
          <CommandCenterBriefing
            version={version}
            orgCount={orgCount}
            executiveCount={executiveCount}
            workflowCount={workflowCount}
            healthOverall={hOverall}
            onNavigate={navigate}
          />
        </motion.div>

        {/* Row 2: Executives + Health */}
        <CommandCenterExecutives board={execBoard} loading={loading} error={null} onNavigate={() => navigate("executives")} />
        <CommandCenterHealth health={health} loading={loading} error={null} onNavigate={() => navigate("operations")} />

        {/* Row 3: Approvals + Learning */}
        <CommandCenterApprovals
          approvals={approvals}
          loading={loading}
          error={approvalsError}
          onNavigate={() => navigate("console")}
          onApprove={handleApprove}
          onReject={handleReject}
        />
        <CommandCenterLearning
          recommendations={recommendations}
          patterns={patterns}
          knowledge={knowledge}
          loading={loading}
          error={null}
          onNavigate={() => navigate("knowledge")}
        />

        {/* Row 4: Actions (full width) */}
        <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} className="lg:col-span-2">
          <CommandCenterActions
            approvalCount={approvals.length}
            recommendations={recommendations}
            health={health}
            knowledgeCount={knowledge.length}
            loading={loading}
            onNavigate={navigate}
          />
        </motion.div>
      </motion.div>
    </div>
  );
}