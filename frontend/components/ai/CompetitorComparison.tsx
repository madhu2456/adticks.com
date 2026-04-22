"use client";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart } from "@/components/charts/BarChart";
import { CategoryBreakdown } from "@/lib/types";

interface CompetitorComparisonProps {
  data?: CategoryBreakdown[];
}

export function CompetitorComparison({ data = [] }: CompetitorComparisonProps) {
  const chartData = data.map((d) => ({
    name: d.category,
    score: d.score,
    max: d.total,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Breakdown</CardTitle>
        <p className="text-xs text-text-muted">AI visibility score by prompt category</p>
      </CardHeader>
      <CardContent>
        <BarChart
          data={chartData}
          xKey="name"
          height={220}
          bars={[{ key: "score", color: "#8b5cf6", name: "Visibility %" }]}
          formatY={(v) => `${v}%`}
        />
      </CardContent>
    </Card>
  );
}
