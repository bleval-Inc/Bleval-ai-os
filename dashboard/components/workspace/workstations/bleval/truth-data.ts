// TRUTH ENGINE — placeholder research/intelligence data.
// Later supplied by the dedicated BLEVAL research database.

import type { MetricKpi } from "./types";

export const truthKpis: MetricKpi[] = [
  { key: "active", label: "Active Research", value: "5", delta: "3 underway", series: [2, 3, 3, 4, 4, 5, 5, 5] },
  { key: "completed", label: "Completed", value: "12", delta: "+2 wk", series: [6, 7, 8, 8, 9, 10, 11, 12] },
  { key: "sources", label: "Sources Analysed", value: "248", delta: "+14%", series: [142, 158, 172, 181, 196, 212, 231, 248] },
  { key: "insights", label: "Insights Generated", value: "37", delta: "16 new", series: [14, 18, 20, 23, 26, 30, 33, 37] },
];

export interface IntelligenceBlock {
  id: string;
  title: string;
  meta: string;
  points: string[];
  value: number; // relative indicator 0-100
}

export const marketIntelligence: IntelligenceBlock[] = [
  {
    id: "trends",
    title: "Market trends",
    meta: "Shifts shaping demand",
    value: 82,
    points: [
      "AI-assisted brand platforms rising",
      "Short-form video dominating lead gen",
      "Fixed-fee retainers gaining share",
    ],
  },
  {
    id: "competitors",
    title: "Competitor observations",
    meta: "Positioning and offers",
    value: 64,
    points: [
      "Competitors bundle creative plus media under one roof",
      "Common gap: no transparent ROI reporting",
      "Pricing clustered mid-tier; premium space open",
    ],
  },
  {
    id: "customers",
    title: "Customer behaviour",
    meta: "Decision drivers",
    value: 71,
    points: [
      "40% shortlist within 72h of first touch",
      "Referral trust outweighs cold outreach",
      "Speed of proposal response is a top close factor",
    ],
  },
  {
    id: "opportunities",
    title: "Emerging opportunities",
    meta: "Adjacent niches",
    value: 58,
    points: [
      "In-house creative outsourcing for funded teams",
      "Performance-linked compensation models",
      "Niche vertical reels packages",
    ],
  },
];

export interface ResearchProject {
  id: string;
  topic: string;
  market: string;
  status: "active" | "paused" | "complete";
  priority: "high" | "medium" | "low";
  lastUpdated: string;
  findings: number;
}

export const researchProjects: ResearchProject[] = [
  { id: "r1", topic: "Solar campaign positioning", market: "Renewable energy", status: "active", priority: "high", lastUpdated: "2h ago", findings: 9 },
  { id: "r2", topic: "Fintech owner pain points", market: "Fintech", status: "active", priority: "high", lastUpdated: "5h ago", findings: 7 },
  { id: "r3", topic: "Luxury real estate buyer journey", market: "Property", status: "active", priority: "medium", lastUpdated: "1d ago", findings: 5 },
  { id: "r4", topic: "Healthcare provider offer gaps", market: "Healthcare", status: "paused", priority: "medium", lastUpdated: "3d ago", findings: 4 },
  { id: "r5", topic: "Packaging design pricing tiers", market: "Creative services", status: "complete", priority: "low", lastUpdated: "6d ago", findings: 6 },
];

export interface IntelligenceFinding {
  id: string;
  finding: string;
  evidence: string;
  sources: number;
  confidence: number; // 0-100
  implication: string;
}

export const intelligenceFindings: IntelligenceFinding[] = [
  {
    id: "f1",
    finding: "Buyers respond 3.2x faster to value-led offers than feature-led ones",
    evidence: "Across 41 outreach samples, value-first subjects opened at 58% vs 18%.",
    sources: 128,
    confidence: 88,
    implication: "Reframe offers around measurable outcomes, not deliverables.",
  },
  {
    id: "f2",
    finding: "A transparent ROI reporting layer is an open differentiation slot",
    evidence: "9 of 12 audited competitors omit performance reporting from pricing.",
    sources: 76,
    confidence: 82,
    implication: "Lead sales and strategy with a visible delivery ROI section.",
  },
  {
    id: "f3",
    finding: "Decision latency drops sharply with same-day first response",
    evidence: "Qualified leads contacted within 1h booked 44% more calls.",
    sources: 154,
    confidence: 90,
    implication: "Tier outreach speed as a signal across Acquisition.",
  },
];

export interface StrategicOutput {
  id: string;
  channel: string;
  usage: number;
}

export const strategicOutputs: StrategicOutput[] = [
  { id: "s1", channel: "Content", usage: 24 },
  { id: "s2", channel: "Offers", usage: 14 },
  { id: "s3", channel: "Proposals", usage: 11 },
  { id: "s4", channel: "Sales", usage: 9 },
  { id: "s5", channel: "Client strategy", usage: 8 },
];