/* Reusable skeleton loaders for Phase 8D */

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div
      className={`glass-card p-4 animate-shimmer bg-gradient-to-r from-[var(--axiom-bg-surface)] via-[var(--axiom-bg-elevated)] to-[var(--axiom-bg-surface)] bg-[length:200%_100%] ${className}`}
    >
      <div className="space-y-3">
        <div className="h-4 w-1/2 rounded bg-[var(--axiom-bg-elevated)]" />
        <div className="h-3 w-3/4 rounded bg-[var(--axiom-bg-elevated)]" />
        <div className="h-3 w-1/3 rounded bg-[var(--axiom-bg-elevated)]" />
      </div>
    </div>
  );
}

export function SkeletonRow({ className = "" }: { className?: string }) {
  return (
    <div
      className={`flex items-center gap-3 px-3 py-2.5 animate-shimmer bg-gradient-to-r from-transparent via-[var(--axiom-bg-elevated)] to-transparent bg-[length:200%_100%] ${className}`}
    >
      <div className="w-2 h-2 rounded-full bg-[var(--axiom-bg-elevated)]" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 w-2/3 rounded bg-[var(--axiom-bg-elevated)]" />
        <div className="h-2.5 w-1/3 rounded bg-[var(--axiom-bg-elevated)]" />
      </div>
    </div>
  );
}

export function SkeletonStat({ className = "" }: { className?: string }) {
  return (
    <div
      className={`rounded-lg border border-[var(--axiom-border)] p-4 animate-shimmer bg-gradient-to-r from-[var(--axiom-bg-surface)] via-[var(--axiom-bg-elevated)] to-[var(--axiom-bg-surface)] bg-[length:200%_100%] ${className}`}
    >
      <div className="h-3 w-1/2 rounded bg-[var(--axiom-bg-elevated)] mb-2" />
      <div className="h-6 w-1/4 rounded bg-[var(--axiom-bg-elevated)]" />
    </div>
  );
}

export function CommandCenterSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-6 max-w-5xl mx-auto">
      <div className="lg:col-span-2">
        <SkeletonCard className="h-32" />
      </div>
      <SkeletonCard className="h-48" />
      <SkeletonCard className="h-48" />
      <SkeletonCard className="h-40" />
      <SkeletonCard className="h-40" />
      <div className="lg:col-span-2">
        <SkeletonCard className="h-36" />
      </div>
    </div>
  );
}