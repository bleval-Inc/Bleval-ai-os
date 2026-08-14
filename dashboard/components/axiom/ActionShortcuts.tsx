"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface Action {
  id: string;
  label: string;
  icon: string;
  description: string;
}

interface ActionShortcutsProps {
  actions: Action[];
  onActionClick: (actionId: string) => void;
}

const ICONS: Record<string, React.ReactNode> = {
  search: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  plus: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  activity: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  play: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  ),
};

const GRADIENTS: Record<string, string> = {
  search: "from-indigo-500 to-blue-500",
  plus: "from-emerald-500 to-teal-500",
  activity: "from-violet-500 to-purple-500",
  play: "from-amber-500 to-orange-500",
};

export default function ActionShortcuts({ actions, onActionClick }: ActionShortcutsProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 md:gap-4 max-w-4xl md:max-w-5xl lg:max-w-6xl w-full px-4">
      {actions.map((action, index) => (
        <motion.button
          key={action.id}
          onClick={() => onActionClick(action.id)}
          className={cn(
            "group relative flex items-center gap-3 px-5 py-3.5 md:px-6 md:py-4",
            "rounded-2xl overflow-hidden",
            "bg-[var(--axiom-bg-surface)]/40 backdrop-blur-sm",
            "border border-[var(--axiom-border)]/30",
            "hover:border-[var(--axiom-accent)]/40",
            "hover:shadow-[0_0_30px_-10px_rgba(99,102,241,0.3)]",
            "transition-all duration-300 ease-out",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--axiom-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--axiom-bg-base)]"
          )}
          whileHover={{ y: -2, scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          style={{
            background: `linear-gradient(135deg, var(--axiom-bg-surface) 0%, var(--axiom-bg-elevated) 100%)`,
          }}
        >
          {/* Accent glow on hover */}
          <motion.div
            className="absolute inset-0 pointer-events-none"
            animate={{
              opacity: 0,
            }}
            whileHover={{
              opacity: 0.15,
            }}
            transition={{ duration: 0.3 }}
            style={{
              background: `linear-gradient(135deg, hsl(var(--axiom-accent-hsl) / 0.2) 0%, transparent 100%)`,
              borderRadius: "inherit",
            }}
          />

          {/* Icon with gradient background */}
          <div className={cn(
            "relative w-11 h-11 md:w-12 md:h-12 rounded-xl flex items-center justify-center flex-shrink-0",
            "bg-gradient-to-br",
            GRADIENTS[action.icon] || "from-indigo-500 to-blue-500",
            "shadow-[0_0_20px_-5px_rgba(99,102,241,0.4)]"
          )}>
            <span className="text-white group-hover:scale-110 transition-transform duration-300">
              {ICONS[action.icon] || ICONS.search}
            </span>
          </div>

          {/* Label & description */}
          <div className="text-left min-w-0">
            <div className="font-medium text-[var(--axiom-text-primary)] text-base md:text-lg tracking-tight">
              {action.label}
            </div>
            <div className="text-[11px] md:text-[12px] text-[var(--axiom-text-tertiary)] font-medium">
              {action.description}
            </div>
          </div>

          {/* Arrow indicator */}
          <motion.div
            className="hidden md:block ml-2 w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--axiom-bg-elevated)]/50 border border-[var(--axiom-border)]/30 opacity-0"
            whileHover={{ opacity: 1, x: 4 }}
            transition={{ duration: 0.2 }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-text-tertiary)]">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </motion.div>

          {/* Bottom accent line */}
          <motion.div
            className="absolute bottom-0 left-0 right-0 h-px"
            animate={{
              scaleX: 0,
              opacity: 0,
            }}
            whileHover={{
              scaleX: 1,
              opacity: 1,
            }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            style={{
              background: `linear-gradient(90deg, transparent, hsl(var(--axiom-accent-hsl) / 0.6), transparent)`,
            }}
          />
        </motion.button>
      ))}
    </div>
  );
}