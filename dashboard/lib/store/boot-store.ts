import { create } from "zustand";

export interface BootStage {
  label: string;
  duration: number;
  completed: boolean;
  failed?: boolean;
}

interface BootState {
  phase: "booting" | "greeting" | "ready";
  bootProgress: number;
  currentStage: number;
  stages: BootStage[];
  greetingText: string;
  runtimeSummary: string;
  advanceStage: () => void;
  setGreeting: (text: string) => void;
  setRuntimeSummary: (text: string) => void;
  completeBoot: () => void;
  transitionToReady: () => void;
}

const BOOT_STAGES: BootStage[] = [
  { label: "Initializing Runtime...", duration: 1200, completed: false },
  { label: "Loading Executive Layer...", duration: 800, completed: false },
  { label: "Loading Memory...", duration: 600, completed: false },
  { label: "Loading Workflow Engine...", duration: 700, completed: false },
  { label: "Loading Intelligence Engine...", duration: 900, completed: false },
  { label: "Loading Event Bus...", duration: 500, completed: false },
  { label: "Loading Tool Engine...", duration: 600, completed: false },
  { label: "Loading Organizations...", duration: 700, completed: false },
  { label: "Synchronizing Runtime...", duration: 800, completed: false },
  { label: "Checking Executive Health...", duration: 600, completed: false },
  { label: "System Ready", duration: 400, completed: false },
];

export const useBootStore = create<BootState>((set) => ({
  phase: "booting",
  bootProgress: 0,
  currentStage: 0,
  stages: BOOT_STAGES,
  greetingText: "",
  runtimeSummary: "",

  advanceStage: () =>
    set((state) => {
      const nextIndex = state.currentStage + 1;
      const updatedStages = state.stages.map((s, i) =>
        i === state.currentStage ? { ...s, completed: true } : s,
      );
      const progress = ((nextIndex) / updatedStages.length) * 100;

      if (nextIndex >= updatedStages.length) {
        return {
          stages: updatedStages,
          bootProgress: 100,
          currentStage: nextIndex,
          phase: "greeting" as const,
        };
      }

      return {
        stages: updatedStages,
        bootProgress: progress,
        currentStage: nextIndex,
      };
    }),

  setGreeting: (text) => set({ greetingText: text }),
  setRuntimeSummary: (text) => set({ runtimeSummary: text }),

  completeBoot: () => set({ phase: "greeting" }),

  transitionToReady: () => set({ phase: "ready" }),
}));