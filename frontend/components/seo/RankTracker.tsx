"use client";
import React, { useState } from "react";
import { LineChart } from "@/components/charts/LineChart";
import { Select, SelectItem } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useKeywords, useRankHistory } from "@/hooks/useSEO";
import { Skeleton } from "@/components/ui/skeleton";

interface RankTrackerProps {
  projectId: string;
}

export function RankTracker({ projectId }: RankTrackerProps) {
  const { data } = useKeywords(projectId);
  const keywords = data?.data ?? [];
  const [selectedId, setSelectedId] = useState("");

  const activeKeywordId = selectedId || keywords[0]?.id || "";

  const { data: historyResponse, isLoading } = useRankHistory(projectId, activeKeywordId);
  
  const rawHistoryData = historyResponse?.data || [];
  
  // Format data for chart (ascending date order)
  const historyData = rawHistoryData
    .map((item: any) => ({
      date: item.timestamp.split("T")[0].slice(5),
      position: item.position,
    }))
    .reverse();

  if (!keywords.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Rank Tracker</CardTitle>
          <p className="text-xs text-text-muted mt-0.5">No keywords available</p>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Rank Tracker</CardTitle>
          <p className="text-xs text-text-muted mt-0.5">Position over last 30 days</p>
        </div>
        <Select value={activeKeywordId} onValueChange={setSelectedId} className="w-64">
          {keywords.map((k) => (
            <SelectItem key={k.id} value={k.id}>{k.keyword || "Unknown"}</SelectItem>
          ))}
        </Select>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[280px] w-full" />
        ) : historyData.length === 0 ? (
           <div className="h-[280px] flex items-center justify-center text-text-muted">
             No ranking history available for this keyword.
           </div>
        ) : (
          <LineChart
            data={historyData}
            xKey="date"
            height={280}
            lines={[{ key: "position", color: "#6366f1", name: "Position" }]}
            formatY={(v) => `#${v}`}
          />
        )}
        <p className="text-xs text-text-muted mt-2 text-center">Lower position = better ranking</p>
      </CardContent>
    </Card>
  );
}
