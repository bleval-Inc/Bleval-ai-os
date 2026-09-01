"use client";

import { motion } from "framer-motion";

/* Stat tile */

interface BriefingStatProps {
  label: string;
  value: string | number;
  icon: string;
  color?: string;
  onClick?: () => void;
}

function BriefingStat({ label, value, icon, color = "var(--axiom-text-secondary)", onClick }: BriefingStatProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="glass-card p-3 text-left"
    >
      {/* icon */}
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" className="mb-2">
        {icon === "orgs" ? <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /></> :
         icon === "execs" ? <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></> :
         icon === "workflows" ? <><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></> :
         <><circle cx="12" cy="12" r="10" /><path d="M12 8v4" /><path d="M12 16h0" /></>}
      </svg>
      <p className="text-[22px] font-semibold text-[var(--axiom-text-primary)] tabular-nums">{value}</p>
      <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5">{label}</p>
    </motion.button>
  );
}

/* Briefing card */

interface CommandCenterBriefingProps {
  version: string;
  orgCount: number;
  executiveCount: number;
  workflowCount: number;
  healthOverall: "healthy" | "unhealthy";
  onNavigate: (view: string) => void;
}

export default function CommandCenterBriefing({
  version,
  orgCount,
  executiveCount,
  workflowCount,
  healthOverall,
  onNavigate,
}: CommandCenterBriefingProps) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Morning" : hour < 17 ? "Afternoon" : "Evening";
  const dateStr = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="glass-panel p-5 flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-gradient">
          Good {greeting}, Founder
        </h1>
        <p className="text-xs text-[var(--axiom-text-tertiary)] mt-0.5">{dateStr}</p>
        <span className="text-[9px] text-[var(--axiom-text-tertiary)] font-mono">v{version}</span>
      </div>
      <div className="grid grid-cols-4 gap-3">
        <BriefingStat label="Organisations" value={orgCount} icon="orgs" onClick={() => onNavigate("console")} />
        <BriefingStat label="Executives" value={executiveCount} icon="execs" onClick={() => onNavigate("executives")} />
        <BriefingStat label="Workflows" value={workflowCount} icon="workflows" onClick={() => onNavigate("operations")} />
        <BriefingStat
          label="Health"
          value={healthOverall === "healthy" ? "All Good" : "Issues"}
          icon="health"
          color={healthOverall === "healthy" ? "var(--axiom-success)" : "var(--axiom-error)"}
          onClick={() => onNavigate("operations")}
        />
      </div>
    </div>
  );
}