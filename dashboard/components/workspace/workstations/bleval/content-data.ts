// CONTENT — placeholder content-production data.
// Later supplied by the dedicated BLEVAL content database.

import type { MetricKpi, FlowStage, StatusTone } from "./types";

export const contentKpis: MetricKpi[] = [
  { key: "produced", label: "Content Produced", value: "48", delta: "+12 wk", series: [20, 24, 28, 30, 35, 40, 44, 48] },
  { key: "production", label: "In Production", value: "12", delta: "5 reels", series: [8, 9, 10, 9, 11, 10, 12, 12] },
  { key: "qc", label: "Awaiting QC", value: "8", delta: "2 failed", series: [6, 7, 6, 8, 7, 9, 8, 8] },
  { key: "scheduled", label: "Scheduled", value: "14", delta: "next 7 days", series: [9, 10, 11, 11, 12, 13, 13, 14] },
];

export const contentPipeline: FlowStage[] = [
  { id: "idea", label: "Idea" },
  { id: "research", label: "Research" },
  { id: "script", label: "Script" },
  { id: "creation", label: "Creation" },
  { id: "qc", label: "QC" },
  { id: "approval", label: "Founder Approval" },
  { id: "scheduled", label: "Scheduled" },
  { id: "published", label: "Published" },
];

export interface CalendarItem {
  id: string;
  platform: string;
  contentType: string;
  date: string;
  status: StatusTone;
}

export const contentCalendar: CalendarItem[] = [
  { id: "c1", platform: "Instagram", contentType: "Reel", date: "Aug 18", status: "healthy" },
  { id: "c2", platform: "LinkedIn", contentType: "Carousel", date: "Aug 19", status: "healthy" },
  { id: "c3", platform: "TikTok", contentType: "Reel", date: "Aug 21", status: "warning" },
  { id: "c4", platform: "Instagram", contentType: "Post", date: "Aug 22", status: "neutral" },
  { id: "c5", platform: "X", contentType: "Thread", date: "Aug 24", status: "neutral" },
];

export interface LibraryItem {
  id: string;
  kind: "Reel" | "Carousel" | "Post" | "Image" | "Campaign";
  title: string;
  platform: string;
  status: StatusTone;
}

export const contentLibrary: LibraryItem[] = [
  { id: "a1", kind: "Reel", title: "Solar split-timing", platform: "Instagram", status: "healthy" },
  { id: "a2", kind: "Carousel", title: "Retail pricing myths", platform: "LinkedIn", status: "healthy" },
  { id: "a3", kind: "Post", title: "Case study — Helios", platform: "Instagram", status: "neutral" },
  { id: "a4", kind: "Image", title: "Brand collage pack", platform: "X", status: "warning" },
  { id: "a5", kind: "Campaign", title: "Solar Growth Blitz", platform: "Multi", status: "neutral" },
];

export interface QCStatus {
  id: string;
  label: string;
  count: number;
  tone: StatusTone;
}

// Nothing custom-publishes: founder approval is a hard gate in the flow.
export const qcStatuses: QCStatus[] = [
  { id: "pending", label: "QC Pending", count: 8, tone: "warning" },
  { id: "passed", label: "QC Passed", count: 11, tone: "healthy" },
  { id: "failed", label: "QC Failed", count: 2, tone: "danger" },
  { id: "awaiting", label: "Awaiting Founder Approval", count: 9, tone: "active" },
  { id: "approved", label: "Approved", count: 6, tone: "healthy" },
  { id: "scheduled", label: "Scheduled", count: 14, tone: "neutral" },
];