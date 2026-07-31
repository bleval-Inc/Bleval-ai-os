"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { TelemetrySnapshot, GreetingResult } from "../lib/axiom/telemetry-types";
import { getTelemetry, getGreeting, getWakeGreeting } from "../lib/axiom/system-monitor";

interface UseTelemetryOptions {
  /** Polling interval in ms (default 5000) */
  interval?: number;
  /** Auto-start polling on mount (default true) */
  autoStart?: boolean;
}

interface UseTelemetryReturn {
  /** Latest telemetry snapshot, or null if not yet loaded */
  snapshot: TelemetrySnapshot | null;
  /** Loading state for initial fetch */
  loading: boolean;
  /** Error message, or null */
  error: string | null;
  /** Whether polling is active */
  isPolling: boolean;
  /** Start polling */
  start: () => void;
  /** Stop polling */
  stop: () => void;
  /** Manually refresh telemetry once */
  refresh: () => Promise<void>;
  /** Boot greeting, populated on first successful telemetry fetch */
  bootGreeting: GreetingResult | null;
  /** Clear the boot greeting (e.g. after it's been spoken) */
  clearBootGreeting: () => void;
  /** Get a wake greeting */
  fetchWakeGreeting: () => Promise<GreetingResult | null>;
}

export function useSystemTelemetry(
  options: UseTelemetryOptions = {}
): UseTelemetryReturn {
  const { interval = 5000, autoStart = true } = options;

  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(autoStart);
  const [bootGreeting, setBootGreeting] = useState<GreetingResult | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasGreeted = useRef(false);
  const mounted = useRef(true);

  const fetchSnapshot = useCallback(async () => {
    try {
      const data = await getTelemetry();
      if (!mounted.current) return;
      setSnapshot(data);
      setError(null);

      // Generate boot greeting on first successful fetch
      if (!hasGreeted.current) {
        hasGreeted.current = true;
        try {
          const greeting = await getGreeting();
          if (mounted.current) {
            setBootGreeting(greeting);
          }
        } catch {
          // Greeting non-critical
        }
      }
    } catch (err) {
      if (!mounted.current) return;
      setError(err instanceof Error ? err.message : "Telemetry unavailable");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  const start = useCallback(() => {
    if (intervalRef.current) return;
    setIsPolling(true);
    fetchSnapshot();
    intervalRef.current = setInterval(fetchSnapshot, interval);
  }, [fetchSnapshot, interval]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const refresh = useCallback(async () => {
    await fetchSnapshot();
  }, [fetchSnapshot]);

  const clearBootGreeting = useCallback(() => {
    setBootGreeting(null);
  }, []);

  const fetchWakeGreeting = useCallback(async () => {
    try {
      return await getWakeGreeting();
    } catch {
      return null;
    }
  }, []);

  // Lifecycle
  useEffect(() => {
    mounted.current = true;
    if (autoStart) {
      start();
    }
    return () => {
      mounted.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    snapshot,
    loading,
    error,
    isPolling,
    start,
    stop,
    refresh,
    bootGreeting,
    clearBootGreeting,
    fetchWakeGreeting,
  };
}