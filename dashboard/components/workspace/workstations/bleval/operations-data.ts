// OPERATIONS — placeholder automation/workflow data.
// Later supplied by the dedicated BLEVAL operations/agent database.

import type { MetricKpi, FlowStage, StatusTone } from "./types";

export const operationsKpis: MetricKpi[] = [
  { key: "workflows", label: "Active Workflows", value: "6", delta: "2 starting", series: [3, 4, 4, 5, 5, 5, 6, 6] },
  { key: "agents", label: "Running Agents", value: "5", delta: "1 standby", series: [4, 4, 5, 5, 5, 5, 5, 5] },
  { key: "projects", label: "Active Projects", value: "9", delta: "2 near due", series: [6, 7, 7, 8, 8, 9, 9, 9] },
  { key: "tasks", label: "Tasks Completed", value: "128", delta: "+31 today", series: [74, 84, 90, 98, 108, 114, 123, 128] },
];

export interface WorkflowRecord {
  id: string;
  name: string;
  status: StatusTone;
  stage: string;
  tasks: number;
  progress: number;
}

export const workflows: WorkflowRecord[] = [
  { id: "w1", name: "Acquisition Workflow", status: "healthy", stage: "Qualifying leads", tasks: 14, progress: 62 },
  { id: "w2", name: "Research Workflow", status: "active", stage: "Fetching sources", tasks: 9, progress: 45 },
  { id: "w3", name: "Content Workflow", status: "active", stage: "QC review", tasks: 12, progress: 58 },
  { id: "w4", name: "Client Onboarding", status: "healthy", stage: "Scheduling kickoff", tasks: 6, progress: 30 },
  { id: "w5", name: "Delivery Workflow", status: "warning", stage: "Vertex build review", tasks: 18, progress: 71 },
  { id: "w6", name: "Follow-up Workflow", status: "neutral", stage: "On hold", tasks: 3, progress: 12 },
];

export interface AgentRecord {
  id: string;
  name: string;
  state: "ACTIVE" | "WORKING" | "STANDBY";
  task: string;
}

export const agents: AgentRecord[] = [
  { id: "g1", name: "Research Agent", state: "ACTIVE", task: "Solar campaign sources" },
  { id: "g2", name: "Lead Discovery", state: "ACTIVE", task: "Niche lead enrichment" },
  { id: "g3", name: "Qualification Agent", state: "ACTIVE", task: "Scoring 41 leads" },
  { id: "g4", name: "Content Agent", state: "WORKING", task: "Script batch #12" },
  { id: "g5", name: "QC Agent", state: "STANDBY", task: "Awaiting review queue" },
  { id: "g6", name: "CRM Agent", state: "ACTIVE", task: "Syncing client records" },
];

export const productionPipeline: FlowStage[] = [
  { id: "research", label: "Research" },
  { id: "strategy", label: "Strategy" },
  { id: "acquisition", label: "Acquisition" },
  { id: "sales", label: "Sales" },
  { id: "onboarding", label: "Onboarding" },
  { id: "delivery", label: "Delivery" },
  { id: "retention", label: "Retention" },
];

export interface ActivityEvent {
  id: string;
  text: string;
  time: string;
}

export const activityEvents: ActivityEvent[] = [
  { id: "e1", text: "Research workflow completed — Solar campaign", time: "09:12" },
  { id: "e2", text: "14 prospects discovered via Lead Discovery", time: "09:04" },
  { id: "e3", text: "6 leads qualified to Qualified stage", time: "08:47" },
  { id: "e4", text: "Content batch #12 entered QC", time: "08:31" },
  { id: "e5", text: "Client onboarding workflow started — Fernwood", time: "08:12" },
];