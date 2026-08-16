"use client";

import { useAxiomStore } from "../../../lib/store/axiom-store";
import { cn } from "../../../lib/utils";

export default function AXIOMWS() {
  const { isAwake, isListening, voiceActive } = useAxiomStore();

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[var(--axiom-bg-base)]">
      {/* Minimal Voice Status Bar - subtle top indicator */}
      <div className="h-6 bg-[var(--axiom-bg-surface)]/50 backdrop-blur-sm border-b border-[var(--axiom-border)]/30 flex items-center justify-end px-4 gap-2">
        <div className="flex items-center gap-2">
          <div className={cn(
            "w-1.5 h-1.5 rounded-full transition-colors duration-200",
            isListening ? "bg-[var(--axiom-success)] animate-pulse" :
            isAwake ? "bg-[var(--axiom-accent)] animate-pulse" :
            voiceActive ? "bg-[var(--axiom-accent)]" :
            "bg-[var(--axiom-text-tertiary)]"
          )} />
          <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)]">
            {isListening ? "LISTENING" : isAwake ? "AWAKE" : voiceActive ? "READY" : "OFFLINE"}
          </span>
        </div>
      </div>

      {/* Empty Workspace — Intentional */}
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center px-8">
          <div className="mx-auto max-w-xl opacity-30">
            <h1 className="text-3xl md:text-4xl font-light text-[var(--axiom-text-primary)] tracking-tight mb-2">
              AXIOM
            </h1>
            <p className="text-[var(--axiom-text-tertiary)] text-base">
              Chief Orchestration Intelligence
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}