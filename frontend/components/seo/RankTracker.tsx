"use client";
import React, { useState } from "react";
import { LineChart } from "@/components/charts/LineChart";
import { Select, SelectItem } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { mockKeywords } from "@/lib/mockData";

function generateRankingHistory(keywordId: string) {
  return Array.from({ length: 30 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (29 - i));
    return {
      date: d.toISOString().split("T")[0].slice(5),
      position: Math.max(1, Math.floor(10 + Math.sin(i * 0.4) * 5 + Math.random() * 4)),
    };
  });
}

export function RankTracker() {
  const [selectedId, setSelectedId] = useState(mockKeywords[0]?.id ?? "");
  const data = generateRankingHistory(selectedId);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Rank Tracker</CardTitle>
          <p className="text-xs text-text-muted mt-0.5">Position over last 30 days</p>
        </div>
        <Select value={selectedId} onValueChange={setSelectedId} className="w-64">
          {mockKeywords.map((k) => (
            <SelectItem key={k.id} value={k.id}>{k.keyword}</SelectItem>
          ))}
        </Select>
      </CardHeader>
      <CardContent>
        <LineChart
          data={data}
          xKey="date"
          height={280}
          lines={[{ key: "position", color: "#6366f1", name: "Position" }]}
          formatY={(v) => `#${v}`}
        />
        <p className="text-xs text-text-muted mt-2 text-center">Lower position = better ranking</p>
      </CardContent>
    </Card>
  );
}
