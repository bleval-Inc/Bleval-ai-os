"use client";

import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type EnhancedNotification } from "../../lib/store/axiom-store";

/* ── Helpers ─────────────────────────────────────────────────────── */

function timeLabel(ts: number): string {
  const diff = Date.now() - ts;
  if (diff < 60000) return "just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
}

function dateGroupLabel(ts: number): string {
  const d = new Date(ts);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

type FilterMode = "all" | "unread" | "urgent";

/* ── Category Icon ────────────────────────────────────────────────── */

function CategoryIcon({ category }: { category: string }) {
  const icons: Record<string, string> = {
    executive: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",
    workflow: "M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2",
    runtime: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
    security: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    learning: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
    integration: "M4 7V4h16v3",
  };
  const colors: Record<string, string> = {
    executive: "text-violet-400",
    workflow: "text-emerald-400",
    runtime: "text-amber-400",
    security: "text-red-400",
    learning: "text-blue-400",
    integration: "text-cyan-400",
  };
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={`flex-shrink-0 ${colors[category] || "text-[var(--axiom-text-tertiary)]"}`}>
      <path d={icons[category] || icons.runtime} />
    </svg>
  );
}

/* ── Priority border color ────────────────────────────────────────── */

function priorityBorder(p: string): string {
  if (p === "urgent") return "border-l-[3px] border-l-red-400";
  if (p === "high") return "border-l-[3px] border-l-amber-400";
  return "";
}

function priorityOpacity(p: string): string {
  if (p === "low") return "opacity-50";
  return "";
}

/* ── Notification Row ─────────────────────────────────────────────── */

function NotificationRow({
  n,
  onAcknowledge,
  onSnooze,
  onDismiss,
  onNavigate,
}: {
  n: EnhancedNotification;
  onAcknowledge: (id: string) => void;
  onSnooze: (id: string) => void;
  onDismiss: (id: string) => void;
  onNavigate: (w?: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.15 }}
      className={`group px-3 py-2 rounded-lg hover:bg-[var(--axiom-bg-elevated)] transition-colors cursor-pointer ${priorityBorder(n.priority)} ${priorityOpacity(n.priority)}`}
      onClick={() => n.sourceWorkspace && onNavigate(n.sourceWorkspace)}
    >
      <div className="flex items-start gap-2">
        <CategoryIcon category={n.category} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className={`text-[11px] font-medium truncate ${n.read ? "text-[var(--axiom-text-tertiary)]" : "text-[var(--axiom-text-primary)]"}`}>
              {n.title}
              {!n.acknowledged && n.priority === "urgent" && (
                <span className="ml-1.5 w-1.5 h-1.5 inline-block rounded-full bg-red-400 align-middle" />
              )}
            </p>
            <span className="text-[9px] text-[var(--axiom-text-tertiary)] flex-shrink-0">{timeLabel(n.timestamp)}</span>
          </div>
          <p className="text-[10px] text-[var(--axiom-text-tertiary)] mt-0.5 line-clamp-2">{n.message}</p>
          <div className="flex items-center gap-2 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
            {!n.acknowledged && (
              <button
                onClick={(e) => { e.stopPropagation(); onAcknowledge(n.id); }}
                className="text-[9px] text-emerald-400 hover:text-emerald-300 font-medium"
              >
                Acknowledge
              </button>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); onSnooze(n.id); }}
              className="text-[9px] text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            >
              Snooze 1h
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDismiss(n.id); }}
              className="text-[9px] text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-error)]"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Main Component ───────────────────────────────────────────────── */

export default function NotificationCenter() {
  const {
    notifications,
    notificationPanelOpen,
    setNotificationPanelOpen,
    acknowledgeNotification,
    snoozeNotification,
    clearNotification,
    clearAllNotifications,
    setActiveView,
  } = useAxiomStore();

  const [filter, setFilter] = useState<FilterMode>("all");

  const now = Date.now();

  const filtered = useMemo(() => {
    return notifications.filter((n) => {
      // Exclude snoozed notifications
      if (n.snoozedUntil && n.snoozedUntil > now) return false;
      if (filter === "unread" && n.read) return false;
      if (filter === "urgent" && n.priority !== "urgent" && n.priority !== "high") return false;
      return true;
    });
  }, [notifications, filter, now]);

  const grouped = useMemo(() => {
    const groups: Record<string, EnhancedNotification[]> = {};
    for (const n of filtered) {
      const label = dateGroupLabel(n.timestamp);
      if (!groups[label]) groups[label] = [];
      groups[label].push(n);
    }
    return groups;
  }, [filtered]);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !n.read && (!n.snoozedUntil || n.snoozedUntil <= now)).length,
    [notifications, now],
  );

  const handleNavigate = useCallback(
    (w?: string) => {
      if (w) setActiveView(w as Parameters<typeof setActiveView>[0]);
      setNotificationPanelOpen(false);
    },
    [setActiveView, setNotificationPanelOpen],
  );

  const handleSnooze = useCallback(
    (id: string) => snoozeNotification(id, Date.now() + 3600000),
    [snoozeNotification],
  );

  const groupKeys = Object.keys(grouped);

  return (
    <AnimatePresence>
      {notificationPanelOpen && (
        <motion.div
          initial={{ opacity: 0, y: -8, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.96 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          className="fixed top-10 right-4 z-[9999] w-[380px] max-h-[480px] glass-panel rounded-xl overflow-hidden shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--axiom-border)]">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Notifications</h3>
              {unreadCount > 0 && (
                <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-medium">
                  {unreadCount}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {notifications.length > 0 && (
                <button
                  onClick={clearAllNotifications}
                  className="text-[9px] text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
                >
                  Clear All
                </button>
              )}
              <button
                onClick={() => setNotificationPanelOpen(false)}
                className="text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 6 6 18" />
                  <path d="m6 6 12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="flex gap-1 px-4 py-2 border-b border-[var(--axiom-border)]">
            {(["all", "unread", "urgent"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 text-[10px] font-medium rounded-md transition-colors capitalize ${
                  filter === f
                    ? "bg-[var(--axiom-accent-subtle)] text-[var(--axiom-accent)]"
                    : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* List */}
          <div className="overflow-y-auto max-h-[360px]">
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)] mb-3">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
                <p className="text-xs text-[var(--axiom-text-tertiary)]">No notifications</p>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {groupKeys.map((label) => (
                  <div key={label}>
                    <p className="text-[9px] text-[var(--axiom-text-tertiary)] font-medium uppercase tracking-wider px-2 pt-2 pb-1">
                      {label}
                    </p>
                    {grouped[label].map((n) => (
                      <NotificationRow
                        key={n.id}
                        n={n}
                        onAcknowledge={acknowledgeNotification}
                        onSnooze={handleSnooze}
                        onDismiss={clearNotification}
                        onNavigate={handleNavigate}
                      />
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}