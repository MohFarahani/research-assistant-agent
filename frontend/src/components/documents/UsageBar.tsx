"use client";

import { useUsage } from "@/hooks/useDocuments";

function Bar({ pct, danger }: { pct: number; danger: boolean }) {
  return (
    <div className="h-1.5 w-full bg-zinc-700 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${
          danger ? "bg-red-500" : pct >= 70 ? "bg-amber-400" : "bg-blue-500"
        }`}
        style={{ width: `${Math.min(pct, 100)}%` }}
      />
    </div>
  );
}

interface UsageBarProps {
  /** Show compact icon-only version for collapsed tablet sidebar */
  compact?: boolean;
}

export function UsageBar({ compact = false }: UsageBarProps) {
  const { data, isLoading } = useUsage();

  if (isLoading || !data) {
    if (compact) return null;
    return (
      <div className="animate-pulse space-y-1.5 px-1">
        <div className="h-2 bg-zinc-700 rounded-full w-3/4" />
        <div className="h-1.5 bg-zinc-700 rounded-full" />
      </div>
    );
  }

  const tokenPct = Math.round((data.tokens_used / data.tokens_limit) * 100);
  const reqPct = Math.round((data.requests_used / data.requests_limit) * 100);
  const danger = tokenPct >= 90 || reqPct >= 90;

  const resetTime = new Date(data.reset_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (compact) {
    // Tiny dot indicator for icon-only sidebar
    return (
      <div className="flex justify-center py-1" title={`Usage: ${tokenPct}% tokens, ${reqPct}% requests`}>
        <div
          className={`w-2 h-2 rounded-full ${
            danger ? "bg-red-500" : tokenPct >= 70 ? "bg-amber-400" : "bg-blue-500"
          }`}
        />
      </div>
    );
  }

  return (
    <div className="px-1 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-400">Daily usage</span>
        {danger && (
          <span className="text-xs text-red-400">resets {resetTime}</span>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span>Tokens</span>
          <span className={danger && tokenPct >= 90 ? "text-red-400" : ""}>{tokenPct}%</span>
        </div>
        <Bar pct={tokenPct} danger={tokenPct >= 90} />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span>Requests</span>
          <span className={danger && reqPct >= 90 ? "text-red-400" : ""}>{reqPct}%</span>
        </div>
        <Bar pct={reqPct} danger={reqPct >= 90} />
      </div>

      {!danger && (
        <p className="text-xs text-zinc-600">resets {resetTime}</p>
      )}
    </div>
  );
}
