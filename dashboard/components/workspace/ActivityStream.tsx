"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";

interface ActivityEvent {
  id: string;
  type: "executive" | "workflow" | "system" | "notification" | "approval";
  title: string;
  description: string;
  timestamp: number;
  executive?: "axiom" | "jenson" | "valta_prime" | "yamako";
  metadata?: Record<string, unknown>;
}

interface ActivityStreamProps {
  events?: ActivityEvent[];
  maxEvents?: number;
  autoScroll?: boolean;
  className?: string;
}

const EXECUTIVE_COLORS: Record<string, string> = {
  axiom: "indigo",
  jenson: "sky",
  valta_prime: "amber",
  yamako: "violet",
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  executive: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  workflow: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <line x1="10" y1="10" x2="14" y2="10" />
      <line x1="10" y1="14" x2="14" y2="14" />
    </svg>
  ),
  system: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
      <path d="M8 21h8" />
      <path d="M12 17v4" />
    </svg>
  ),
  notification: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  ),
  approval: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
};

export function ActivityStream({
  events = [],
  maxEvents = 20,
  autoScroll = true,
  className = "",
}: ActivityStreamProps) {
  const displayedEvents = events.slice(0, maxEvents);

  const formatTime = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <div className={cn("flex flex-col gap-2 overflow-hidden", className)}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Activity Stream</h3>
        <span className="text-[10px] font-mono text-slate-500">{displayedEvents.length} events</span>
      </div>
      <div className="flex-1 overflow-y-auto pr-1">
        <AnimatePresence>
          {displayedEvents.map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: "auto" }}
              exit={{ opacity: 0, x: 20, height: 0 }}
              transition={{ duration: 0.2, delay: index * 0.02 }}
              className="flex items-start gap-3 px-3 py-2.5 hover:bg-white/2.5 rounded-lg transition-colors"
            >
              {/* Executive/Type Indicator */}
              <div className="flex-shrink-0 mt-0.5">
                {event.executive && (
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center bg-gradient-to-br from-${EXECUTIVE_COLORS[event.executive]}-400 to-${EXECUTIVE_COLORS[event.executive]}-600`}>
                    <span className="text-[8px] font-bold text-white">{event.executive.charAt(0).toUpperCase()}</span>
                  </div>
                )}
                {!event.executive && (
                  <div className="w-6 h-6 rounded-full flex items-center justify-center bg-white/5 border border-white/10">
                    {TYPE_ICONS[event.type]}
                  </div>
                )}
              </div>

              {/* Event Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white truncate">{event.title}</span>
                  <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">{formatTime(event.timestamp)}</span>
                  {event.executive && (
                    <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded bg-${EXECUTIVE_COLORS[event.executive]}-500/20 text-${EXECUTIVE_COLORS[event.executive]}-400 border border-${EXECUTIVE_COLORS[event.executive]}-500/30`}>
                      {event.executive.replace("_", " ")}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-400 mt-0.5 line-clamp-2">{event.description}</p>
                {event.metadata && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {Object.entries(event.metadata).map(([key, value]) => (
                      <span key={key} className="text-[9px] font-mono text-slate-500 bg-white/5 px-1.5 py-0.5 rounded border border-white/5">
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {displayedEvents.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-12 text-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="text-slate-600 mb-3">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <p className="text-sm text-slate-500">No activity yet</p>
            <p className="text-xs text-slate-600 mt-1">Events will appear here as they happen</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Mock data generator for demo
export function generateMockActivity(): ActivityEvent[] {
  const now = Date.now();
  return [
    {
      id: "1",
      type: "executive",
      title: "Jenson completed deployment",
      description: "Deployed v2.4.1 to production. All health checks passing.",
      timestamp: now - 1000 * 60 * 5,
      executive: "jenson",
      metadata: { version: "2.4.1", duration: "2m 34s" },
    },
    {
      id: "2",
      type: "workflow",
      title: "Pipeline completed",
      description: "CI/CD pipeline finished successfully for feature/auth-refactor",
      timestamp: now - 1000 * 60 * 15,
      metadata: { branch: "feature/auth-refactor", commit: "a1b2c3d" },
    },
    {
      id: "3",
      type: "executive",
      title: "Valta Prime flagged market anomaly",
      description: "Detected unusual volume spike in AAPL. Monitoring position limits.",
      timestamp: now - 1000 * 60 * 30,
      executive: "valta_prime",
      metadata: { symbol: "AAPL", volumeRatio: "3.2x" },
    },
    {
      id: "4",
      type: "approval",
      title: "Approval required",
      description: "Valta Prime requests approval for portfolio rebalance",
      timestamp: now - 1000 * 60 * 45,
      executive: "valta_prime",
      metadata: { action: "rebalance", amount: "$125k" },
    },
    {
      id: "5",
      type: "system",
      title: "Scheduled backup completed",
      description: "Nightly database backup finished. 2.4TB archived to cold storage.",
      timestamp: now - 1000 * 60 * 60 * 3,
      metadata: { size: "2.4TB", duration: "47m" },
    },
    {
      id: "6",
      type: "executive",
      title: "Yamako created content brief",
      description: "Generated content calendar for Q4 marketing campaign",
      timestamp: now - 1000 * 60 * 60 * 5,
      executive: "yamako",
      metadata: { campaign: "Q4 Launch", pieces: 12 },
    },
    {
      id: "7",
      type: "workflow",
      title: "Agent task completed",
      description: "Research agent finished competitive analysis for Product team",
      timestamp: now - 1000 * 60 * 60 * 8,
      metadata: { agent: "research-01", pages: 47 },
    },
    {
      id: "8",
      type: "notification",
      title: "System health check",
      description: "All 27 system components reporting healthy. No issues detected.",
      timestamp: now - 1000 * 60 * 60 * 12,
    },
  ];
}

export default ActivityStream;