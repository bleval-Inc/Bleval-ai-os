// ── AXIOM OS API Types ───────────────────────────────────────────────
// Generated from backend routes.py — consumes existing runtime APIs

// ── Runtime & System ─────────────────────────────────────────────────

export interface SystemStatus {
  service: string;
  version: string;
  status: "running" | "initialising";
  docs: string;
}

export interface RuntimeStatus {
  version: string;
  initialised: boolean;
  running: boolean;
  components: Record<string, boolean>;
  health: HealthSummary;
  workflows_defined: number;
  executives: number;
  org_count: number;
}

export interface HealthSummary {
  total: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
  overall: "healthy" | "unhealthy";
  last_check: string;
}

// ── Organisations ────────────────────────────────────────────────────

export interface Organisation {
  id: string;
  name: string;
  executives: string[];
}

export interface OrganisationDetail extends Organisation {
  departments?: string[];
  agents?: string[];
  boundaries?: Record<string, unknown>;
}

// ── Executives ───────────────────────────────────────────────────────

export interface Executive {
  id: string;
  org: string;
  department: string;
}

export interface ExecutiveDetail extends Executive {
  description?: string;
  capabilities?: string[];
  knowledge?: string[];
  permissions?: Record<string, unknown>;
}

export interface ExecutiveBoardStatus {
  [exec_id: string]: {
    org: string;
    status: "running" | "stopped" | "error";
    cycle_count: number;
    last_cycle?: string;
    schedules: Record<string, string>;
  };
}

export interface ExecutiveLoopStatus {
  exec_id: string;
  org_id: string;
  running: boolean;
  cycle_count: number;
  last_cycle?: string;
  schedules: Record<string, string>;
}

// ── Agents ───────────────────────────────────────────────────────────

export interface Agent {
  id: string;
  org: string;
  department: string;
  type: string;
}

export interface AgentDetail extends Agent {
  capabilities?: string[];
  permissions?: Record<string, unknown>;
  memory_config?: Record<string, unknown>;
}

// ── Workflows ────────────────────────────────────────────────────────

export interface Workflow {
  id: string;
  description: string;
  department: string;
  org: string;
  steps: number;
}

export interface WorkflowLaunchRequest {
  workflow_id: string;
  context: Record<string, unknown>;
}

export interface WorkflowLaunchResponse {
  instance_id: string;
  workflow_id: string;
  status: string;
}

export interface WorkflowInstance {
  instance_id: string;
  workflow_id: string;
  status: string;
  created_at: string;
  current_step: number;
  total_steps: number;
}

// ── Events ───────────────────────────────────────────────────────────

export interface EventType {
  name: string;
  channel: string;
  description: string;
}

// ── Capabilities ─────────────────────────────────────────────────────

export interface Capability {
  id: string;
  category: string;
  name: string;
  level: string;
  agents: string[];
}

// ── Memory ───────────────────────────────────────────────────────────

export interface AgentMemory {
  agent_id: string;
  files: string[];
  content: Record<string, string>;
}

// ── Approvals ────────────────────────────────────────────────────────

export interface Approval {
  approval_id: string;
  workflow_id: string;
  step_name: string;
  status: string;
  requested_by: string;
  requested_at: string;
}

export interface ApprovalResponse {
  approval_id: string;
  approved: boolean;
  approved_by: string;
  notes?: string;
}

// ── Learning Engine ──────────────────────────────────────────────────

export interface LearningStatus {
  total_learning_cycles: number;
  total_patterns_detected: number;
  total_recommendations: number;
  total_knowledge_entries: number;
  active_patterns: number;
  pending_recommendations: number;
  last_cycle?: string;
}

// ── Intelligence Providers ───────────────────────────────────────────

export interface IntelligenceProvider {
  name: string;
  available: boolean;
  type: string;
  label: string;
  model: string;
  role: string;
  provider: string;
}

export interface IntelligenceProvidersResponse {
  has_real_provider: boolean;
  total_providers: number;
  providers: IntelligenceProvider[];
}

export interface PerformanceScore {
  entity_id: string;
  entity_type: string;
  running_average: number;
  trend: string;
  total_scores: number;
  last_updated: string | null;
}

export interface ScoreHistory {
  entity_id: string;
  entity_type: string;
  running_average: number;
  trend: string;
  scores: ScoreEntry[];
}

export interface ScoreEntry {
  overall: number;
  categories: Record<string, number>;
  duration: number;
  step_count: number;
  error_count: number;
  retry_count: number;
  timestamp: string;
}

export interface WorkflowAnalytics {
  workflow_id: string;
  total_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  avg_retries: number;
  trend: string;
  failure_reasons: Record<string, number>;
  last_run: string | null;
}

export interface LearningPattern {
  pattern_id: string;
  pattern_type: string;
  severity: "info" | "warning" | "critical";
  title: string;
  description: string;
  entities_involved: string[];
  frequency: number;
  impact_score: number;
  first_detected: string;
  last_detected: string;
}

export interface LearningRecommendation {
  recommendation_id: string;
  title: string;
  description: string;
  expected_impact: string;
  confidence: number;
  status: string;
  change_type: string;
  suggested_action: string;
  created_at: string;
  approved_by: string | null;
}

export interface KnowledgeEntry {
  entry_id: string;
  title: string;
  content: string;
  source: string;
  confidence: number;
  tags: string[];
  created_at: string;
}

export interface LearningCycle {
  cycle_id: string;
  source_entity: string;
  scores: number;
  patterns_detected: number;
  recommendations: number;
  knowledge_written: number;
  duration_seconds: number;
  success: boolean;
  completed_at: string | null;
}

export interface PlaybookEvolution {
  playbook_name: string;
  version: number;
  change_description: string;
  triggered_by_pattern: string;
  applied_at: string;
  approved_by: string | null;
}

// ═══════════════════════════════════════════════════════════════════════════
// Phase A — AXIOM Core Types
// ═══════════════════════════════════════════════════════════════════════════

export interface AxiomStatus {
  state: string;
  boot_id: string;
  is_online: boolean;
  awareness: SystemAwareness;
}

export interface SystemAwareness {
  timestamp: number;
  state: string;
  health_score: number;
  uptime_seconds: number;
  overall_health: string;
  executives: ExecutiveAwareness[];
  engines: EngineAwareness[];
  workflows: WorkflowAwareness;
  intelligence_available: boolean;
  pending_approvals: number;
  running_since: number;
  boot_id: string;
}

export interface ExecutiveAwareness {
  id: string;
  org: string;
  state: string;
  cycle_count: number;
  last_cycle: string | null;
  health: string;
}

export interface EngineAwareness {
  name: string;
  state: string;
  label: string;
}

export interface WorkflowAwareness {
  defined: number;
  active: number;
  pending: number;
  failed: number;
  awaiting_approval: number;
}

export interface AxiomChatResponse {
  response: string;
  agent_id: string;
  category?: string;
  awareness?: SystemAwareness;
  intent?: string;
}

export interface AxiomRouteResponse {
  category: string;
  complexity: string;
  intent: string;
  confidence: number;
  handler: string;
  target: string;
  requires_approval: boolean;
  response: string;
  awareness?: SystemAwareness;
}

export interface ResearchWorkspaceSummary {
  id: string;
  title: string;
  query: string;
  created_at: string;
  status: string;
  sources_count: number;
  findings_count: number;
  conversation_length: number;
}

export interface ResearchWorkspace extends ResearchWorkspaceSummary {
  conversation: ConversationEntry[];
  sources: ResearchSource[];
  findings: ResearchFinding[];
  conclusions: ResearchConclusion[];
  documents_count: number;
  images_count: number;
  videos_count: number;
  audio_count: number;
  notes_count: number;
  references_count: number;
  decisions_count: number;
  actions_count: number;
  generated_assets_count: number;
}

export interface ConversationEntry {
  role: string;
  content: string;
  type?: string;
  timestamp: string;
}

export interface ResearchSource {
  type: string;
  url?: string;
  title?: string;
  added_at: string;
  [key: string]: unknown;
}

export interface ResearchFinding {
  title?: string;
  content: string;
  confidence?: number;
  source?: string;
  added_at: string;
  [key: string]: unknown;
}

export interface ResearchConclusion {
  summary: string;
  details?: string;
  added_at: string;
  [key: string]: unknown;
}