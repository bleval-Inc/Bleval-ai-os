import { create } from "zustand";
import type {
  RuntimeStatus,
  ExecutiveBoardStatus,
  HealthSummary,
  FounderAvailability,
  LearningStatus,
  LearningPattern,
  LearningRecommendation,
  KnowledgeEntry,
  WorkflowAnalytics,
  LearningCycle,
  PerformanceScore,
} from "../api-types";

export interface FounderModel {
  decisionPatterns: Record<string, number>;
  approvedFormats: string[];
  workingHours: { start: number; end: number };
  preferredOutputs: string[];
  communicationStyle: string;
  recurringPriorities: string[];
  approvedStandards: string[];
}

export interface QCLearningSignal {
  failureType: string;
  workflowId: string;
  count: number;
  trend: "improving" | "declining" | "stable";
  lastDetected: string;
}

export interface SelfHealerStatus {
  totalRecoveryEvents: number;
  successful: number;
  verified: number;
  successRate: number;
  componentsWithHistory: string[];
  circuitBreakers: Record<string, { attempts: number; open: boolean }>;
}

// ── Workstation identifiers (Phase E) ───────────────────────────────
export type WorkstationId =
  | "axiom"
  | "bleval"
  | "valta"
  | "personal";

export type WorkstationStatus = "healthy" | "degraded" | "busy" | "idle";

// ── Workspace identifiers ────────────────────────────────────────────
export type WorkspaceId =
  | "workspace"         // 1: Founder (AXIOM Workstation)
  | "executives"        // 2: Executive Board
  | "operations"        // 3: Operations Center
  | "knowledge"         // 4: Knowledge
  | "projects"          // 5: Projects
  | "creator"           // 6: Creator Studio
  | "trading"           // 7: Trading Terminal
  | "console"           // 8: Founder Console
  | "communications"    // 9: Communications Hub (Phase 8C)
  | "intelligence"      // 10: Intelligence Center (Phase 8C)
  | "content-hub"       // 11: Content Hub (Phase 8C)
  | "integrations"      // 12: Integrations (Phase 8C)
  | "collaboration"     // 13: Collaboration Workspace (Phase 8C)
  | "axiom-workspace"   // 14: AXIOM Workstation
  | "research";         // 15: Research Workspace

export interface WorkspaceState {
  expandedSections: Record<string, boolean>;
  scrollPosition: number;
  selectedItem: string | null;
  activePanel: string | null;
}

function defaultWorkspaceState(): WorkspaceState {
  return {
    expandedSections: {},
    scrollPosition: 0,
    selectedItem: null,
    activePanel: null,
  };
}

interface AxiomState {
  // Runtime state
  runtime: RuntimeStatus | null;
  health: HealthSummary | null;
  executiveBoard: ExecutiveBoardStatus | null;

  // UI state
  commandPaletteOpen: boolean;
  sidePanel: "memory" | "files" | "none";
  activeView: WorkspaceId;
  activeWorkstation: WorkstationId;
  workstationStatus: Record<WorkstationId, WorkstationStatus>;
  activeWorkstationView: WorkspaceId;
  sidebarCollapsed: boolean;

  // Per-workspace persistent state
  workspaceStates: Record<WorkspaceId, WorkspaceState>;

  // Executive board
  selectedExecutive: string | null;
  executiveMeetingActive: boolean;
  currentSpeaker: string | null;

  // Voice
  voiceActive: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  isAwake: boolean;
  pendingVoiceCommand: string | null;
  voiceWakeTimeout: number | null;
  listeningExecutive: string | null;  // "axiom" | "jenson" | "valta_prime" | "yamako" | null

  // Notifications
  notifications: EnhancedNotification[];
  notificationPanelOpen: boolean;

  // Phase F — Board Room state
  boardMeetings: import("../api-types").BoardMeeting[];
  boardActiveMeeting: import("../api-types").BoardMeetingDetail | null;
  boardKpis: Record<string, Record<string, number>>;
  boardActionItems: import("../api-types").BoardActionItemsResponse | null;

  // Phase F — Founder availability
  founderAvailability: FounderAvailability;
  founderManualOverride: string | null;
  founderLastActive: number;

  // Phase F — Emergency state
  emergencyActive: boolean;
  emergencySource: string | null;
  emergencyLevel: string | null;

  // Phase F — Speaker queue mirror
  activeSpeaker: import("../api-types").SpeakerId | null;

  // Phase G — Learning + Optimization state
  learningStatus: LearningStatus | null;
  learningPatterns: LearningPattern[];
  learningRecommendations: LearningRecommendation[];
  learningKnowledge: KnowledgeEntry[];
  workflowAnalytics: WorkflowAnalytics[];
  learningCycles: LearningCycle[];
  performanceScores: PerformanceScore[];
  founderModel: FounderModel;
  qcLearningSignals: QCLearningSignal[];
  selfHealerStatus: SelfHealerStatus | null;
  selectedLearningTab: string;

  // Phase G — Learning actions
  setLearningStatus: (s: LearningStatus | null) => void;
  setLearningPatterns: (p: LearningPattern[]) => void;
  setLearningRecommendations: (r: LearningRecommendation[]) => void;
  setLearningKnowledge: (k: KnowledgeEntry[]) => void;
  setWorkflowAnalytics: (a: WorkflowAnalytics[]) => void;
  setLearningCycles: (c: LearningCycle[]) => void;
  setPerformanceScores: (s: PerformanceScore[]) => void;
  setFounderModel: (m: Partial<FounderModel>) => void;
  setQCLearningSignals: (s: QCLearningSignal[]) => void;
  setSelfHealerStatus: (s: SelfHealerStatus | null) => void;
  setSelectedLearningTab: (tab: string) => void;

  // Actions
  setRuntime: (r: RuntimeStatus) => void;
  setHealth: (h: HealthSummary) => void;
  setExecutiveBoard: (b: ExecutiveBoardStatus) => void;
  toggleCommandPalette: () => void;
  setCommandPalette: (open: boolean) => void;
  setSidePanel: (panel: "memory" | "files" | "none") => void;
  setActiveView: (view: WorkspaceId) => void;
  setActiveWorkstation: (ws: WorkstationId) => void;
  setWorkstationStatus: (ws: WorkstationId, status: WorkstationStatus) => void;
  setActiveWorkstationView: (view: WorkspaceId) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setWorkspaceState: (workspace: WorkspaceId, state: Partial<WorkspaceState>) => void;
  setSelectedExecutive: (id: string | null) => void;
  setExecutiveMeetingActive: (active: boolean) => void;
  setCurrentSpeaker: (speaker: string | null) => void;
  setVoiceActive: (active: boolean) => void;
  setIsListening: (listening: boolean) => void;
  setIsSpeaking: (speaking: boolean) => void;
  setIsAwake: (awake: boolean) => void;
  setPendingVoiceCommand: (cmd: string | null) => void;
  setVoiceWakeTimeout: (id: number | null) => void;
  setListeningExecutive: (exec: string | null) => void;

  // Phase F — Board Room actions
  setBoardMeetings: (meetings: import("../api-types").BoardMeeting[]) => void;
  setBoardActiveMeeting: (meeting: import("../api-types").BoardMeetingDetail | null) => void;
  setBoardKpis: (kpis: Record<string, Record<string, number>>) => void;
  setBoardActionItems: (items: import("../api-types").BoardActionItemsResponse | null) => void;

  // Phase F — Founder availability actions
  setFounderAvailability: (availability: FounderAvailability) => void;
  setFounderManualOverride: (override: string | null) => void;
  setFounderLastActive: (timestamp: number) => void;

  // Phase F — Emergency actions
  setEmergencyActive: (active: boolean) => void;
  setEmergencySource: (source: string | null) => void;
  setEmergencyLevel: (level: string | null) => void;
  clearEmergency: () => void;

  // Phase F — Speaker actions
  setActiveSpeaker: (speaker: import("../api-types").SpeakerId | null) => void;

  addNotification: (n: Notification) => void;
  dismissNotification: (id: string) => void;
  setNotificationPanelOpen: (open: boolean) => void;
  toggleNotificationPanel: () => void;
  snoozeNotification: (id: string, until: number) => void;
  acknowledgeNotification: (id: string) => void;
  clearNotification: (id: string) => void;
  clearAllNotifications: () => void;
  addSystemNotification: (n: Omit<EnhancedNotification, "id" | "timestamp" | "read" | "acknowledged" | "snoozedUntil">) => void;
}

export interface Notification {
  id: string;
  type: "info" | "warning" | "error" | "success";
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
}

export type NotificationCategory = "executive" | "workflow" | "runtime" | "security" | "learning" | "integration";
export type NotificationPriority = "urgent" | "high" | "normal" | "low";

export interface EnhancedNotification {
  id: string;
  type: "info" | "warning" | "error" | "success";
  category: NotificationCategory;
  priority: NotificationPriority;
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  acknowledged: boolean;
  snoozedUntil: number | null;
  sourceWorkspace?: WorkspaceId;
}

const ALL_WORKSPACES: WorkspaceId[] = [
  "workspace", "executives", "operations", "knowledge",
  "projects", "creator", "trading", "console",
  "communications", "intelligence", "content-hub", "integrations",
  "collaboration",
];

function initWorkspaceStates(): Record<WorkspaceId, WorkspaceState> {
  const states = {} as Record<WorkspaceId, WorkspaceState>;
  for (const id of ALL_WORKSPACES) {
    states[id] = defaultWorkspaceState();
  }
  return states;
}

export const useAxiomStore = create<AxiomState>((set) => ({
  runtime: null,
  health: null,
  executiveBoard: null,
  commandPaletteOpen: false,
  sidePanel: "none",
  activeView: "workspace",
  activeWorkstation: "axiom",
  workstationStatus: { axiom: "healthy", bleval: "healthy", valta: "healthy", personal: "healthy" },
  activeWorkstationView: "workspace",
  sidebarCollapsed: false,
  workspaceStates: initWorkspaceStates(),
  selectedExecutive: null,
  executiveMeetingActive: false,
  currentSpeaker: null,
  voiceActive: false,
  isListening: false,
  isSpeaking: false,
  isAwake: false,
  pendingVoiceCommand: null,
  voiceWakeTimeout: null,
  listeningExecutive: null,
  notifications: [],
  notificationPanelOpen: false,

  // Phase F — Board Room initial state
  boardMeetings: [],
  boardActiveMeeting: null,
  boardKpis: {},
  boardActionItems: null,

  // Phase F — Founder availability initial state
  founderAvailability: "unknown" as FounderAvailability,
  founderManualOverride: null,
  founderLastActive: Date.now(),

  // Phase F — Emergency initial state
  emergencyActive: false,
  emergencySource: null,
  emergencyLevel: null,

  // Phase F — Speaker initial state
  activeSpeaker: null,

  // Phase G — Learning initial state
  learningStatus: null,
  learningPatterns: [],
  learningRecommendations: [],
  learningKnowledge: [],
  workflowAnalytics: [],
  learningCycles: [],
  performanceScores: [],
  founderModel: {
    decisionPatterns: {},
    approvedFormats: [],
    workingHours: { start: 5, end: 21 },
    preferredOutputs: [],
    communicationStyle: "professional",
    recurringPriorities: [],
    approvedStandards: [],
  },
  qcLearningSignals: [],
  selfHealerStatus: null,
  selectedLearningTab: "overview",

  setRuntime: (r) => set({ runtime: r }),
  setHealth: (h) => set({ health: h }),
  setExecutiveBoard: (b) => set({ executiveBoard: b }),
  toggleCommandPalette: () =>
    set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  setCommandPalette: (open) => set({ commandPaletteOpen: open }),
  setSidePanel: (panel) => set({ sidePanel: panel }),
  setActiveView: (view) => set({ activeView: view }),
  setActiveWorkstation: (ws) => set({ activeWorkstation: ws }),
  setWorkstationStatus: (ws, status) => set((s) => ({ workstationStatus: { ...s.workstationStatus, [ws]: status } })),
  setActiveWorkstationView: (view) => set({ activeWorkstationView: view, activeView: view }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setWorkspaceState: (workspace, state) =>
    set((s) => ({
      workspaceStates: {
        ...s.workspaceStates,
        [workspace]: { ...s.workspaceStates[workspace], ...state },
      },
    })),
  setSelectedExecutive: (id) => set({ selectedExecutive: id }),
  setExecutiveMeetingActive: (active) => set({ executiveMeetingActive: active }),
  setCurrentSpeaker: (speaker) => set({ currentSpeaker: speaker }),
  setVoiceActive: (active) => set({ voiceActive: active }),
  setIsListening: (listening) => set({ isListening: listening }),
  setIsSpeaking: (speaking) => set({ isSpeaking: speaking }),
  setIsAwake: (awake) => set({ isAwake: awake }),
  setPendingVoiceCommand: (cmd) => set({ pendingVoiceCommand: cmd }),
  setVoiceWakeTimeout: (id) => set({ voiceWakeTimeout: id }),
  setListeningExecutive: (exec) => set({ listeningExecutive: exec }),
  addNotification: (n) =>
    set((s) => ({
      notifications: [{
        ...n,
        category: (n as EnhancedNotification).category || "runtime",
        priority: (n as EnhancedNotification).priority || "normal",
        acknowledged: (n as EnhancedNotification).acknowledged ?? false,
        snoozedUntil: (n as EnhancedNotification).snoozedUntil ?? null,
      }, ...s.notifications],
    })),
  dismissNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
    })),
  setNotificationPanelOpen: (open) => set({ notificationPanelOpen: open }),
  toggleNotificationPanel: () => set((s) => ({ notificationPanelOpen: !s.notificationPanelOpen })),
  snoozeNotification: (id, until) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, snoozedUntil: until } : n,
      ),
    })),
  acknowledgeNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, acknowledged: true, read: true } : n,
      ),
    })),
  clearNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
    })),
  clearAllNotifications: () => set({ notifications: [] }),
  addSystemNotification: (n) =>
    set((s) => ({
      notifications: [{
        ...n,
        id: `notif-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        timestamp: Date.now(),
        read: false,
        acknowledged: false,
        snoozedUntil: null,
      }, ...s.notifications],
    })),

  // Phase F — Board Room actions
  setBoardMeetings: (meetings) => set({ boardMeetings: meetings }),
  setBoardActiveMeeting: (meeting) => set({ boardActiveMeeting: meeting }),
  setBoardKpis: (kpis) => set({ boardKpis: kpis }),
  setBoardActionItems: (items) => set({ boardActionItems: items }),

  // Phase F — Founder availability actions
  setFounderAvailability: (availability) => set({ founderAvailability: availability }),
  setFounderManualOverride: (override) => set({ founderManualOverride: override }),
  setFounderLastActive: (timestamp) => set({ founderLastActive: timestamp }),

  // Phase F — Emergency actions
  setEmergencyActive: (active) => set({ emergencyActive: active }),
  setEmergencySource: (source) => set({ emergencySource: source }),
  setEmergencyLevel: (level) => set({ emergencyLevel: level }),
  clearEmergency: () => set({ emergencyActive: false, emergencySource: null, emergencyLevel: null }),

  // Phase F — Speaker actions
  setActiveSpeaker: (speaker) => set({ activeSpeaker: speaker }),

  // Phase G — Learning actions
  setLearningStatus: (s) => set({ learningStatus: s }),
  setLearningPatterns: (p) => set({ learningPatterns: p }),
  setLearningRecommendations: (r) => set({ learningRecommendations: r }),
  setLearningKnowledge: (k) => set({ learningKnowledge: k }),
  setWorkflowAnalytics: (a) => set({ workflowAnalytics: a }),
  setLearningCycles: (c) => set({ learningCycles: c }),
  setPerformanceScores: (s) => set({ performanceScores: s }),
  setFounderModel: (m) =>
    set((s) => ({ founderModel: { ...s.founderModel, ...m } })),
  setQCLearningSignals: (sigs) => set({ qcLearningSignals: sigs }),
  setSelfHealerStatus: (st) => set({ selfHealerStatus: st }),
  setSelectedLearningTab: (tab) => set({ selectedLearningTab: tab }),
}));