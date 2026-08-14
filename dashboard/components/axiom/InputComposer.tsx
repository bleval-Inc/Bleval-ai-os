"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface InputComposerProps {
  input: string;
  setInput: (value: string) => void;
  onSend: (text?: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  isProcessing: boolean;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  voiceActive: boolean;
}

export default function InputComposer({
  input,
  setInput,
  onSend,
  onKeyDown,
  isProcessing,
  inputRef,
  voiceActive,
}: InputComposerProps) {
  const [isComposing, setIsComposing] = useState(false);
  const [showAttachments, setShowAttachments] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current || inputRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      const newHeight = Math.min(textarea.scrollHeight, 200);
      textarea.style.height = `${newHeight}px`;
    }
  }, [input, inputRef]);

  const handleTextareaKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      onKeyDown(e);
    },
    [onKeyDown]
  );

  const handleSend = useCallback(() => {
    if (input.trim() && !isProcessing) {
      onSend(input);
    }
  }, [input, isProcessing, onSend]);

  const handlePaste = useCallback(
    (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
      const text = e.clipboardData.getData("text");
      // Allow pasting, will trigger auto-resize
    },
    []
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // For now, just log - real implementation would upload and reference
      Array.from(files).forEach((file) => {
        console.log("Attachment:", file.name, file.type, file.size);
      });
      // Clear input so same file can be selected again
      e.target.value = "";
    }
  };

  return (
    <div className="p-4 md:p-6">
      <div className="max-w-4xl md:max-w-5xl lg:max-w-6xl mx-auto">
        {/* Attachments preview */}
        <AnimatePresence>
          {showAttachments && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-3 flex flex-wrap gap-2"
            >
              {/* Placeholder for actual attachments */}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main input row */}
        <div className="flex items-end gap-3">
          {/* Attachment button */}
          <button
            type="button"
            onClick={() => {
              fileInputRef.current?.click();
            }}
            className={cn(
              "p-2.5 rounded-xl flex items-center justify-center flex-shrink-0",
              "bg-[var(--axiom-bg-elevated)]/50 border border-[var(--axiom-border)]/30",
              "hover:bg-[var(--axiom-bg-elevated)] hover:border-[var(--axiom-border)]/50",
              "transition-all duration-200",
              "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-secondary)]"
            )}
            aria-label="Attach files"
            disabled={isProcessing}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.49" />
            </svg>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
          </button>

          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
              }}
              onKeyDown={handleTextareaKeyDown}
              onPaste={handlePaste}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={() => setIsComposing(false)}
              placeholder="Message AXIOM..."
              className={cn(
                "w-full min-h-[56px] max-h-[200px] px-4 py-3 pr-14",
                "bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]/30",
                "rounded-2xl text-[var(--axiom-text-primary)]",
                "placeholder:text-[var(--axiom-text-tertiary)]/50",
                "focus:outline-none focus:border-[var(--axiom-accent)]/50 focus:ring-1 focus:ring-[var(--axiom-accent)]/20",
                "transition-all duration-200",
                "resize-none font-sans text-base leading-relaxed",
                "scrollbar-thin scrollbar-track-transparent scrollbar-thumb-[var(--axiom-border)]/30",
                isProcessing && "opacity-50 pointer-events-none"
              )}
              disabled={isProcessing || isComposing}
              aria-label="Message input"
            />
            {/* Character count / hint */}
            <div className="absolute bottom-1 right-3 text-[10px] font-mono text-[var(--axiom-text-tertiary)]/50 pointer-events-none">
              {input.length > 0 ? `${input.length}` : "Shift+Enter for new line"}
            </div>
          </div>

          {/* Voice button */}
          <button
            type="button"
            className={cn(
              "p-3 rounded-xl flex items-center justify-center flex-shrink-0",
              "transition-all duration-200",
              voiceActive
                ? "bg-gradient-to-br from-[var(--axiom-accent)] to-[var(--axiom-accent-secondary)] text-white shadow-[0_0_20px_-5px_rgba(99,102,241,0.5)] animate-pulse"
                : "bg-[var(--axiom-bg-elevated)]/50 border border-[var(--axiom-border)]/30 text-[var(--axiom-text-tertiary)] hover:bg-[var(--axiom-bg-elevated)] hover:border-[var(--axiom-border)]/50 hover:text-[var(--axiom-text-secondary)]"
            )}
            aria-label={voiceActive ? "Voice active - listening" : "Start voice input"}
            disabled={isProcessing}
          >
            {voiceActive ? (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-white">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            )}
          </button>

          {/* Send button */}
          <motion.button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className={cn(
              "p-3 rounded-xl flex items-center justify-center flex-shrink-0",
              "bg-gradient-to-br from-[var(--axiom-accent)] to-[var(--axiom-accent-secondary)]",
              "text-white font-medium",
              "shadow-[0_0_20px_-5px_rgba(99,102,241,0.4)]",
              "transition-all duration-200",
              "disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Send message"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </motion.button>
        </div>

        {/* Keyboard shortcuts hint */}
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-4 text-[11px] font-mono text-[var(--axiom-text-tertiary)]/60">
            <kbd className="px-2 py-0.5 rounded bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]/30">Enter</kbd>
            <span>Send</span>
            <kbd className="px-2 py-0.5 rounded bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]/30">Shift+Enter</kbd>
            <span>New line</span>
            <kbd className="px-2 py-0.5 rounded bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]/30">Cmd+V</kbd>
            <span>Paste as text</span>
          </div>
        </div>
      </div>
    </div>
  );
}