"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAxiomStore } from "@/lib/store/axiom-store";
import { speak, stopSpeaking } from "@/lib/voice/speak";
import { axiom } from "@/lib/api";
import type { AxiomChatResponse } from "@/lib/api-types";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "@/components/axiom/MarkdownRenderer";
import ConversationMessage from "@/components/axiom/ConversationMessage";
import InputComposer from "@/components/axiom/InputComposer";
import ActionShortcuts from "@/components/axiom/ActionShortcuts";
import ThinkingIndicator from "@/components/axiom/ThinkingIndicator";

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
}

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "axiom",
  content: "What would you like to work on?",
  timestamp: new Date(),
  executive: "axiom",
};

const ACTIONS = [
  { id: "research", label: "Research", icon: "search", description: "Deep research & analysis" },
  { id: "create", label: "Create", icon: "plus", description: "Generate content & code" },
  { id: "analyze", label: "Analyze", icon: "activity", description: "Data & system analysis" },
  { id: "execute", label: "Execute", icon: "play", description: "Run workflows & commands" },
];

export default function AXIOMInterface() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [thinkingState, setThinkingState] = useState<string | null>(null);
  const [showActions, setShowActions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const {
    setIsSpeaking,
    pendingVoiceCommand,
    setPendingVoiceCommand,
    isAwake,
    isListening,
  } = useAxiomStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const goHome = useCallback(() => {
    useAxiomStore.getState().setActiveWorkstation("axiom");
    router.push("/");
  }, [router]);

  const axiomSpeak = useCallback(
    (text: string) => {
      speak(text, {
        rate: 0.85,
        pitch: 1.08,
        onStart: () => setIsSpeaking(true),
        onEnd: () => setIsSpeaking(false),
      });
    },
    [setIsSpeaking],
  );

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isProcessing) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsProcessing(true);
    setThinkingState("Initializing...");
    setShowActions(false);

    try {
      const activeView = useAxiomStore.getState().activeView;
      const agentId = activeView === "boardroom" ? "jenson" : "founder";

      // First, send the message and get route info
      const routeResponse = await axiom.route(text.trim());

      // Update thinking state based on route
      if (routeResponse.category) {
        setThinkingState(`Routing to ${routeResponse.category}...`);
      }

      // Send chat request
      const response = await axiom.chat(text.trim());

      // Extract thinking if available
      let thinkingContent: string | undefined;
      if (response.awareness) {
        thinkingContent = `System awareness: ${response.awareness.state}, Health: ${Math.round(response.awareness.health_score * 100)}%`;
      }

      const axiomMsg: Message = {
        id: `axiom-${Date.now()}`,
        role: "axiom",
        content: response.response || "(no response)",
        timestamp: new Date(),
        thinking: thinkingContent,
        executive: response.agent_id || "axiom",
        toolCalls: [],
      };
      setMessages((prev) => [...prev, axiomMsg]);

      // AXIOM speaks the response
      axiomSpeak(axiomMsg.content);
    } catch (error) {
      const axiomMsg: Message = {
        id: `axiom-${Date.now()}`,
        role: "axiom",
        content:
          "I encountered an error processing your request. Please try again or check that the backend is running.",
        timestamp: new Date(),
        executive: "axiom",
      };
      setMessages((prev) => [...prev, axiomMsg]);
    } finally {
      setIsProcessing(false);
      setThinkingState(null);
      // Show actions again after a delay if no messages or only welcome
      setTimeout(() => {
        if (messages.length <= 2) setShowActions(true);
      }, 1000);
    }
  };

  // Handle voice commands from VoiceEngine (defined after handleSend)
  useEffect(() => {
    if (pendingVoiceCommand) {
      const cmd = pendingVoiceCommand;
      setPendingVoiceCommand(null);
      handleSend(cmd);
    }
  }, [pendingVoiceCommand]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleActionClick = (actionId: string) => {
    const prompts: Record<string, string> = {
      research: "Research ",
      create: "Create ",
      analyze: "Analyze ",
      execute: "Execute ",
    };
    const prompt = prompts[actionId] || "";
    if (prompt) {
      setInput(prompt);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[var(--axiom-bg-base)]">
      {/* Header with back navigation to the home dashboard */}
      <div className="flex items-center gap-2 px-4 md:px-6 py-2.5 border-b border-[var(--axiom-border)]/40 bg-[var(--axiom-bg-surface)]/30 backdrop-blur-xl flex-shrink-0">
        <motion.button
          onClick={goHome}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          className="group flex items-center gap-2 px-3 py-1.5 rounded-lg text-[var(--axiom-text-secondary)] hover:text-[var(--axiom-text-primary)] hover:bg-[var(--axiom-bg-elevated)]/60 transition-colors"
          title="Back to Home Dashboard"
          aria-label="Back to Home Dashboard"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-[var(--axiom-accent)] transition-transform duration-200 group-hover:-translate-x-0.5"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span className="text-xs font-semibold tracking-widest uppercase">Home</span>
        </motion.button>
      </div>

      {/* Main conversation area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Scrollable messages */}
        <div
          ref={scrollAreaRef}
          className="flex-1 overflow-y-auto px-6 md:px-12 lg:px-16 py-8 md:py-12 space-y-6"
        >
          <AnimatePresence initial={false} mode="popLayout">
            {messages.map((msg, index) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10, scale: 0.98 }}
                transition={{ duration: 0.35, ease: "easeOut" as const, delay: index * 0.03 }}
                className="flex gap-4 max-w-4xl md:max-w-5xl lg:max-w-6xl mx-auto w-full"
              >
                <ConversationMessage
                  message={msg}
                  isLast={index === messages.length - 1}
                />
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Thinking/Processing indicator */}
          <AnimatePresence>
            {isProcessing && (
              <motion.div
                key="thinking"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex gap-4 max-w-4xl md:max-w-5xl lg:max-w-6xl mx-auto w-full"
              >
                <ThinkingIndicator state={thinkingState} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action shortcuts (initial state) */}
          <AnimatePresence>
            {showActions && messages.length === 1 && !isProcessing && (
              <motion.div
                key="actions"
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.98 }}
                transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" as const }}
                className="flex justify-center pt-8"
              >
                <ActionShortcuts
                  actions={ACTIONS}
                  onActionClick={handleActionClick}
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>

        {/* Input composer */}
        <div className="border-t border-[var(--axiom-border)]/50 bg-[var(--axiom-bg-surface)]/30 backdrop-blur-xl">
          <InputComposer
            input={input}
            setInput={setInput}
            onSend={handleSend}
            onKeyDown={handleKeyDown}
            isProcessing={isProcessing}
            inputRef={inputRef}
            voiceActive={isAwake || isListening}
          />
        </div>
      </div>
    </div>
  );
}