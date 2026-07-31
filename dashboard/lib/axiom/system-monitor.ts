"use client";

import type {
  TelemetrySnapshot,
  GreetingResult,
  SystemHealthCheck,
  ToolResult,
} from "./telemetry-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

/** Fetch full system telemetry snapshot */
export async function getTelemetry(): Promise<TelemetrySnapshot> {
  return fetchJson<TelemetrySnapshot>(`${API_BASE}/system/telemetry`);
}

/** Fetch quick health check */
export async function getSystemHealth(): Promise<SystemHealthCheck> {
  return fetchJson<SystemHealthCheck>(`${API_BASE}/system/health`);
}

/** Generate a dynamic boot greeting */
export async function getGreeting(
  isFirstBoot?: boolean,
  userName?: string
): Promise<GreetingResult> {
  const params = new URLSearchParams();
  if (isFirstBoot) params.set("first_boot", "true");
  if (userName) params.set("user_name", userName);
  const qs = params.toString();
  return fetchJson<GreetingResult>(
    `${API_BASE}/system/greeting${qs ? `?${qs}` : ""}`
  );
}

/** Generate a wake greeting (shorter, for waking from idle) */
export async function getWakeGreeting(): Promise<GreetingResult> {
  return fetchJson<GreetingResult>(`${API_BASE}/system/greeting/wake`);
}

/** Generate a one-line system status report */
export async function getStatusReport(): Promise<{ text: string }> {
  return fetchJson<{ text: string }>(`${API_BASE}/system/status-report`);
}

/** Execute a system tool */
export async function executeTool(
  tool: string,
  args: Record<string, unknown> = {}
): Promise<ToolResult> {
  return fetchJson<ToolResult>(`${API_BASE}/system/execute-tool`, {
    method: "POST",
    body: JSON.stringify({ tool, args }),
  });
}

/** List available system tools */
export async function listTools(): Promise<
  { name: string; description: string }[]
> {
  return fetchJson<{ name: string; description: string }[]>(
    `${API_BASE}/system/tools`
  );
}

/** Get system info (OS, hostname, uptime) */
export async function getSystemInfo(): Promise<{
  hostname: string;
  platform: string;
  uptime_seconds: number;
  boot_time: number;
}> {
  return fetchJson(`${API_BASE}/system/info`);
}