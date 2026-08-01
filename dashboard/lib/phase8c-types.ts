// ── Phase 8C — Collaboration, Integrations & Intelligence Types ──────
// Types for: Communications Hub, Intelligence Layer, Content Hub, Integrations

// ═══════════════════════════════════════════════════════════════════════
// Unified Communications Hub
// ═══════════════════════════════════════════════════════════════════════

export type ConversationSource =
  | "founder"
  | "axiom"
  | "executive"
  | "agent"
  | "slack"
  | "whatsapp"
  | "email"
  | "voice"
  | "notification";

export interface Participant {
  id: string;
  name: string;
  avatar?: string;
  role: string;
  source: ConversationSource;
}

export interface Attachment {
  id: string;
  type: "image" | "file" | "link" | "code" | "document";
  name: string;
  url?: string;
  size?: number;
  preview?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: Participant;
  content: string;
  timestamp: string;
  source: ConversationSource;
  read: boolean;
  attachments: Attachment[];
  thread_id?: string;
  reply_to?: string;
}

export interface Conversation {
  id: string;
  title: string;
  source: ConversationSource;
  participants: Participant[];
  last_message: Message | null;
  unread_count: number;
  project_id?: string;
  executive_id?: string;
  timestamp: string;
  pinned: boolean;
  labels: string[];
  snippet: string;
}

export interface CommunicationsState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  search: string;
  sourceFilter: ConversationSource | "all";
  unreadFilter: boolean;
  pinFilter: boolean;
  loading: boolean;
  error: string | null;
}

// ═══════════════════════════════════════════════════════════════════════
// Intelligence Layer
// ═══════════════════════════════════════════════════════════════════════

export interface ActiveReasoning {
  id: string;
  agent_id: string;
  task: string;
  status: "reasoning" | "executing" | "complete" | "error";
  started_at: string;
  completed_at?: string;
  model: string;
  provider: string;
  tokens_used: number;
  confidence: number;
  reasoning_chain: ReasoningStep[];
}

export interface ReasoningStep {
  id: string;
  type: "analysis" | "tool_call" | "memory_check" | "decision" | "synthesis";
  title: string;
  description: string;
  duration_ms: number;
  tokens_used: number;
  confidence: number;
}

export interface ToolExecution {
  id: string;
  tool_name: string;
  args: Record<string, unknown>;
  result: string;
  duration_ms: number;
  status: "running" | "success" | "error";
  reasoning_id?: string;
  timestamp: string;
}

export interface MemoryRetrieval {
  id: string;
  agent_id: string;
  query: string;
  results: string[];
  duration_ms: number;
  confidence: number;
  timestamp: string;
}

export interface DecisionChain {
  id: string;
  agent_id: string;
  decision: string;
  reasoning: string;
  confidence: number;
  alternatives: { title: string; reasoning: string; confidence: number }[];
  memory_refs: string[];
  tool_refs: string[];
  created_at: string;
}

export interface ProviderUsage {
  provider: string;
  model: string;
  tokens_in: number;
  tokens_out: number;
  requests: number;
  avg_latency_ms: number;
  cost_estimate: number;
}

export interface IntelligenceMetrics {
  active_reasoning: ActiveReasoning[];
  recent_tool_executions: ToolExecution[];
  recent_memory_retrievals: MemoryRetrieval[];
  decision_chains: DecisionChain[];
  provider_usage: ProviderUsage[];
  total_tokens_today: number;
  total_requests_today: number;
  avg_latency_ms: number;
  avg_confidence: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
}

// ═══════════════════════════════════════════════════════════════════════
// Generated Content Hub
// ═══════════════════════════════════════════════════════════════════════

export type AssetType =
  | "research"
  | "document"
  | "image"
  | "video"
  | "audio"
  | "code"
  | "report"
  | "presentation"
  | "spreadsheet";

export interface AssetVersion {
  version_id: string;
  version_number: number;
  content: string;
  size: number;
  created_at: string;
  author: string;
  change_description: string;
}

export interface ContentAsset {
  id: string;
  type: AssetType;
  title: string;
  description: string;
  tags: string[];
  project_id?: string;
  executive_id?: string;
  executive_name?: string;
  memory_refs: string[];
  version_history: AssetVersion[];
  current_version: number;
  preview_url?: string;
  preview_type?: "image" | "code" | "text" | "markdown";
  created_at: string;
  updated_at: string;
  size: number;
  starred: boolean;
}

export interface ContentHubState {
  assets: ContentAsset[];
  activeAsset: ContentAsset | null;
  search: string;
  typeFilter: AssetType | "all";
  tagFilter: string[];
  projectFilter: string | null;
  executiveFilter: string | null;
  starredOnly: boolean;
  loading: boolean;
  error: string | null;
}

// ═══════════════════════════════════════════════════════════════════════
// Integration Layer
// ═══════════════════════════════════════════════════════════════════════

export type IntegrationServiceType =
  | "github"
  | "claude_code"
  | "vscode"
  | "tradingview"
  | "mt5"
  | "gmail"
  | "calendar"
  | "crm"
  | "whatsapp"
  | "custom";

export type ConnectionStatus = "connected" | "disconnected" | "error" | "pending";

export interface IntegrationEvent {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  status: "success" | "error" | "warning";
}

export interface IntegrationService {
  id: string;
  name: string;
  type: IntegrationServiceType;
  description: string;
  status: ConnectionStatus;
  permissions: string[];
  health: "healthy" | "degraded" | "unhealthy";
  last_connected: string | null;
  activity_count: number;
  recent_events: IntegrationEvent[];
  logs: string[];
  icon: string;
  configurable: boolean;
}

export interface IntegrationsState {
  services: IntegrationService[];
  activeService: IntegrationService | null;
  loading: boolean;
  error: string | null;
}

// ═══════════════════════════════════════════════════════════════════════
// Collaboration Workspace
// ═══════════════════════════════════════════════════════════════════════

export type SessionStatus = "active" | "scheduled" | "completed";
export type ParticipantRole = "owner" | "editor" | "viewer";
export type SessionType = "code" | "brainstorm" | "review" | "design";

export interface TeamMember {
  id: string;
  name: string;
  role: ParticipantRole;
  avatar: string;
  status: "online" | "idle" | "offline";
  email: string;
}

export interface CollaborationSession {
  id: string;
  title: string;
  participants: Participant[];
  messages: Message[];
  linked_project_id?: string;
  linked_workflow_id?: string;
  decisions: CollaborationDecision[];
  created_at: string;
  updated_at: string;
  active: boolean;
  /* UI-level fields */
  type: SessionType;
  status: SessionStatus;
  lastActivity: string;
  branch?: string;
  startedAt: string;
}

export interface CollaborationDecision {
  id: string;
  title: string;
  description: string;
  made_by: string;
  timestamp: string;
  context: string;
  memory_ref: string | null;
  approved: boolean;
  approved_by?: string;
}

export interface CollaborationState {
  sessions: CollaborationSession[];
  activeSession: CollaborationSession | null;
  loading: boolean;
  error: string | null;
}