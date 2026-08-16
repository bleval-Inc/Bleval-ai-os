"use client";

/** Mirrors the backend TelemetrySnapshot.to_dict() structure. */

export interface CpuInfo {
  percent: number;
  per_core: number[];
  count_logical: number;
  count_physical: number;
  frequency_mhz: number;
  load_avg: [number, number, number];
}

export interface MemoryInfo {
  total_gb: number;
  used_gb: number;
  available_gb: number;
  percent: number;
  swap_total_gb: number;
  swap_used_gb: number;
}

export interface DiskInfo {
  total_gb: number;
  used_gb: number;
  free_gb: number;
  percent: number;
  mount_point: string;
}

export interface NetworkInfo {
  bytes_sent_mb: number;
  bytes_recv_mb: number;
  packets_sent: number;
  packets_recv: number;
  connections: number;
  interfaces: string[];
}

export interface TemperatureInfo {
  cpu_temp_c: number | null;
  gpu_temp_c: number | null;
}

export interface ServiceInfo {
  name: string;
  status: string;
  pid: number | null;
  cpu_percent: number;
  memory_mb: number;
  uptime_seconds: number;
}

export interface TelemetrySnapshot {
  timestamp: number;
  hostname: string;
  platform: string;
  uptime_seconds: number;
  boot_time: number;
  processes: number;
  health_score: number;
  health_label: "healthy" | "degraded" | "critical";
  cpu: CpuInfo;
  memory: MemoryInfo;
  disk: DiskInfo;
  network: NetworkInfo;
  temperature: TemperatureInfo;
  services: ServiceInfo[];
}

export interface GreetingResult {
  text: string;
  mood: "professional" | "excited" | "calm" | "serious" | "warm";
  time_of_day: "morning" | "afternoon" | "evening" | "night";
  health_label: string;
  variant_id: string;
  is_seasonal: boolean;
  is_returning: boolean;
}

export interface SystemHealthCheck {
  healthy: boolean;
  health_score: number;
  health_label: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  uptime_seconds: number;
  processes: number;
  hostname: string;
  platform: string;
}

export interface ToolResult {
  success: boolean;
  output: string;
  data: Record<string, unknown>;
  error?: string;
}