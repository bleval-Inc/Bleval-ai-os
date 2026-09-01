"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { board as boardApi } from "../../lib/api";
import type {
  BoardMeeting,
  BoardMeetingDetail,
  BoardDashboard,
} from "../../lib/api-types";

// Types

type PanelTab = "meetings" | "kpis" | "actions";

interface KpiCard {
  executive: string;
  metric: string;
  value: number;
  label: string;
}

// Color helpers

const STATUS_COLORS: Record<string, string> = {
  scheduled: "text-amber-400 border-amber-400/30 bg-amber-400/10",
  in_progress: "text-green-400 border-green-400/30 bg-green-400/10",
  completed: "text-blue-400 border-blue-400/30 bg-blue-400/10",
  cancelled: "text-red-400 border-red-400/30 bg-red-400/10",
};

const TYPE_ICONS: Record<string, string> = {
  daily: "📅",
  weekly: "📊",
  monthly: "📈",
  quarterly: "🏆",
  emergency: "🚨",
  one_on_one: "🤝",
  review: "🔍",
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: "text-red-400 border-red-400/30 bg-red-400/10",
  high: "text-orange-400 border-orange-400/30 bg-orange-400/10",
  medium: "text-amber-400 border-amber-400/30 bg-amber-400/10",
  low: "text-blue-400 border-blue-400/30 bg-blue-400/10",
};

// BoardRoomPanel

export default function BoardRoomPanel() {
  const [activeTab, setActiveTab] = useState<PanelTab>("meetings");
  const [meetings, setMeetings] = useState<BoardMeeting[]>([]);
  const [activeMeeting, setActiveMeeting] = useState<BoardMeetingDetail | null>(null);
  const [kpiData, setKpiData] = useState<KpiCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helpers
  function formatMetricLabel(key: string): string {
    return key
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  // Data Fetching
  const fetchData = useCallback(async () => {
    try {
      const [dash, mList, kpiRes] = await Promise.all([
        boardApi.dashboard().catch(() => null),
        boardApi.meetings().catch(() => []),
        boardApi.kpis().catch(() => ({})),
      ]);

      if (dash) {
        const meetingDetail = (dash as BoardDashboard).active_meeting ?? null;
        setActiveMeeting(meetingDetail ? (meetingDetail as unknown as BoardMeetingDetail) : null);
      }

      const meetingsList = mList as BoardMeeting[];
      setMeetings(Array.isArray(meetingsList) ? meetingsList : []);

      // Flatten KPIs into cards
      const kpiRecord = kpiRes as Record<string, Record<string, number>>;
      if (kpiRecord && typeof kpiRecord === "object") {
        const cards: KpiCard[] = [];
        for (const [exec, metrics] of Object.entries(kpiRecord)) {
          if (metrics && typeof metrics === "object") {
            for (const [metric, value] of Object.entries(metrics)) {
              cards.push({
                executive: exec,
                metric,
                value: value as number,
                label: formatMetricLabel(metric),
              });
            }
          }
        }
        setKpiData(cards);
      }

      setError(null);
    } catch {
      setError("Failed to load Board Room data");
    } finally {
      setLoading(false);
    }
  }, []);

  // Polling
  useEffect(() => {
    // Initial data fetch
    fetchData();

    // Set up polling interval for subsequent updates
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  function formatTimestamp(ts: string | number | undefined): string {
    if (!ts) return "—";
    const d = typeof ts === "number" ? new Date(ts) : new Date(ts);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function getExecutiveColor(exec: string): string {
    const colors: Record<string, string> = {
      axiom: "text-indigo-400",
      jenson: "text-blue-400",
      valta_prime: "text-amber-400",
      yamako: "text-violet-400",
    };
    return colors[exec.toLowerCase()] ?? "text-gray-400";
  }

  // RENDER
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          <span className="text-xs text-[var(--axiom-text-tertiary)]">Loading Board Room...</span>
        </div>
      </div>
    );
  }

  if (error && meetings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <span className="text-3xl">🏛️</span>
        <p className="text-xs text-red-400">{error}</p>
        <button onClick={fetchData} className="px-3 py-1 text-[10px] font-medium text-white bg-indigo-500/20 border border-indigo-500/30 rounded-md hover:bg-indigo-500/30 transition-colors">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--axiom-border)]">
        <div className="flex items-center gap-2.5">
          <span className="text-sm">🏛️</span>
          <h2 className="text-xs font-semibold text-[var(--axiom-text-primary)]">Board Room</h2>
        </div>

        {/* Active meeting indicator */}
        {activeMeeting && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-medium text-green-400 bg-green-400/10 border border-green-400/20 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Meeting in progress
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--axiom-border)]">
        {([
          { id: "meetings" as PanelTab, label: "Meetings", icon: "📅" },
          { id: "kpis" as PanelTab, label: "KPIs", icon: "📊" },
          { id: "actions" as PanelTab, label: "Actions", icon: "✅" },
        ]).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3.5 py-2 text-[10px] font-medium transition-colors relative ${
              activeTab === tab.id
                ? "text-indigo-400"
                : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            }`}
          >
            <span className="text-[11px]">{tab.icon}</span>
            {tab.label}
            {activeTab === tab.id && (
              <motion.div
                layoutId="board-tab-underline"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-400"
              />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scroll-smooth">
        {activeTab === "meetings" && (
          <MeetingsTab
            meetings={meetings}
            activeMeeting={activeMeeting}
            getExecutiveColor={getExecutiveColor}
            formatTimestamp={formatTimestamp}
          />
        )}
        {activeTab === "kpis" && (
          <KpisTab kpiData={kpiData} getExecutiveColor={getExecutiveColor} />
        )}
        {activeTab === "actions" && (
          <ActionsTab />
        )}
      </div>
    </div>
  );
}

// Meetings Tab

function MeetingsTab({
  meetings,
  activeMeeting,
  getExecutiveColor,
  formatTimestamp,
}: {
  meetings: BoardMeeting[];
  activeMeeting: BoardMeetingDetail | null;
  getExecutiveColor: (exec: string) => string;
  formatTimestamp: (ts: string | number | undefined) => string;
}) {
  // Show active meeting first
  const sortedMeetings = [...meetings].sort((a, b) => {
    if (a.status === "in_progress") return -1;
    if (b.status === "in_progress") return 1;
    return 0;
  });

  return (
    <div className="p-3 space-y-2">
      {/* Active Meeting Banner */}
      {activeMeeting && (
        <div className="glass-panel p-3 border border-green-400/20">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <h3 className="text-xs font-semibold text-[var(--axiom-text-primary)]">
                {activeMeeting.title || "Active Meeting"}
              </h3>
            </div>
            <span className={getExecutiveColor(activeMeeting.called_by || "")}>
              {activeMeeting.called_by}
            </span>
          </div>

          {/* Agenda */}
          {activeMeeting.agenda && activeMeeting.agenda.length > 0 && (
            <div className="mt-2">
              <p className="text-[9px] font-medium text-[var(--axiom-text-tertiary)] mb-1 uppercase tracking-wider">Agenda</p>
              <div className="space-y-1">
                {activeMeeting.agenda.map((item, i) => (
                  <div key={i} className="flex items-start gap-2 px-2 py-1 text-[10px] bg-white/5 rounded-md">
                    <span className={`flex-shrink-0 w-3.5 h-3.5 rounded-full flex items-center justify-center ${
                      item.status === "complete" ? "bg-green-500/20 text-green-400" :
                      item.status === "in_progress" ? "bg-amber-500/20 text-amber-400" :
                      "bg-white/10 text-[var(--axiom-text-tertiary)]"
                    }`}>
                      {item.status === "complete" ? "✓" : item.status === "in_progress" ? "●" : `${i + 1}`}
                    </span>
                    <span className="text-[var(--axiom-text-secondary)]">{item.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Decisions */}
          {activeMeeting.decisions && activeMeeting.decisions.length > 0 && (
            <div className="mt-2">
              <p className="text-[9px] font-medium text-[var(--axiom-text-tertiary)] mb-1 uppercase tracking-wider">Decisions</p>
              <div className="space-y-1">
                {activeMeeting.decisions.map((d, i) => (
                  <div key={i} className="px-2 py-1 text-[10px] bg-indigo-500/5 border border-indigo-500/10 rounded-md text-[var(--axiom-text-secondary)]">
                    <span className={getExecutiveColor(d.proposed_by || "")}>@{d.proposed_by}: </span>
                    {d.title || d.description}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Items */}
          {activeMeeting.action_items && activeMeeting.action_items.length > 0 && (
            <div className="mt-2">
              <p className="text-[9px] font-medium text-[var(--axiom-text-tertiary)] mb-1 uppercase tracking-wider">Action Items</p>
              <div className="space-y-1">
                {activeMeeting.action_items.map((ai, i) => (
                  <div key={i} className="flex items-center gap-2 px-2 py-1 text-[10px] bg-white/5 rounded-md">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      ai.priority === "critical" ? "bg-red-400" :
                      ai.priority === "high" ? "bg-amber-400" : "bg-blue-400"
                    }`} />
                    <span className="text-[var(--axiom-text-secondary)] flex-1">{ai.title}</span>
                    <span className={getExecutiveColor(ai.assigned_to || "")}>{ai.assigned_to}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Meeting List */}
      {sortedMeetings.filter((m) => m.status !== "in_progress" || !activeMeeting).length === 0 && !activeMeeting ? (
        <div className="flex flex-col items-center justify-center py-12 gap-2">
          <span className="text-3xl opacity-30">📅</span>
          <p className="text-xs text-[var(--axiom-text-tertiary)]">No meetings scheduled</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {sortedMeetings.map((meeting) => (
            <MeetingCard
              key={meeting.meeting_id}
              meeting={meeting}
              getExecutiveColor={getExecutiveColor}
              formatTimestamp={formatTimestamp}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function MeetingCard({
  meeting,
  getExecutiveColor,
  formatTimestamp,
}: {
  meeting: BoardMeeting;
  getExecutiveColor: (exec: string) => string;
  formatTimestamp: (ts: string | number | undefined) => string;
}) {
  const typeIcon = TYPE_ICONS[meeting.meeting_type || ""] ?? "📋";
  const statusColor = STATUS_COLORS[meeting.status || "scheduled"];

  return (
    <div className="glass-panel p-2.5 flex items-center gap-3">
      <span className="text-sm">{typeIcon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium text-[var(--axiom-text-primary)] truncate">
            {meeting.title || meeting.meeting_type || "Untitled"}
          </span>
          <span className={`px-1.5 py-0.5 text-[8px] font-medium border rounded-full ${statusColor}`}>
            {meeting.status?.replace(/_/g, " ")}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-0.5 text-[9px] text-[var(--axiom-text-tertiary)]">
          {meeting.called_by && (
            <span className={getExecutiveColor(meeting.called_by)}>Called by: {meeting.called_by}</span>
          )}
          {meeting.scheduled_at && (
            <span>{formatTimestamp(meeting.scheduled_at)}</span>
          )}
          {meeting.attendees && meeting.attendees.length > 0 && (
            <span>{meeting.attendees.length} attendee{meeting.attendees.length > 1 ? "s" : ""}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// KPIs Tab

function KpisTab({
  kpiData,
  getExecutiveColor,
}: {
  kpiData: KpiCard[];
  getExecutiveColor: (exec: string) => string;
}) {
  // Group KPIs by executive
  const grouped = kpiData.reduce(
    (acc, card) => {
      if (!acc[card.executive]) acc[card.executive] = [];
      acc[card.executive].push(card);
      return acc;
    },
    {} as Record<string, KpiCard[]>,
  );

  const execs = Object.keys(grouped);

  return (
    <div className="p-3 space-y-3">
      {execs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 gap-2">
          <span className="text-3xl opacity-30">📊</span>
          <p className="text-xs text-[var(--axiom-text-tertiary)]">No KPIs available</p>
          <p className="text-[9px] text-[var(--axiom-text-tertiary)] opacity-60">KPIs are published during Board Room meetings</p>
        </div>
      ) : (
        execs.map((exec) => (
          <div key={exec} className="glass-panel p-3">
            <h3 className={`text-[11px] font-semibold mb-2 ${getExecutiveColor(exec)}`}>
              {exec === "valta_prime" ? "Valta Prime" : exec.charAt(0).toUpperCase() + exec.slice(1)}
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {grouped[exec].map((card, i) => (
                <div key={i} className="px-2.5 py-2 bg-white/5 rounded-md">
                  <p className="text-[18px] font-bold text-[var(--axiom-text-primary)]">
                    {typeof card.value === "number"
                      ? card.value.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })
                      : card.value}
                  </p>
                  <p className="text-[9px] text-[var(--axiom-text-tertiary)] truncate">{card.label}</p>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// Actions Tab

import type { BoardActionItemsResponse } from "../../lib/api-types";

function ActionsTab() {
  const [actions, setActions] = useState<BoardActionItemsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await boardApi.actionItems();
        setActions(res as BoardActionItemsResponse);
      } catch {
        // silently fail
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <span className="text-[11px] text-[var(--axiom-text-tertiary)]">Loading action items...</span>
      </div>
    );
  }

  const overdue = actions?.overdue ?? [];
  const open = actions?.open ?? [];

  return (
    <div className="p-3 space-y-3">
      {/* Overdue Section */}
      {overdue.length > 0 && (
        <div>
          <h3 className="text-[10px] font-medium text-red-400 mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            Overdue ({overdue.length})
          </h3>
          <div className="space-y-1.5">
            {overdue.map((item, i) => (
              <ActionItemCard key={i} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* Open Section */}
      {open.length > 0 && (
        <div>
          <h3 className="text-[10px] font-medium text-[var(--axiom-text-secondary)] mb-2">
            Open ({open.length})
          </h3>
          <div className="space-y-1.5">
            {open.map((item, i) => (
              <ActionItemCard key={i} item={item} />
            ))}
          </div>
        </div>
      )}

      {overdue.length === 0 && open.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 gap-2">
          <span className="text-3xl opacity-30">✅</span>
          <p className="text-xs text-[var(--axiom-text-tertiary)]">All action items complete</p>
        </div>
      )}
    </div>
  );
}

function ActionItemCard({ item }: { item: BoardActionItemsResponse["open"][0] | BoardActionItemsResponse["overdue"][0] }) {
  const priorityColor = PRIORITY_COLORS[item.priority || "medium"];

  return (
    <div className="glass-panel p-2.5 flex items-start gap-2.5">
      <div className={`w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0 ${
        item.priority === "critical" ? "bg-red-400" :
        item.priority === "high" ? "bg-amber-400" :
        "bg-blue-400"
      }`} />
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-[var(--axiom-text-primary)]">{item.title}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className={`px-1.5 py-0.5 text-[8px] font-medium border rounded-full ${priorityColor}`}>
            {item.priority || "medium"}
          </span>
          <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
            @{item.assigned_to || "unassigned"}
          </span>
          {item.deadline && (
            <span className="text-[9px] text-[var(--axiom-text-tertiary)]">
              Due: {new Date(item.deadline).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}