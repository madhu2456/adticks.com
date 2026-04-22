"use client";
import React, { useState } from "react";
import { Inbox } from "lucide-react";
import { Insight } from "@/lib/types";
import { InsightCard } from "./InsightCard";

interface InsightListProps {
  insights: Insight[];
  loading?: boolean;
  onMarkRead?: (id: string) => void;
}

function SkeletonCard() {
  return (
    <div className="bg-[#1e293b] rounded-xl border border-[#334155] border-l-4 border-l-[#334155] p-5 animate-pulse">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg bg-[#334155]" />
        <div className="h-3 w-24 bg-[#334155] rounded" />
        <div className="ml-auto h-4 w-20 bg-[#334155] rounded" />
      </div>
      <div className="h-4 w-3/4 bg-[#334155] rounded mb-2" />
      <div className="h-3 w-full bg-[#334155] rounded mb-1" />
      <div className="h-3 w-5/6 bg-[#334155] rounded mb-4" />
      <div className="flex gap-2">
        <div className="h-5 w-16 bg-[#334155] rounded" />
        <div className="h-5 w-20 bg-[#334155] rounded" />
      </div>
    </div>
  );
}

const PAGE_SIZE = 10;

export function InsightList({ insights, loading = false, onMarkRead }: InsightListProps) {
  const [showAll, setShowAll] = useState(false);

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  if (insights.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-14 h-14 rounded-2xl bg-[#334155] flex items-center justify-center mb-4">
          <Inbox className="h-7 w-7 text-[#475569]" />
        </div>
        <h3 className="text-[#f1f5f9] font-semibold mb-1">No insights found</h3>
        <p className="text-sm text-[#94a3b8]">
          Try adjusting your filters or refresh to generate new insights.
        </p>
      </div>
    );
  }

  const displayed = showAll ? insights : insights.slice(0, PAGE_SIZE);

  return (
    <div className="space-y-3">
      {displayed.map((insight) => (
        <InsightCard key={insight.id} insight={insight} onMarkRead={onMarkRead} />
      ))}
      {insights.length > PAGE_SIZE && !showAll && (
        <div className="pt-2 text-center">
          <button
            onClick={() => setShowAll(true)}
            className="px-5 py-2 rounded-lg bg-[#334155] hover:bg-[#475569] text-[#f1f5f9] text-sm font-medium transition-colors"
          >
            Load more ({insights.length - PAGE_SIZE} remaining)
          </button>
        </div>
      )}
    </div>
  );
}
