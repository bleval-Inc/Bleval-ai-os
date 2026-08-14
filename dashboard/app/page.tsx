"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useAxiomStore } from "@/lib/store/axiom-store";
import { system, executives, learning, board } from "@/lib/api";
import type { RuntimeStatus, HealthSummary, ExecutiveBoardStatus, LearningStatus, WorkflowAnalytics } from "@/lib/api-types";
import DashboardConsole from "@/components/dashboard/DashboardConsole";

interface DashboardData {
  bleval: { clients: number; revenue: number; leads: number; pipeline: number; tasks: number; growth: number | null };
  valta: { marketStatus: string; activeMarkets: number; currentBias: string; opportunities: number; riskStatus: string; performance: number | null };
  personal: { todaysPriority: string; scheduleCount: number; activeGoals: number; tasks: number; learningProgress: number | null; projectsProgress: number | null };
  axiom: { systemStatus: string; activeExecutives: number; runningWorkflows: number; tasks: number; health: string; currentActivity: string };
}

export default function HomeDashboard() {
  const { setActiveWorkstation } = useAxiomStore();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [hoveredConsole, setHoveredConsole] = useState<string | null>(null);

  // Fetch real data on mount
  useEffect(() => {
    let cancelled = false;

    async function fetchDashboardData() {
      try {
        const [
          runtimeStatus,
          healthSummary,
          executiveBoard,
          learningStatus,
          workflowAnalytics,
          performanceScores,
          boardDashboard,
        ] = await Promise.allSettled([
          system.getRuntimeStatus(),
          system.health(),
          executives.boardStatus(),
          learning.status(),
          learning.workflowAnalytics(),
          learning.scores(),
          board.dashboard(),
        ]);

        if (cancelled) return;

        // BLEVAL data (from org stats)
        const orgCount = runtimeStatus.status === "fulfilled" ? runtimeStatus.value.org_count : 0;
        const workflowsDefined = runtimeStatus.status === "fulfilled" ? runtimeStatus.value.workflows_defined : 0;

        // VALTA data (from trading/executive intelligence)
        const marketStatus = "OPEN";
        const activeMarkets = 0;

        // AXIOM system data
        const activeExecutives = executiveBoard.status === "fulfilled"
          ? Object.values(executiveBoard.value).filter((e) => e.status === "running").length
          : 0;
        const runningWorkflows = 0;
        const systemHealth = healthSummary.status === "fulfilled"
          ? healthSummary.value.overall
          : "unknown";

        // Personal data
        const learningCycles = learningStatus.status === "fulfilled"
          ? learningStatus.value.total_learning_cycles
          : 0;
        const activePatterns = learningStatus.status === "fulfilled"
          ? learningStatus.value.active_patterns
          : 0;

        const dashboardData: DashboardData = {
          bleval: {
            clients: orgCount,
            revenue: 0,
            leads: workflowsDefined,
            pipeline: runtimeStatus.status === "fulfilled" ? runtimeStatus.value.workflows_defined : 0,
            tasks: 0,
            growth: null,
          },
          valta: {
            marketStatus,
            activeMarkets,
            currentBias: "NEUTRAL",
            opportunities: activePatterns,
            riskStatus: systemHealth.toUpperCase(),
            performance: null,
          },
          personal: {
            todaysPriority: "System Review",
            scheduleCount: 0,
            activeGoals: activePatterns,
            tasks: 0,
            learningProgress: learningCycles > 0 ? Math.min(100, learningCycles * 10) : null,
            projectsProgress: null,
          },
          axiom: {
            systemStatus: runtimeStatus.status === "fulfilled" && runtimeStatus.value.running ? "ONLINE" : "INITIALISING",
            activeExecutives,
            runningWorkflows,
            tasks: workflowAnalytics.status === "fulfilled"
              ? workflowAnalytics.value.reduce((sum, w) => sum + w.total_runs, 0)
              : 0,
            health: systemHealth,
            currentActivity: activeExecutives > 0 ? `${activeExecutives} executives running cycles` : "Awaiting their command",
          },
        };

        setData(dashboardData);
        setLoading(false);
      } catch {
        setLoading(false);
      }
    }

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const consoles = [
    {
      id: "bleval",
      title: "BLEVAL INC",
      subtitle: "Company Operations",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      ),
      metrics: data?.bleval
        ? [
            { label: "Active Clients", value: data.bleval.clients },
            { label: "Revenue", value: data.bleval.revenue > 0 ? `$${data.bleval.revenue.toLocaleString()}` : "—" },
            { label: "Leads", value: data.bleval.leads },
            { label: "Pipeline", value: data.bleval.pipeline },
            { label: "Tasks", value: data.bleval.tasks },
            { label: "Growth", value: data.bleval.growth !== null ? `${data.bleval.growth}%` : "—" },
          ]
        : [],
      accentColor: "from-indigo-400 to-violet-500",
      onClick: () => setActiveWorkstation("bleval"),
    },
    {
      id: "valta",
      title: "HOUSE OF VALTA",
      subtitle: "Markets & Strategy",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12V7H5V2H1v5H1" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      ),
      metrics: data?.valta
        ? [
            { label: "Market Status", value: data.valta.marketStatus },
            { label: "Active Markets", value: data.valta.activeMarkets },
            { label: "Current Bias", value: data.valta.currentBias },
            { label: "Opportunities", value: data.valta.opportunities },
            { label: "Risk Status", value: data.valta.riskStatus },
            { label: "Performance", value: data.valta.performance !== null ? `${data.valta.performance}%` : "—" },
          ]
        : [],
      accentColor: "from-amber-400 to-orange-500",
      onClick: () => setActiveWorkstation("valta"),
    },
    {
      id: "personal",
      title: "PERSONAL",
      subtitle: "Personal Operations",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      ),
      metrics: data?.personal
        ? [
            { label: "Today's Priority", value: data.personal.todaysPriority },
            { label: "Schedule", value: data.personal.scheduleCount },
            { label: "Active Goals", value: data.personal.activeGoals },
            { label: "Tasks", value: data.personal.tasks },
            { label: "Learning", value: data.personal.learningProgress !== null ? `${data.personal.learningProgress}%` : "—" },
            { label: "Projects", value: data.personal.projectsProgress !== null ? `${data.personal.projectsProgress}%` : "—" },
          ]
        : [],
      accentColor: "from-emerald-400 to-teal-500",
      onClick: () => setActiveWorkstation("personal"),
    },
    {
      id: "axiom",
      title: "AXIOM SYSTEM",
      subtitle: "Operating Status",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ),
      metrics: data?.axiom
        ? [
            { label: "System Status", value: data.axiom.systemStatus },
            { label: "Active Executives", value: data.axiom.activeExecutives },
            { label: "Running Workflows", value: data.axiom.runningWorkflows },
            { label: "Total Tasks", value: data.axiom.tasks },
            { label: "System Health", value: data.axiom.health.toUpperCase() },
            { label: "Current Activity", value: data.axiom.currentActivity },
          ]
        : [],
      accentColor: "from-indigo-400 via-violet-500 to-purple-600",
      onClick: () => setActiveWorkstation("axiom"),
    },
  ];

  const handleLogoClick = () => {
    // Open AI workstation in new window
    const url = typeof window !== "undefined" ? `${window.location.origin}/axiom` : "/axiom";
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[var(--axiom-bg-base)]">
      {/* Page content - full viewport centered layout */}
      <main className="flex-1 flex flex-col items-center justify-center p-8 md:p-12 lg:p-16 overflow-y-auto">
        <div className="w-full max-w-7xl flex flex-col items-center justify-center h-full">

          {/* Top row: BLEVAL (left) and VALTA (right) */}
          <div className="w-full flex justify-between gap-6 md:gap-8 mb-10 lg:mb-12">
            {/* BLEVAL Console - Top Left */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.08, ease: "easeOut" }}
              className="flex-1 max-w-[calc(50%-1.5rem)]"
            >
              <DashboardConsole
                {...consoles[0]}
                isHovered={hoveredConsole === consoles[0].id}
                onHover={(hovered) => setHoveredConsole(hovered ? consoles[0].id : null)}
                loading={loading}
              />
            </motion.div>

            {/* VALTA Console - Top Right */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.16, ease: "easeOut" }}
              className="flex-1 max-w-[calc(50%-1.5rem)]"
            >
              <DashboardConsole
                {...consoles[1]}
                isHovered={hoveredConsole === consoles[1].id}
                onHover={(hovered) => setHoveredConsole(hovered ? consoles[1].id : null)}
                loading={loading}
              />
            </motion.div>
          </div>

          {/* Center: AXIOM Logo - Clickable, opens AI workstation in new window */}
          <motion.button
            onClick={handleLogoClick}
            className="relative w-36 h-36 md:w-44 md:h-44 lg:w-52 lg:h-52 rounded-2xl flex items-center justify-center cursor-pointer group"
            style={{
              background: "linear-gradient(135deg, var(--axiom-bg-elevated) 0%, var(--axiom-bg-surface) 100%)",
              border: "1px solid var(--axiom-border)",
              boxShadow: "0 0 60px -10px rgba(99, 102, 241, 0.35), inset 0 1px 0 rgba(255,255,255,0.05)"
            }}
            animate={{
              boxShadow: [
                "0 0 60px -10px rgba(99, 102, 241, 0.35), inset 0 1px 0 rgba(255,255,255,0.05)",
                "0 0 80px -5px rgba(99, 102, 241, 0.55), inset 0 1px 0 rgba(255,255,255,0.05)",
                "0 0 60px -10px rgba(99, 102, 241, 0.35), inset 0 1px 0 rgba(255,255,255,0.05)"
              ]
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            aria-label="Open AXIOM AI Workstation"
          >
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)] group-hover:stroke-[var(--axiom-accent-secondary)] transition-colors duration-300">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>

            {/* Subtle ambient glow ring */}
            <motion.div
              className="absolute inset-0 rounded-2xl"
              style={{
                border: "1px solid rgba(99, 102, 241, 0.3)",
                boxShadow: "inset 0 0 30px rgba(99, 102, 241, 0.1)"
              }}
              animate={{
                opacity: [0.3, 0.7, 0.3],
                scale: [1, 1.03, 1]
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* New window indicator - subtle */}
            <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 hidden md:block">
              <motion.div
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--axiom-bg-elevated)]/80 backdrop-blur-sm border border-[var(--axiom-border)]/40 text-[10px] font-mono text-[var(--axiom-text-tertiary)] uppercase tracking-wider opacity-0"
                animate={{ opacity: 0.6 }}
                transition={{ delay: 1.5, duration: 0.5 }}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
                <span>New Window</span>
              </motion.div>
            </div>
          </motion.button>

          {/* Bottom row: PERSONAL (left) and AXIOM SYSTEM (right) */}
          <div className="w-full flex justify-between gap-6 md:gap-8 mt-10 lg:mt-12">
            {/* PERSONAL Console - Bottom Left */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.24, ease: "easeOut" }}
              className="flex-1 max-w-[calc(50%-1.5rem)]"
            >
              <DashboardConsole
                {...consoles[2]}
                isHovered={hoveredConsole === consoles[2].id}
                onHover={(hovered) => setHoveredConsole(hovered ? consoles[2].id : null)}
                loading={loading}
              />
            </motion.div>

            {/* AXIOM SYSTEM Console - Bottom Right */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.32, ease: "easeOut" }}
              className="flex-1 max-w-[calc(50%-1.5rem)]"
            >
              <DashboardConsole
                {...consoles[3]}
                isHovered={hoveredConsole === consoles[3].id}
                onHover={(hovered) => setHoveredConsole(hovered ? consoles[3].id : null)}
                loading={loading}
              />
            </motion.div>
          </div>

        </div>
      </main>
    </div>
  );
}