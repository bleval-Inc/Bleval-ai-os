"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../lib/store/axiom-store";

type ExecutiveId = "axiom" | "jenson" | "valta_prime" | "yamako";

const EXECUTIVE_CONFIG: Record<ExecutiveId, {
  label: string;
  color: string;
  avatar: string;
  colorFrom: string;
  colorTo: string;
}> = {
  axiom: {
    label: "AXIOM",
    color: "bg-indigo-400",
    avatar: "A",
    colorFrom: "indigo-400",
    colorTo: "indigo-600",
  },
  jenson: {
    label: "Jenson",
    color: "bg-blue-500",
    avatar: "J",
    colorFrom: "sky-400",
    colorTo: "blue-600",
  },
  valta_prime: {
    label: "Valta Prime",
    color: "bg-amber-500",
    avatar: "V",
    colorFrom: "amber-400",
    colorTo: "amber-600",
  },
  yamako: {
    label: "Yamako",
    color: "bg-violet-400",
    avatar: "Y",
    colorFrom: "violet-400",
    colorTo: "purple-600",
  },
};

interface ListeningIndicatorProps {
  /** The executive to show indicator for, or "auto" to show whoever is listening */
  executive?: ExecutiveId | "auto";
  /** Size of the indicator */
  size?: "sm" | "md" | "lg";
  /** Show label */
  showLabel?: boolean;
  /** Position style */
  position?: "fixed" | "absolute" | "relative";
  /** Custom className */
  className?: string;
}

export function ListeningIndicator({
  executive = "auto",
  size = "md",
  showLabel = true,
  position = "relative",
  className = "",
}: ListeningIndicatorProps) {
  const listeningExecutive = useAxiomStore((s) => s.listeningExecutive);
  const isListening = useAxiomStore((s) => s.isListening);
  const isAwake = useAxiomStore((s) => s.isAwake);

  // Determine which executive to show
  const currentExec = executive === "auto" ? (listeningExecutive as ExecutiveId | null) : executive;
  const config = currentExec ? EXECUTIVE_CONFIG[currentExec] : null;

  // Only show if we're actually listening/awake and have an executive
  if (!isListening || !isAwake || !config) {
    return null;
  }

  const sizeClasses = {
    sm: "w-8 h-8 text-[10px] px-2 py-1 gap-1.5",
    md: "w-10 h-10 text-[12px] px-3 py-2 gap-2",
    lg: "w-12 h-12 text-[14px] px-4 py-2.5 gap-2.5",
  };

  const labelClasses = {
    sm: "text-[10px]",
    md: "text-[11px]",
    lg: "text-sm",
  };

  const positionClasses = {
    fixed: "fixed top-16 right-6 z-50",
    absolute: "absolute top-4 right-4 z-20",
    relative: "relative",
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.8, y: -10 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className={`${positionClasses[position]} ${className}`}
      >
        <motion.div
          className={`flex items-center ${sizeClasses[size]} glass-panel rounded-full border border-[var(--axiom-border)] shadow-lg backdrop-blur-xl animate-pulse`}
          animate={{
            boxShadow: [
              `0 0 0 0 ${config.colorFrom}`,
              `0 0 20px 5px ${config.colorFrom}/40`,
              `0 0 0 0 ${config.colorFrom}`,
            ],
          }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className={`w-full h-full rounded-full bg-gradient-to-br from-${config.colorFrom} to-${config.colorTo} flex items-center justify-center flex-shrink-0`}>
            <span className={`font-bold text-white ${labelClasses[size]}`}>{config.avatar}</span>
          </div>
          {showLabel && (
            <span className="font-medium text-[var(--axiom-text-primary)] whitespace-nowrap">{config.label} listening…</span>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// Simplified version for inline use in workstation headers
export function InlineListeningIndicator({
  executive,
  className = "",
}: { executive?: ExecutiveId; className?: string }) {
  const listeningExecutive = useAxiomStore((s) => s.listeningExecutive);
  const isListening = useAxiomStore((s) => s.isListening);
  const isAwake = useAxiomStore((s) => s.isAwake);

  const currentExec = executive || (listeningExecutive as ExecutiveId | null);
  const config = currentExec ? EXECUTIVE_CONFIG[currentExec] : null;

  if (!isListening || !isAwake || !config) {
    return null;
  }

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: 1,
        scale: 1,
        boxShadow: [
          `0 0 0 0 ${config.colorFrom}`,
          `0 0 12px 3px ${config.colorFrom}/40`,
          `0 0 0 0 ${config.colorFrom}`,
        ],
      }}
      exit={{ opacity: 0, scale: 0.8 }}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full glass-panel border border-[var(--axiom-border)] animate-pulse ${className}`}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
    >
      <span className={`w-4 h-4 rounded-full bg-gradient-to-br from-${config.colorFrom} to-${config.colorTo} flex items-center justify-center text-[7px] font-bold text-white`}>
        {config.avatar}
      </span>
      <span className="text-[10px] font-medium text-[var(--axiom-text-primary)]">
        {config.label} listening
      </span>
    </motion.span>
  );
}

export default ListeningIndicator;