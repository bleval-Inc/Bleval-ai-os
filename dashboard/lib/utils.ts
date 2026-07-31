import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function timeAgo(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const seconds = Math.floor((now - then) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function healthColor(
  status: "healthy" | "degraded" | "unhealthy" | string,
): string {
  switch (status) {
    case "healthy":
      return "text-emerald-400";
    case "degraded":
      return "text-amber-400";
    case "unhealthy":
      return "text-red-400";
    default:
      return "text-zinc-500";
  }
}

export function healthDotColor(
  status: "healthy" | "degraded" | "unhealthy" | string,
): string {
  switch (status) {
    case "healthy":
      return "bg-emerald-400";
    case "degraded":
      return "bg-amber-400";
    case "unhealthy":
      return "bg-red-400";
    default:
      return "bg-zinc-500";
  }
}