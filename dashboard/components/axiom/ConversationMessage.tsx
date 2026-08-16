"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "./MarkdownRenderer";

interface Message {
  id: string;
  role: "user" | "axiom";
  content: string;
  timestamp: Date;
  thinking?: string;
  toolCalls?: ToolCall[];
  executive?: string;
}

interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: unknown;
  error?: string;
}

interface ToolCallResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

interface ConversationMessageProps {
  message: Message;
  isLast: boolean;
}

const EXECUTIVE_CONFIG: Record<string, { label: string; color: string; avatar: string }> = {
  axiom: { label: "AXIOM", color: "from-indigo-400 to-violet-500", avatar: "���" },
  jenson: { label: "JENSON", color: "from-blue-400 to-cyan-500", avatar: "J" },
  valta_prime: { label: "VALTA PRIME", color: "from-amber-400 to-orange-500", avatar: "V" },
  yamako: { label: "YAMAKO", color: "from-violet-400 to-purple-500", avatar: "Y" },
};

export default function ConversationMessage({ message, isLast }: ConversationMessageProps) {
  const execConfig = message.executive ? EXECUTIVE_CONFIG[message.executive] || EXECUTIVE_CONFIG.axiom : EXECUTIVE_CONFIG.axiom;
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 w-full", isUser ? "justify-end" : "")}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
          <div className={cn(
            "w-full h-full rounded-full flex items-center justify-center",
            "bg-gradient-to-br",
            execConfig.color
          )}>
            <span className="text-[11px] font-bold text-white">{execConfig.avatar}</span>
          </div>
        </div>
      )}

      <div className={cn(
        "max-w-[85%] w-full",
        isUser ? "order-2" : "order-1"
      )}>
        <div className={cn(
          isUser
            ? "bg-[var(--axiom-accent)]/10 text-[var(--axiom-text-primary)] rounded-2xl rounded-tr-md px-5 py-3.5 border border-[var(--axiom-accent)]/20"
            : "text-[var(--axiom-text-primary)] px-1 py-2"
        )}>
          {/* Executive label for AXIOM messages */}
          {!isUser && message.executive && (
            <div className="flex items-center gap-2 mb-2">
              <span className={cn(
                "text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full",
                "bg-gradient-to-r",
                execConfig.color,
                "text-white"
              )}>
                {execConfig.label}
              </span>
            </div>
          )}

          {/* Message content */}
          <div className={cn(isUser ? "" : "pl-1")}>
            <MarkdownRenderer content={message.content} />
          </div>

          {/* Thinking process */}
          {message.thinking && !isUser && (
            <details className="group mt-3">
              <summary className={cn(
                "flex items-center gap-2 text-[11px] font-mono text-[var(--axiom-text-tertiary)]",
                "cursor-pointer select-none",
                "hover:text-[var(--axiom-text-secondary)]",
                "transition-colors duration-150"
              )}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]/50 group-open:rotate-90 transition-transform">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
                <span>Thinking process</span>
              </summary>
              <div className="mt-2 p-3 rounded-xl bg-[var(--axiom-bg-elevated)]/50 border border-[var(--axiom-border)]/30 ml-1">
                <pre className="text-[11px] font-mono text-[var(--axiom-text-secondary)] whitespace-pre-wrap overflow-x-auto">
                  {message.thinking}
                </pre>
              </div>
            </details>
          )}

          {/* Tool calls */}
          {message.toolCalls && message.toolCalls.length > 0 && !isUser && (
            <div className="mt-3 space-y-2 ml-1">
              {message.toolCalls.map((tool, i) => (
                <ToolCallDisplay key={i} tool={tool} />
              ))}
            </div>
          )}

          {/* Timestamp */}
          <div className="flex items-center gap-2 mt-2" style={{ opacity: isLast ? 1 : 0.5 }}>
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: isLast ? 1 : 0.5, scale: 1 }}
              transition={{ duration: 0.2 }}
              className="text-[10px] font-mono text-[var(--axiom-text-tertiary)]"
            >
              {message.timestamp.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
            </motion.span>
            {!isUser && isLast && (
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--axiom-accent)] animate-pulse" />
            )}
          </div>
        </div>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-10 h-10 rounded-full border border-[var(--axiom-border)] flex items-center justify-center flex-shrink-0 mt-0.5 bg-[var(--axiom-bg-elevated)]">
          <span className="text-[11px] font-medium text-[var(--axiom-text-secondary)]">F</span>
        </div>
      )}
    </div>
  );
}

function ToolCallDisplay({ tool }: { tool: ToolCall }) {
  const hasResult = tool.result !== undefined && tool.result !== null;
  const resultAsAny = tool.result as Record<string, unknown> | unknown;

  return (
    <div className="rounded-xl bg-[var(--axiom-bg-elevated)]/50 border border-[var(--axiom-border)]/30 overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-[var(--axiom-bg-surface)]/50 border-b border-[var(--axiom-border)]/20">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)]">
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <path d="M8 21h8M12 17v4" />
        </svg>
        <span className="text-[11px] font-medium text-[var(--axiom-text-primary)]">{tool.name}</span>
        <span className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] px-2 py-0.5 rounded bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]">
          {hasResult ? "completed" : "running"}
        </span>
      </div>
      <div className="p-3">
        <details className="w-full">
          <summary className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] cursor-pointer hover:text-[var(--axiom-text-secondary)] mb-1">
            Arguments
          </summary>
          <pre className="mt-1 text-[10px] font-mono text-[var(--axiom-text-secondary)] whitespace-pre-wrap overflow-x-auto max-h-40 overflow-y-auto">
            {JSON.stringify(tool.args, null, 2)}
          </pre>
        </details>
        {hasResult && (
          <details className="w-full mt-2">
            <summary className="text-[10px] font-mono text-[var(--axiom-text-tertiary)] cursor-pointer hover:text-[var(--axiom-text-secondary)] mb-1">
              Result
            </summary>
            <pre className="mt-1 text-[10px] font-mono text-[var(--axiom-text-secondary)] whitespace-pre-wrap overflow-x-auto max-h-60 overflow-y-auto">
              {JSON.stringify(resultAsAny, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}