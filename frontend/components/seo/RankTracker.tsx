"use client";
import React, { useState } from "react";
import { LineChart } from "@/components/charts/LineChart";
import { Select, SelectItem } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useKeywords, useRankHistory, useSOV } from "@/hooks/useSEO";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, Smartphone, Monitor } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface RankTrackerProps {
  projectId: string;
}

export function RankTracker({ projectId }: RankTrackerProps) {
  const { data } = useKeywords(projectId);
  const keywords = data?.data ?? [];
  const [selectedId, setSelectedId] = useState("");
  const [device, setDevice] = useState("desktop");

  const activeKeywordId = selectedId || keywords[0]?.keyword_id || "";

  const { data: historyResponse, isLoading } = useRankHistory(projectId, activeKeywordId, 30, 0, 50, device);
  const { data: sovData } = useSOV(projectId);
  
  const rawHistoryData = historyResponse?.data || [];
  
  // Format data for chart (ascending date order)
  const historyData = rawHistoryData
    .map((item: any) => ({
      date: item.timestamp.split("T")[0].slice(5),
      position: item.rank !== undefined ? item.rank : item.position,
    }))
    .reverse();

  if (!keywords.length && !isLoading) {
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
        <div className="flex items-center gap-6">
          <div>
            <CardTitle>Rank Tracker</CardTitle>
            <p className="text-xs text-text-muted mt-0.5">Position over last 30 days</p>
          </div>
          {sovData && (
            <div className="flex items-center gap-2 border-l border-border pl-6">
               <div className="p-2 bg-primary/10 rounded-lg text-primary">
                 <TrendingUp size={16} />
               </div>
               <div>
                 <p className="text-[10px] text-text-muted uppercase font-bold tracking-wider">Share of Voice</p>
                 <p className="text-lg font-bold text-primary">{sovData.share_of_voice}%</p>
               </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Tabs value={device} onValueChange={setDevice} className="hidden sm:block">
            <TabsList className="h-9">
              <TabsTrigger value="desktop" className="gap-1.5 px-3">
                <Monitor size={14} />
                Desktop
              </TabsTrigger>
              <TabsTrigger value="mobile" className="gap-1.5 px-3">
                <Smartphone size={14} />
                Mobile
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <Select value={activeKeywordId} onValueChange={setSelectedId} className="w-64">
            {keywords.map((k) => (
              <SelectItem key={k.id} value={k.keyword_id}>{k.keyword || "Unknown"}</SelectItem>
            ))}
          </Select>
        </div>
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
