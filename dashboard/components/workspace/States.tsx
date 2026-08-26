"use client";

import type { ReactNode } from "react";

/* Empty State */

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

export function EmptyState({ icon, title, description, action, className = "" }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-10 text-center ${className}`}>
      {icon || (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-tertiary)] mb-3">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4" />
          <path d="M12 16h0" />
        </svg>
      )}
      <p className="text-sm font-medium text-[var(--axiom-text-primary)] mt-3">{title}</p>
      {description && <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1 max-w-xs">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-4 py-1.5 text-xs font-medium text-[var(--axiom-accent)] border border-[var(--axiom-border)] rounded-md hover:bg-[var(--axiom-bg-elevated)] transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

/* Error State */

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
  className?: string;
}

export function ErrorState({ message, onRetry, className = "" }: ErrorStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-10 text-center ${className}`}>
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-error)] mb-3">
        <circle cx="12" cy="12" r="10" />
        <path d="m15 9-6 6" />
        <path d="m9 9 6 6" />
      </svg>
      <p className="text-sm font-medium text-[var(--axiom-text-primary)] mb-1">Connection Error</p>
      <p className="text-xs text-[var(--axiom-text-tertiary)] mb-4 max-w-xs">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 rounded-md text-xs font-medium bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors"
      >
        Retry
      </button>
    </div>
  );
}

/* Offline State */

interface OfflineStateProps {
  lastCheck?: string;
  onRetry: () => void;
}

export function OfflineState({ lastCheck, onRetry }: OfflineStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--axiom-text-tertiary)] mb-3">
        <path d="M4.22 4.22A17.9 17.9 0 0 1 12 2c4.2 0 8 1.5 10.78 4.22" />
        <path d="M1 1l22 22" />
        <path d="M8.76 8.76A12.9 12.9 0 0 1 12 8c3.2 0 6.1 1.1 8.36 3.02" />
        <path d="M12 16c.7 0 1.37.08 2.02.23" />
        <path d="M18.36 14.64A8.9 8.9 0 0 0 12 13a9 9 0 0 0-2.02.25" />
        <line x1="12" y1="20" x2="12.01" y2="20" />
      </svg>
      <p className="text-sm font-medium text-[var(--axiom-text-primary)] mt-3">System Offline</p>
      <p className="text-xs text-[var(--axiom-text-tertiary)] mt-1">Unable to connect to AXIOM runtime.</p>
      {lastCheck && <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-2 font-mono">Last check: {lastCheck}</p>}
      <button
        onClick={onRetry}
        className="mt-4 px-4 py-2 rounded-md text-xs font-medium bg-[var(--axiom-accent)] text-white hover:bg-[var(--axiom-accent-hover)] transition-colors"
      >
        Reconnect
      </button>
    </div>
  );
}