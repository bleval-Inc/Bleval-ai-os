// AXIOM SYSTEM console data — isolated placeholder telemetry.
// The machine's instrument panel: tells the Founder whether Axiom is healthy,
// executives are online, the AI brain is connected, and core services are up.
// Replace these values with real system telemetry in a later step.
// No new backend endpoints or infrastructure are introduced.

export interface MetricPanel {
  key: string;
  label: string;
  value: string;
  unit: string;
  series: number[];
}

export interface ExecutiveStatus {
  key: string;
  name: string;
  status: "online" | "offline";
}

export type ServiceStatus =
  | "Online"
  | "Connected"
  | "Operational"
  | "Offline";

export interface CoreService {
  key: string;
  label: string;
  status: ServiceStatus;
}

export interface Uptime {
  days: number;
  hours: number;
  minutes: number;
}

export interface AxiomData {
  identity: string;
  health: number;
  healthMessage: string;
  healthSeries: number[];
  metrics: MetricPanel[];
  executives: ExecutiveStatus[];
  services: CoreService[];
  uptime: Uptime;
}

export const axiomData: AxiomData = {
  identity: "AYA",
  health: 98,
  healthMessage: "All systems operational",
  healthSeries: [89, 92, 90, 95, 93, 96, 97, 96, 98],
  metrics: [
    {
      key: "cpu",
      label: "CPU",
      value: "24",
      unit: "%",
      series: [12, 30, 22, 42, 28, 35, 19, 27, 24],
    },
    {
      key: "memory",
      label: "Memory",
      value: "61",
      unit: "%",
      series: [52, 55, 60, 58, 63, 59, 62, 64, 61],
    },
    {
      key: "storage",
      label: "Storage",
      value: "42",
      unit: "%",
      series: [36, 38, 37, 40, 39, 41, 42, 41, 42],
    },
    {
      key: "network",
      label: "Network",
      value: "18",
      unit: "ms",
      series: [40, 32, 25, 38, 22, 29, 21, 26, 18],
    },
  ],
  executives: [
    { key: "jenson", name: "Jenson", status: "online" },
    { key: "valta-prime", name: "Valta Prime", status: "online" },
    { key: "yamako", name: "Yamako", status: "online" },
  ],
  services: [
    { key: "core", label: "AXIOM CORE", status: "Online" },
    { key: "workflows", label: "WORKFLOW ENGINE", status: "Online" },
    { key: "agents", label: "AGENT SYSTEM", status: "Online" },
    { key: "llm", label: "LLM CONNECTION", status: "Connected" },
    { key: "api", label: "BACKEND/API", status: "Operational" },
  ],
  uptime: { days: 4, hours: 18, minutes: 32 },
};