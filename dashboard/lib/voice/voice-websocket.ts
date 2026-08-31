// Voice WebSocket Hook
// Real-time bidirectional voice communication with executives

import { useEffect, useRef, useState, useCallback } from "react";

export type VoiceWSEventType =
  | "connected"
  | "wake_detected"
  | "listening_started"
  | "transcription_started"
  | "transcription_complete"
  | "processing"
  | "synthesizing"
  | "executive_speaking"
  | "display_result"
  | "idle"
  | "error"
  | "status"
  | "ping"
  | "pong";

export type SpeechUrgency = "silent" | "low" | "normal" | "high" | "critical" | "escalation";

export interface VoiceWSMessage {
  event: VoiceWSEventType;
  entity?: string;
  client_id?: string;
  message?: string;
  timestamp?: string;
  data?: {
    wake_word?: string;
    confidence?: number;
    text?: string;
    spoken_text?: string;
    audio_base64?: string;
    action_taken?: string;
    workflow_triggered?: string | null;
    requires_approval?: boolean;
    approval_id?: string | null;
    target_workstation?: string;
    transcript?: string;
    is_listening?: boolean;
    urgency?: SpeechUrgency;
    source?: string;
    [key: string]: any;
  };
}

export interface VoiceWSCommandData {
  transcript: string;
  executive: "axiom" | "jenson" | "valta_prime" | "yamako";
  wake_word: string;
  confidence: number;
}

export interface UseVoiceWebSocketOptions {
  clientId: string;
  onEvent?: (message: VoiceWSMessage) => void;
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
  sendPushToTalk: (entity: "axiom" | "jenson" | "valta_prime" | "yamako") => void;
  sendPing: () => void;
  lastMessage: VoiceWSMessage | null;
  connectionError: string | null;
  setShouldConnect: (should: boolean) => void;
}

export function useVoiceWebSocket(
  options: UseVoiceWebSocketOptions
): UseVoiceWebSocketReturn {
  const {
    clientId,
    onEvent,
    onSpeak,
    onStatus,
    onError,
    onOpen,
    onClose,
    autoConnect = true,
  } = options;

  // Use refs for callbacks to avoid recreating connect/disconnect
  const onEventRef = useRef(onEvent);
  const onSpeakRef = useRef(onSpeak);
  const onStatusRef = useRef(onStatus);
  const onErrorRef = useRef(onError);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const autoConnectRef = useRef(autoConnect);
  const clientIdRef = useRef(clientId);

  // Update refs when props change
  onEventRef.current = onEvent;
  onSpeakRef.current = onSpeak;
  onStatusRef.current = onStatus;
  onErrorRef.current = onError;
  onOpenRef.current = onOpen;
  onCloseRef.current = onClose;
  autoConnectRef.current = autoConnect;
  clientIdRef.current = clientId;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<VoiceWSMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const shouldConnectRef = useRef(true);
  const mountedRef = useRef(true);

  // Track mounted state
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (!shouldConnectRef.current) return;

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/v1/voice/ws/${clientIdRef.current}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttempts.current = 0;
        onOpenRef.current?.();
      };

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const message: VoiceWSMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Call appropriate callback based on event type
          switch (message.event) {
            case "executive_speaking":
              onSpeakRef.current?.(message);
              break;
            case "status":
              onStatusRef.current?.(message);
              break;
            case "error":
              onErrorRef.current?.(message.data?.message || "Unknown error");
              setConnectionError(message.data?.message || "Unknown error");
              break;
            case "pong":
              break;
          }

          // Also call generic onEvent for all events
          onEventRef.current?.(message);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      wsRef.current.onclose = (event) => {
        if (!mountedRef.current) return;
        setIsConnected(false);
        onCloseRef.current?.();

        const isCleanClose = event.code === 1000 || event.code === 1001;
        const shouldReconnect = shouldConnectRef.current &&
                                reconnectAttempts.current < maxReconnectAttempts &&
                                event.code !== 1006;

        if (shouldReconnect && !isCleanClose) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (isCleanClose) {
          reconnectAttempts.current = 0;
        }
      };

      wsRef.current.onerror = (error) => {
        if (!mountedRef.current) return;
        if (wsRef.current?.readyState === WebSocket.CONNECTING) {
          setConnectionError("WebSocket connection failed");
        }
        onErrorRef.current?.("WebSocket connection failed");
      };
    } catch (err) {
      console.error("Failed to create WebSocket:", err);
      if (mountedRef.current) {
        setConnectionError("Failed to create WebSocket connection");
      }
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (mountedRef.current) {
      setIsConnected(false);
    }
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

  const sendPushToTalk = useCallback(
    (entity: "axiom" | "jenson" | "valta_prime" | "yamako") => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "push_to_talk",
            entity,
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

  const setShouldConnect = useCallback((should: boolean) => {
    shouldConnectRef.current = should;
    if (!should) {
      disconnect();
    } else if (autoConnectRef.current) {
      connect();
    }
  }, [connect, disconnect]);

  // Auto-connect on mount - only depends on autoConnect ref, not callbacks
  useEffect(() => {
    if (autoConnectRef.current) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

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
    sendPushToTalk,
    sendPing,
    lastMessage,
    connectionError,
    setShouldConnect,
  };
}

// Broadcast WebSocket for multi-client voice notifications

export interface UseVoiceBroadcastOptions {
  onEvent?: (message: VoiceWSMessage) => void;
  onSpeak?: (speak: VoiceWSMessage) => void;
  onStatus?: (status: VoiceWSMessage) => void;
  autoConnect?: boolean;
}

export interface UseVoiceBroadcastReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendSpeak: (executive: string, text: string, urgency?: "normal" | "high" | "emergency") => void;
  setShouldConnect: (should: boolean) => void;
}

export function useVoiceBroadcast(
  options: UseVoiceBroadcastOptions
): UseVoiceBroadcastReturn {
  const { onEvent, onSpeak, onStatus, autoConnect = true } = options;

  // Use refs for callbacks to avoid recreating connect/disconnect
  const onEventRef = useRef(onEvent);
  const onSpeakRef = useRef(onSpeak);
  const onStatusRef = useRef(onStatus);
  const autoConnectRef = useRef(autoConnect);

  // Update refs when props change
  onEventRef.current = onEvent;
  onSpeakRef.current = onSpeak;
  onStatusRef.current = onStatus;
  autoConnectRef.current = autoConnect;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const shouldConnectRef = useRef(true);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const mountedRef = useRef(true);

  // Track mounted state
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (!shouldConnectRef.current) return;

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/v1/voice/ws/broadcast`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const message: VoiceWSMessage = JSON.parse(event.data);
          
          switch (message.event) {
            case "executive_speaking":
              onSpeakRef.current?.(message);
              break;
            case "status":
              onStatusRef.current?.(message);
              break;
          }
          
          onEventRef.current?.(message);
        } catch (err) {
          console.error("Failed to parse broadcast message:", err);
        }
      };

      wsRef.current.onclose = (event) => {
        if (!mountedRef.current) return;
        setIsConnected(false);

        const isCleanClose = event.code === 1000 || event.code === 1001;
        const shouldReconnect = shouldConnectRef.current &&
                                reconnectAttempts.current < maxReconnectAttempts &&
                                event.code !== 1006;

        if (shouldReconnect && !isCleanClose) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (isCleanClose) {
          reconnectAttempts.current = 0;
        }
      };
    } catch (err) {
      console.error("Failed to create broadcast WebSocket:", err);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (mountedRef.current) {
      setIsConnected(false);
    }
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

  const setShouldConnect = useCallback((should: boolean) => {
    shouldConnectRef.current = should;
    if (!should) {
      disconnect();
    } else if (autoConnectRef.current) {
      connect();
    }
  }, [connect, disconnect]);

  useEffect(() => {
    if (autoConnectRef.current) {
      connect();
    }
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    connect,
    disconnect,
    sendSpeak,
    setShouldConnect,
  };
}