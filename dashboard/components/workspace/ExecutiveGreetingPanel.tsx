"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";
import { executiveIntelligence } from "../../lib/api";

type ExecutiveId = "jenson" | "valta_prime" | "yamako";

interface ExecutiveGreeting {
  exec_id: string;
  greeting: string;
  timestamp: string;
  context?: {
    cycle_count?: number;
    last_cycle?: string;
    active_workflows?: number;
  };
}

interface ExecutiveBranding {
  name: string;
  shortName: string;
  colorFrom: string;
  colorTo: string;
  org: string;
  icon: React.ReactNode;
}

const EXECUTIVE_BRANDING: Record<ExecutiveId, ExecutiveBranding> = {
  jenson: {
    name: "BLEVAL INC",
    shortName: "Jenson",
    colorFrom: "sky-400",
    colorTo: "blue-600",
    org: "Bleval Inc",
    icon: <span className="text-[7px] font-bold text-white">B</span>,
  },
  valta_prime: {
    name: "HOUSE OF VALTA",
    shortName: "Valta Prime",
    colorFrom: "amber-400",
    colorTo: "amber-600",
    org: "House of Valta",
    icon: <span className="text-[7px] font-bold text-white">V</span>,
  },
  yamako: {
    name: "PERSONAL OPS",
    shortName: "Yamako",
    colorFrom: "violet-400",
    colorTo: "purple-600",
    org: "Personal Operations",
    icon: <span className="text-[7px] font-bold text-white">P</span>,
  },
};

const WORKSTATION_TO_EXEC: Record<string, ExecutiveId> = {
  bleval: "jenson",
  valta: "valta_prime",
  personal: "yamako",
};

export function ExecutiveGreetingPanel() {
  const activeWorkstation = useAxiomStore((s) => s.activeWorkstation);
  const [greeting, setGreeting] = useState<ExecutiveGreeting | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const hasShownRef = useRef<Set<string>>(new Set());
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const execId = WORKSTATION_TO_EXEC[activeWorkstation];
  const branding = execId ? EXECUTIVE_BRANDING[execId] : null;

  // Fetch greeting when workstation changes
  useEffect(() => {
    if (!execId || !branding) {
      setIsVisible(false);
      setGreeting(null);
      return;
    }

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Check if we've already shown a greeting for this workstation in this session
    const alreadyShown = hasShownRef.current.has(activeWorkstation);

    const fetchGreeting = async () => {
      setIsLoading(true);
      try {
        const data = await executiveIntelligence.greeting(execId);
        setGreeting(data);

        // Show greeting: always on first visit, or if it's been a while
        if (!alreadyShown) {
          hasShownRef.current.add(activeWorkstation);
          setIsVisible(true);

          // Auto-hide after 8 seconds
          timeoutRef.current = setTimeout(() => {
            setIsVisible(false);
          }, 8000);
        }
      } catch (error) {
        console.warn(`Failed to fetch greeting for ${execId}:`, error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGreeting();
  }, [activeWorkstation, execId, branding]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (!branding || !greeting || !isVisible) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="fixed top-16 left-1/2 -translate-x-1/2 z-50 max-w-md w-full mx-4 pointer-events-none"
      >
        <motion.div
          className={`glass-panel rounded-2xl p-5 shadow-2xl border ${
            branding.colorFrom
          }/20 backdrop-blur-xl pointer-events-auto`}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ delay: 0.1, duration: 0.25 }}
        >
          {/* Header with executive branding */}
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br from-${branding.colorFrom} to-${branding.colorTo} flex items-center justify-center flex-shrink-0`}>
              {branding.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-medium text-[var(--axiom-text-tertiary)] uppercase tracking-wider">
                {branding.org}
              </p>
              <h3 className="text-sm font-semibold text-[var(--axiom-text-primary)] truncate">
                {branding.shortName}
              </h3>
            </div>
            <button
              onClick={() => setIsVisible(false)}
              className="p-1.5 rounded-lg text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)] hover:bg-[var(--axiom-bg-elevated)] transition-colors flex-shrink-0"
              aria-label="Dismiss greeting"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* Greeting message */}
          <div className="text-sm text-[var(--axiom-text-secondary)] leading-relaxed whitespace-pre-wrap">
            {greeting.greeting}
          </div>

          {/* Context info */}
          {(greeting.context?.cycle_count !== undefined || greeting.context?.active_workflows !== undefined) && (
            <div className="mt-3 pt-3 border-t border-[var(--axiom-border)] flex items-center gap-4 text-[11px] text-[var(--axiom-text-tertiary)]">
              {greeting.context?.cycle_count !== undefined && (
                <span className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  {greeting.context.cycle_count} cycles
                </span>
              )}
              {greeting.context?.active_workflows !== undefined && (
                <span className="flex items-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                    <path d="M8 21h8M12 17v4" />
                  </svg>
                  {greeting.context.active_workflows} active
                </span>
              )}
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default ExecutiveGreetingPanel;