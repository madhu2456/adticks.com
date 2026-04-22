import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number, compact = false): string {
  if (compact && num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (compact && num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return new Intl.NumberFormat("en-US").format(num);
}

export function formatCurrency(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date));
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diff = now.getTime() - then.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return formatDate(date);
}

export function getTrendColor(change: number): string {
  if (change > 0) return "text-success";
  if (change < 0) return "text-danger";
  return "text-text-muted";
}

export function getTrendSymbol(change: number): string {
  if (change > 0) return "↑";
  if (change < 0) return "↓";
  return "—";
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#f59e0b";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

export function getPriorityColor(priority: "P1" | "P2" | "P3"): string {
  switch (priority) {
    case "P1": return "#ef4444";
    case "P2": return "#f59e0b";
    case "P3": return "#eab308";
    default: return "#94a3b8";
  }
}

export function getDifficultyColor(difficulty: number): string {
  if (difficulty <= 30) return "#10b981";
  if (difficulty <= 60) return "#f59e0b";
  return "#ef4444";
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
