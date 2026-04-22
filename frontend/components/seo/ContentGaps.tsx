"use client";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ContentGap } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

interface ContentGapsProps {
  gaps?: ContentGap[];
  loading?: boolean;
}

export function ContentGaps({ gaps = [], loading }: ContentGapsProps) {
  if (loading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface2/50">
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wide">Topic</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wide">Est. Volume</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wide">Competitors Covering</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wide">Opportunity</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wide">Keywords</th>
          </tr>
        </thead>
        <tbody>
          {gaps.map((gap, i) => (
            <tr key={gap.id} className="border-b border-border last:border-0 hover:bg-surface2/30 transition-colors">
              <td className="px-4 py-3 font-medium text-text-primary">{gap.topic}</td>
              <td className="px-4 py-3 text-text-muted">{formatNumber(gap.estimated_volume, true)}/mo</td>
              <td className="px-4 py-3">
                <div className="flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <div
                      key={j}
                      className={`w-3 h-3 rounded-sm ${j < gap.competitor_coverage ? "bg-warning/70" : "bg-surface2"}`}
                    />
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-surface2 rounded-full">
                    <div
                      className="h-full rounded-full bg-success"
                      style={{ width: `${gap.opportunity_score}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold text-success">{gap.opportunity_score}</span>
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {gap.keywords.slice(0, 2).map((kw) => (
                    <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                  ))}
                  {gap.keywords.length > 2 && (
                    <Badge variant="secondary" className="text-xs">+{gap.keywords.length - 2}</Badge>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
