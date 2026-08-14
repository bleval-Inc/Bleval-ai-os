"use client";

export default function SystemWS() {
  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[var(--axiom-bg-base)]">
      {/* Empty Workspace — Intentional */}
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center px-8">
          <div className="mx-auto max-w-xl opacity-30">
            <h1 className="text-3xl md:text-4xl font-light text-[var(--axiom-text-primary)] tracking-tight mb-2">
              SYSTEM
            </h1>
            <p className="text-[var(--axiom-text-tertiary)] text-base">
              System Monitoring
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}