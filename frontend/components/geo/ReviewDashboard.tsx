"use client";

import React from "react";
import { Star, TrendingUp, MessageSquare } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ReviewSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ReviewDashboardProps {
  projectId?: string;
  summary?: ReviewSummary;
  loading?: boolean;
}

export function ReviewDashboard({ projectId, summary, loading = false }: ReviewDashboardProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="h-48 rounded-lg" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="text-center py-12 text-muted-foreground border rounded-lg">
        No review data available
      </div>
    );
  }

  const getSentimentColor = (label: string) => {
    if (label === "positive") return "text-green-600 bg-green-50";
    if (label === "negative") return "text-red-600 bg-red-50";
    return "text-gray-600 bg-gray-50";
  };

  const getRatingColor = (rating?: number) => {
    if (!rating) return "text-muted-foreground";
    if (rating >= 4.5) return "text-green-600";
    if (rating >= 3.5) return "text-blue-600";
    if (rating >= 2.5) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-4">
      {/* Overall Rating */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Average Rating</h3>
              <div className="flex items-end gap-2">
                <span className={cn("text-4xl font-bold", getRatingColor(summary.average_rating))}>
                  {summary.average_rating?.toFixed(1) || "N/A"}
                </span>
                <span className="text-muted-foreground mb-1">/ 5.0</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-muted-foreground mb-1">Total Reviews</div>
              <div className="text-3xl font-bold">{summary.total_reviews}</div>
            </div>
          </div>

          {/* Star Distribution */}
          <div className="space-y-2 pt-4 border-t">
            {[5, 4, 3, 2, 1].map((stars) => {
              const count =
                stars === 5
                  ? summary.five_star
                  : stars === 4
                    ? summary.four_star
                    : stars === 3
                      ? summary.three_star
                      : stars === 2
                        ? summary.two_star
                        : summary.one_star;
              const percentage =
                summary.total_reviews > 0 ? (count / summary.total_reviews) * 100 : 0;

              return (
                <div key={stars} className="flex items-center gap-2">
                  <div className="flex items-center gap-1 w-12">
                    {stars}
                    <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  </div>
                  <div className="flex-1 bg-secondary rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-amber-400 h-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <div className="w-12 text-right text-xs text-muted-foreground">{count}</div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Sentiment Breakdown */}
      <Card className="p-6">
        <h3 className="font-semibold mb-4">Sentiment Breakdown</h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-4 rounded-lg bg-green-50">
            <div className="text-2xl font-bold text-green-600">{summary.positive_count}</div>
            <div className="text-sm text-green-700 font-medium">Positive</div>
          </div>
          <div className="p-4 rounded-lg bg-gray-50">
            <div className="text-2xl font-bold text-gray-600">{summary.neutral_count}</div>
            <div className="text-sm text-gray-700 font-medium">Neutral</div>
          </div>
          <div className="p-4 rounded-lg bg-red-50">
            <div className="text-2xl font-bold text-red-600">{summary.negative_count}</div>
            <div className="text-sm text-red-700 font-medium">Negative</div>
          </div>
        </div>
      </Card>

      {/* Reviews by Source */}
      <Card className="p-6">
        <h3 className="font-semibold mb-4">Reviews by Source</h3>
        <div className="space-y-2">
          {[
            { label: "Google", count: summary.google_reviews },
            { label: "Yelp", count: summary.yelp_reviews },
            { label: "Facebook", count: summary.facebook_reviews },
          ]
            .filter((source) => source.count > 0)
            .map((source) => {
              const percentage =
                summary.total_reviews > 0 ? (source.count / summary.total_reviews) * 100 : 0;
              return (
                <div key={source.label} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{source.label}</span>
                    <span className="text-muted-foreground">{source.count}</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-full rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </Card>
    </div>
  );
}
