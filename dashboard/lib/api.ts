// ── AXIOM OS API Client ─────────────────────────────────────────────
// Consumes the existing runtime APIs via Next.js proxy (no direct backend access)

import type {
  Agent,
  AgentDetail,
  AgentMemory,
  Approval,
  ApprovalResponse,
  Capability,
  EventType,
  Executive,
  ExecutiveBoardStatus,
  ExecutiveDetail,
  ExecutiveLoopStatus,
  HealthSummary,
  IntelligenceProvidersResponse,
  KnowledgeEntry,
  LearningCycle,
  LearningPattern,
  LearningRecommendation,
  LearningStatus,
  Organisation,
  OrganisationDetail,
  PerformanceScore,
  PlaybookEvolution,
  RuntimeStatus,
  ScoreHistory,
  SystemStatus,
  Workflow,
  WorkflowAnalytics,
  WorkflowInstance,
  WorkflowLaunchRequest,
  WorkflowLaunchResponse,
} from "./api-types";

const BASE = "/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }

  return res.json() as Promise<T>;
}

// ── System ──────────────────────────────────────────────────────────

export const system = {
  root: () => fetchApi<SystemStatus>(""),
  status: () => fetchApi<RuntimeStatus>("/status"),
  health: () => fetchApi<HealthSummary>("/health"),
  getRuntimeStatus: () => fetchApi<RuntimeStatus>("/status"),
  getIntelligenceProviders: () =>
    fetchApi<IntelligenceProvidersResponse>("/intelligence/providers"),
  // Shortcut aliases used by workspace components
  getExecutiveBoardStatus: () => executives.boardStatus(),
  getPerformanceScores: () => learning.scores(),
  getWorkflowAnalytics: () => learning.workflowAnalytics(),
  getKnowledgeEntries: () => learning.knowledge(),
  listCapabilities: () => capabilities.list(),
  listWorkflows: () => workflows.list(),
  listWorkflowInstances: () => instances.list(),
};

// ── Organisations ───────────────────────────────────────────────────

export const organisations = {
  list: () => fetchApi<Organisation[]>("/organisations"),
  get: (id: string) => fetchApi<OrganisationDetail>(`/organisations/${id}`),
  departments: (orgId: string) =>
    fetchApi<string[]>(`/organisations/${orgId}/departments`),
};

// ── Executives ──────────────────────────────────────────────────────

export const executives = {
  list: () => fetchApi<Executive[]>("/executives"),
  get: (id: string) => fetchApi<ExecutiveDetail>(`/executives/${id}`),
  boardStatus: () => fetchApi<ExecutiveBoardStatus>("/executives/board/status"),
  triggerBoard: (cycleType = "manual") =>
    fetchApi<Record<string, unknown>>("/executives/board/trigger", {
      method: "POST",
      body: JSON.stringify({ cycle_type: cycleType }),
    }),
  loopStatus: (id: string) =>
    fetchApi<ExecutiveLoopStatus>(`/executives/${id}/loop/status`),
  triggerCycle: (id: string, cycleType = "manual") =>
    fetchApi<Record<string, unknown>>(`/executives/${id}/loop/trigger`, {
      method: "POST",
      body: JSON.stringify({ cycle_type: cycleType }),
    }),
  schedules: (id: string) =>
    fetchApi<Record<string, string>>(`/executives/${id}/loop/schedules`),
};

// ── Agents ──────────────────────────────────────────────────────────

export const agents = {
  list: () => fetchApi<Agent[]>("/agents"),
  get: (id: string) => fetchApi<AgentDetail>(`/agents/${id}`),
};

// ── Workflows ───────────────────────────────────────────────────────

export const workflows = {
  list: () => fetchApi<Workflow[]>("/workflows"),
  get: (id: string) => fetchApi<Record<string, unknown>>(`/workflows/${id}`),
  launch: (req: WorkflowLaunchRequest) =>
    fetchApi<WorkflowLaunchResponse>("/workflows/launch", {
      method: "POST",
      body: JSON.stringify(req),
    }),
};

// ── Instances ───────────────────────────────────────────────────────

export const instances = {
  list: (status?: string) =>
    fetchApi<WorkflowInstance[]>(
      `/instances${status ? `?status=${status}` : ""}`,
    ),
  get: (id: string) =>
    fetchApi<Record<string, unknown>>(`/instances/${id}`),
  advance: (id: string, stepOutput?: Record<string, unknown>) =>
    fetchApi<Record<string, unknown>>(`/instances/${id}/advance`, {
      method: "POST",
      body: JSON.stringify({ step_output: stepOutput }),
    }),
  cancel: (id: string) =>
    fetchApi<Record<string, unknown>>(`/instances/${id}/cancel`, {
      method: "POST",
    }),
};

// ── Events ──────────────────────────────────────────────────────────

export const events = {
  types: () => fetchApi<EventType[]>("/events/types"),
  publish: (
    eventType: string,
    source: string,
    payload?: Record<string, unknown>,
    correlationId?: string,
  ) =>
    fetchApi<{ event_type: string; published: boolean }>("/events/publish", {
      method: "POST",
      body: JSON.stringify({
        event_type: eventType,
        source,
        payload,
        correlation_id: correlationId,
      }),
    }),
};

// ── Capabilities ────────────────────────────────────────────────────

export const capabilities = {
  list: (search?: string) =>
    fetchApi<Capability[]>(
      `/capabilities${search ? `?search=${encodeURIComponent(search)}` : ""}`,
    ),
  get: (id: string) => fetchApi<Record<string, unknown>>(`/capabilities/${id}`),
};

// ── Memory ──────────────────────────────────────────────────────────

export const memory = {
  get: (agentId: string, org = "", dept = "") =>
    fetchApi<AgentMemory>(
      `/memory/${agentId}?org=${org}&dept=${dept}`,
    ),
};

// ── Approvals ───────────────────────────────────────────────────────

export const approvals = {
  list: (status?: string) =>
    fetchApi<Approval[]>(
      `/approvals${status ? `?status=${status}` : ""}`,
    ),
  respond: (id: string, req: ApprovalResponse) =>
    fetchApi<{ approval_id: string; approved: boolean }>(
      `/approvals/${id}/respond`,
      { method: "POST", body: JSON.stringify(req) },
    ),
};

// ── Learning Engine ─────────────────────────────────────────────────

export const learning = {
  status: () => fetchApi<LearningStatus>("/learning/status"),
  scores: () => fetchApi<PerformanceScore[]>("/learning/scores"),
  scoreHistory: (type: string, id: string) =>
    fetchApi<ScoreHistory>(`/learning/scores/${type}/${id}`),
  workflowAnalytics: (workflowId?: string) =>
    fetchApi<WorkflowAnalytics[]>(
      `/learning/analytics/workflows${
        workflowId ? `?workflow_id=${workflowId}` : ""
      }`,
    ),
  patterns: (severity?: string) =>
    fetchApi<LearningPattern[]>(
      `/learning/patterns${severity ? `?severity=${severity}` : ""}`,
    ),
  recommendations: (status?: string) =>
    fetchApi<LearningRecommendation[]>(
      `/learning/recommendations${
        status ? `?status=${status}` : ""
      }`,
    ),
  knowledge: () => fetchApi<KnowledgeEntry[]>("/learning/knowledge"),
  cycles: (limit = 10) =>
    fetchApi<LearningCycle[]>(`/learning/cycles?limit=${limit}`),
  runCycle: (entityId = "system", entityType = "system") =>
    fetchApi<Record<string, unknown>>("/learning/cycle/run", {
      method: "POST",
      body: JSON.stringify({ entity_id: entityId, entity_type: entityType }),
    }),
  playbookEvolutions: () =>
    fetchApi<PlaybookEvolution[]>("/learning/playbook-evolutions"),
};

export { ApiError };