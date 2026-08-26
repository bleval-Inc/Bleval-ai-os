// CLIENTS — placeholder client/portfolio data.
// Later supplied by the dedicated BLEVAL client database / CRM.

import type { MetricKpi, FlowStage, StatusTone } from "./types";

export const clientsKpis: MetricKpi[] = [
  { key: "active", label: "Active Clients", value: "14", delta: "+3", series: [9, 10, 10, 11, 12, 12, 13, 14] },
  { key: "new", label: "New Clients", value: "3", delta: "this month", series: [1, 1, 1, 2, 2, 2, 3, 3] },
  { key: "projects", label: "Projects", value: "9", delta: "2 in build", series: [6, 6, 7, 7, 7, 8, 9, 9] },
  { key: "retainers", label: "Retainers", value: "7", delta: "R74k / mo", series: [6, 6, 6, 7, 7, 7, 7, 7] },
];

export const clientPipeline: FlowStage[] = [
  { id: "prospect", label: "Prospect" },
  { id: "qualified", label: "Qualified" },
  { id: "salescall", label: "Sales Call" },
  { id: "closed", label: "Closed" },
  { id: "onboarding", label: "Onboarding" },
  { id: "active", label: "Active" },
  { id: "retained", label: "Retained" },
];

export interface ClientRecord {
  id: string;
  business: string;
  industry: string;
  status: string;
  project: string;
  revenue: string;
  retainer: string;
  health: StatusTone;
}

export const clientList: ClientRecord[] = [
  { id: "cl1", business: "Nova Dynamics", industry: "Tech", status: "Active", project: "Platform retainer", revenue: "R8,200/mo", retainer: "Yes", health: "healthy" },
  { id: "cl2", business: "Vertex Labs", industry: "SaaS", status: "Build", project: "Product build", revenue: "R12,500/mo", retainer: "Yes", health: "healthy" },
  { id: "cl3", business: "Orbit Health", industry: "Healthcare", status: "Active", project: "Consulting", revenue: "R5,400/mo", retainer: "No", health: "warning" },
  { id: "cl4", business: "Helios Capital", industry: "Finance", status: "Active", project: "Retainer + commission", revenue: "R9,800/mo", retainer: "Yes", health: "healthy" },
  { id: "cl5", business: "Fernwood Capital", industry: "Property", status: "Onboarding", project: "Brand build", revenue: "R12,500/mo", retainer: "No", health: "active" },
  { id: "cl6", business: "Listenatix", industry: "SaaS", status: "At Risk", project: "Content retainer", revenue: "R6,200/mo", retainer: "Yes", health: "danger" },
];

export interface ActiveProject {
  id: string;
  client: string;
  project: string;
  progress: number;
  stage: string;
  deadline: string;
  workflow: string;
}

export const activeProjects: ActiveProject[] = [
  { id: "p1", client: "Vertex Labs", project: "Product build", progress: 68, stage: "Development", deadline: "Sep 12", workflow: "Delivery-011" },
  { id: "p2", client: "Nova Dynamics", project: "Q3 campaign", progress: 42, stage: "Production", deadline: "Sep 05", workflow: "Content-022" },
  { id: "p3", client: "Helios Capital", project: "Brand refresh", progress: 81, stage: "QC", deadline: "Aug 28", workflow: "Brand-006" },
  { id: "p4", client: "Fernwood Capital", project: "Onboarding", progress: 22, stage: "Onboarding", deadline: "Sep 02", workflow: "Onboard-014" },
];

export interface HealthItem {
  id: string;
  client: string;
  label: string;
  tone: StatusTone;
  detail: string;
}

export const clientHealth: HealthItem[] = [
  { id: "h1", client: "Listenatix", label: "At Risk", tone: "danger", detail: "Deliverable slippage — 2 missed check-ins" },
  { id: "h2", client: "Orbit Health", label: "Attention", tone: "warning", detail: "Reduced this month; may downsize retainer" },
  { id: "h3", client: "Nova Dynamics", label: "Healthy", tone: "healthy", detail: "Expansion conversation scheduled" },
];