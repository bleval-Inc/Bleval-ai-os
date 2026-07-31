import { create } from "zustand";
import type { RuntimeStatus, ExecutiveBoardStatus, HealthSummary } from "../api-types";

// ── Workspace identifiers ────────────────────────────────────────────
export type WorkspaceId =
  | "workspace"   // 1: Founder
  | "executives"  // 2: Executive Board
  | "operations"  // 3: Operations Center
  | "knowledge"   // 4: Knowledge
  | "projects"    // 5: Projects
  | "creator"     // 6: Creator Studio
  | "trading"     // 7: Trading Terminal
  | "console";    // 8: Founder Console

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

  // Notifications
  notifications: Notification[];

  // Actions
  setRuntime: (r: RuntimeStatus) => void;
  setHealth: (h: HealthSummary) => void;
  setExecutiveBoard: (b: ExecutiveBoardStatus) => void;
  toggleCommandPalette: () => void;
  setCommandPalette: (open: boolean) => void;
  setSidePanel: (panel: "memory" | "files" | "none") => void;
  setActiveView: (view: WorkspaceId) => void;
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
  addNotification: (n: Notification) => void;
  dismissNotification: (id: string) => void;
}

export interface Notification {
  id: string;
  type: "info" | "warning" | "error" | "success";
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
}

const ALL_WORKSPACES: WorkspaceId[] = [
  "workspace", "executives", "operations", "knowledge",
  "projects", "creator", "trading", "console",
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
  notifications: [],

  setRuntime: (r) => set({ runtime: r }),
  setHealth: (h) => set({ health: h }),
  setExecutiveBoard: (b) => set({ executiveBoard: b }),
  toggleCommandPalette: () =>
    set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  setCommandPalette: (open) => set({ commandPaletteOpen: open }),
  setSidePanel: (panel) => set({ sidePanel: panel }),
  setActiveView: (view) => set({ activeView: view }),
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
  addNotification: (n) =>
    set((s) => ({ notifications: [n, ...s.notifications] })),
  dismissNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
    })),
}));