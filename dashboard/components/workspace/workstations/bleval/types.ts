// Shared types for the BLEVAL INC workstation.

export type BaseIcon =
  | "dashboard"
  | "jenson"
  | "truth"
  | "acquisition"
  | "content"
  | "clients"
  | "operations";

// Operational / status tone — kept neutral so any future DB status maps cleanly.
export type StatusTone = "healthy" | "active" | "warning" | "danger" | "neutral";

export interface MetricKpi {
  key: string;
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down";
  series?: number[];
}

export interface FlowStage {
  id: string;
  label: string;
}

// Brand gradient used across the BLEVAL workstation (matches AXIOM Home console).
export const BLEVAL_GRADIENT = "linear-gradient(135deg, #6d7cff 0%, #a88cff 100%)";
export const BLEVAL_ACCENT = "#6d7cff";
export const BLEVAL_VIOLET = "#a88cff";
export const BLEVAL_CYAN = "#00d4ff";