"use client";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AIPromptResult } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

interface PromptResultsProps {
  results?: AIPromptResult[];
  loading?: boolean;
}

const llmColors: Record<string, string> = {
  chatgpt: "bg-emerald-500/20 text-emerald-400",
  gemini: "bg-blue-500/20 text-blue-400",
  claude: "bg-orange-500/20 text-orange-400",
  perplexity: "bg-purple-500/20 text-purple-400",
};

const categoryColors: Record<string, string> = {
  brand: "bg-indigo-500/20 text-indigo-400",
  comparison: "bg-yellow-500/20 text-yellow-400",
  problem: "bg-red-500/20 text-red-400",
  feature: "bg-green-500/20 text-green-400",
};

export function PromptResults({ results = [], loading }: PromptResultsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader><Skeleton className="h-5 w-40" /></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt Results</CardTitle>
        <p className="text-xs text-text-muted">Recent AI prompt scans and brand mention positions</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {results.map((result) => {
            const selfMention = result.mentions.find((m) => m.brand === "AdTicks");
            return (
              <div key={result.id} className="rounded-lg border border-border p-4 hover:border-primary/30 transition-colors">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <p className="text-sm font-medium text-text-primary leading-snug flex-1">
                    &quot;{result.prompt.prompt}&quot;
                  </p>
                  <div className="flex items-center gap-1 shrink-0">
                    <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", llmColors[result.llm] ?? "bg-surface2 text-text-muted")}>
                      {result.llm}
                    </span>
                    <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium capitalize", categoryColors[result.prompt.category])}>
                      {result.prompt.category}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {result.mentions.map((m) => (
                    <div
                      key={m.brand}
                      className={cn(
                        "flex items-center gap-1 text-xs px-2 py-1 rounded-full border",
                        m.brand === "AdTicks"
                          ? "bg-primary/20 border-primary/40 text-primary font-semibold"
                          : "bg-surface2 border-border text-text-muted"
                      )}
                    >
                      <span className="w-4 h-4 rounded-full bg-surface flex items-center justify-center text-xs font-bold">{m.position}</span>
                      {m.brand}
                    </div>
                  ))}
                  {!selfMention && (
                    <span className="text-xs text-danger bg-danger/10 border border-danger/20 px-2 py-1 rounded-full">
                      AdTicks not mentioned
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-muted/60 mt-2">{formatRelativeTime(result.scanned_at)}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
