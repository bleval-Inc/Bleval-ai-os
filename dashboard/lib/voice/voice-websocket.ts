// ── Voice WebSocket Hook ──────────────────────────────────────────────
// Real-time bidirectional voice communication with executives

import { useEffect, useRef, useState, useCallback } from "react";

export type VoiceWSMessageType =
  | "command"
  | "response"
  | "speak"
  | "status"
  | "error"
  | "ping"
  | "pong";

export type SpeechUrgency = "silent" | "low" | "normal" | "high" | "critical" | "escalation";

export interface VoiceWSMessage {
  type: VoiceWSMessageType;
  executive?: string;
  transcript?: string;
  response?: string;
  action_taken?: string;
  workflow_triggered?: string | null;
  requires_approval?: boolean;
  approval_id?: string | null;
  text?: string;
  urgency?: SpeechUrgency;
  wake_word?: string;
  confidence?: number;
  is_listening?: boolean;
  listening_executive?: string;
  message?: string;
  data?: VoiceWSCommandData;
}

export interface VoiceWSCommandData {
  transcript: string;
  executive: "axiom" | "jenson" | "valta_prime" | "yamako";
  wake_word: string;
  confidence: number;
}

export interface UseVoiceWebSocketOptions {
  clientId: string;
  onResponse?: (response: VoiceWSMessage) => void;
  onSpeak?: (speak: VoiceWSMessage) => void;
  onStatus?: (status: VoiceWSMessage) => void;
  onError?: (error: string) => void;
  onOpen?: () => void;
  onClose?: () => void;
  autoConnect?: boolean;
}

export interface UseVoiceWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendCommand: (transcript: string, executive: "axiom" | "jenson" | "valta_prime" | "yamako", wakeWord: string, confidence: number) => void;
  sendPing: () => void;
  lastMessage: VoiceWSMessage | null;
  connectionError: string | null;
}

export function useVoiceWebSocket(
  options: UseVoiceWebSocketOptions
): UseVoiceWebSocketReturn {
  const {
    clientId,
    onResponse,
    onSpeak,
    onStatus,
    onError,
    onOpen,
    onClose,
    autoConnect = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<VoiceWSMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/v1/voice/ws/${clientId}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttempts.current = 0;
        onOpen?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: VoiceWSMessage = JSON.parse(event.data);
          setLastMessage(message);

          switch (message.type) {
            case "response":
              onResponse?.(message);
              break;
            case "speak":
              onSpeak?.(message);
              break;
            case "status":
              onStatus?.(message);
              break;
            case "error":
              onError?.(message.message || "Unknown error");
              setConnectionError(message.message || "Unknown error");
              break;
            case "pong":
              // Heartbeat response
              break;
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        onClose?.();

        // Attempt reconnection
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionError("WebSocket connection failed");
        onError?.("WebSocket connection failed");
      };
    } catch (err) {
      console.error("Failed to create WebSocket:", err);
      setConnectionError("Failed to create WebSocket connection");
    }
  }, [clientId, onOpen, onClose, onResponse, onSpeak, onStatus, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendCommand = useCallback(
    (
      transcript: string,
      executive: "axiom" | "jenson" | "valta_prime" | "yamako",
      wakeWord: string,
      confidence: number
    ) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "command",
            data: {
              transcript,
              executive,
              wake_word: wakeWord,
              confidence,
            },
          })
        );
      }
    },
    []
  );

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "ping" }));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Heartbeat
  useEffect(() => {
    if (!isConnected) return;
    const interval = setInterval(() => {
      sendPing();
    }, 30000);
    return () => clearInterval(interval);
  }, [isConnected, sendPing]);

  return {
    isConnected,
    connect,
    disconnect,
    sendCommand,
    sendPing,
    lastMessage,
    connectionError,
  };
}

// ── Broadcast WebSocket for multi-client voice notifications ──────────

export interface UseVoiceBroadcastOptions {
  onSpeak?: (speak: VoiceWSMessage) => void;
  onStatus?: (status: VoiceWSMessage) => void;
  autoConnect?: boolean;
}

export interface UseVoiceBroadcastReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendSpeak: (executive: string, text: string, urgency?: "normal" | "high" | "emergency") => void;
}

export function useVoiceBroadcast(
  options: UseVoiceBroadcastOptions
): UseVoiceBroadcastReturn {
  const { onSpeak, onStatus, autoConnect = true } = options;
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/v1/voice/ws/broadcast`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: VoiceWSMessage = JSON.parse(event.data);
          if (message.type === "speak") {
            onSpeak?.(message);
          } else if (message.type === "status") {
            onStatus?.(message);
          }
        } catch (err) {
          console.error("Failed to parse broadcast message:", err);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
      };
    } catch (err) {
      console.error("Failed to create broadcast WebSocket:", err);
    }
  }, [onSpeak, onStatus]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendSpeak = useCallback(
    (executive: string, text: string, urgency: "normal" | "high" | "emergency" = "normal") => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "speak",
            executive,
            text,
            urgency,
          })
        );
      }
    },
    []
  );

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => disconnect();
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    connect,
    disconnect,
    sendSpeak,
  };
}