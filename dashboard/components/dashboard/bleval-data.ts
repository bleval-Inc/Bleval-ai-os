// BLEVAL INC demo data — isolated placeholder values.
// Replace these with live workstation data in a later step.

export interface Point {
  label: string;
  value: number;
}

export interface KPI {
  key: string;
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down";
  series: number[];
}

export interface ClientRow {
  id: string;
  name: string;
  initiative: string;
  value: string;
  initials: string;
  hue: string;
}

export interface FunnelStage {
  id: string;
  label: string;
  value: number;
}

export interface BreakdownSlice {
  id: string;
  label: string;
  value: number;
  color: string;
}

export interface BlevalDashboardData {
  revenueSeries: Point[];
  revenueTotal: string;
  revenueDelta: string;
  kpis: KPI[];
  clients: ClientRow[];
  funnel: { total: string; stages: FunnelStage[] };
  breakdown: { total: string; slices: BreakdownSlice[] };
}

export const blevalData: BlevalDashboardData = {
  revenueSeries: [
    { label: "Jan", value: 22 },
    { label: "Feb", value: 28 },
    { label: "Mar", value: 26 },
    { label: "Apr", value: 35 },
    { label: "May", value: 32 },
    { label: "Jun", value: 41 },
    { label: "Jul", value: 38 },
    { label: "Aug", value: 45 },
  ],
  revenueTotal: "$42,500",
  revenueDelta: "+18.4%",
  kpis: [
    {
      key: "revenue",
      label: "Revenue",
      value: "$42,500",
      delta: "+18.4%",
      trend: "up",
      series: [22, 26, 24, 30, 35, 33, 40, 42],
    },
    {
      key: "profit",
      label: "Net Profit",
      value: "$28,200",
      delta: "+11.2%",
      trend: "up",
      series: [18, 20, 19, 24, 26, 27, 28, 28],
    },
    {
      key: "growth",
      label: "Growth",
      value: "+18.4%",
      delta: "+3.2 pts",
      trend: "up",
      series: [8, 10, 12, 11, 14, 16, 18, 18],
    },
    {
      key: "clients",
      label: "Clients",
      value: "+12",
      delta: "8 new",
      trend: "up",
      series: [2, 3, 3, 5, 6, 8, 10, 12],
    },
  ],
  clients: [
    { id: "c1", name: "Nova Dynamics", initiative: "Platform Retainer", value: "$8,200/mo", initials: "ND", hue: "from-indigo-500 to-blue-500" },
    { id: "c2", name: "Vertex Labs", initiative: "Product Build", value: "$12,500/mo", initials: "VL", hue: "from-violet-500 to-purple-500" },
    { id: "c3", name: "Orbit Health", initiative: "Consulting", value: "$5,400/mo", initials: "OH", hue: "from-cyan-500 to-sky-500" },
    { id: "c4", name: "Helios Capital", initiative: "Retainer + Commission", value: "$9,800/mo", initials: "HC", hue: "from-emerald-500 to-teal-500" },
  ],
  funnel: {
    total: "$42,500",
    stages: [
      { id: "upfront", label: "Upfront", value: 48 },
      { id: "retainers", label: "Retainers", value: 34 },
      { id: "commissions", label: "Commissions", value: 18 },
    ],
  },
  breakdown: {
    total: "$42,500",
    slices: [
      { id: "upfront", label: "Upfront", value: 20400, color: "#6d7cff" },
      { id: "retainers", label: "Retainers", value: 14450, color: "#a88cff" },
      { id: "commissions", label: "Commissions", value: 7650, color: "#00d4ff" },
    ],
  },
};