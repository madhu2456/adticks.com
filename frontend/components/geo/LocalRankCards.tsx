"use client";

import React from "react";
import { MapPin, TrendingUp, TrendingDown, Smartphone, Monitor } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { LocalRank } from "@/lib/types";
import { cn } from "@/lib/utils";

interface LocalRankCardsProps {
  ranks?: LocalRank[];
  loading?: boolean;
  maxRows?: number;
}

export function LocalRankCards({ ranks = [], loading = false, maxRows = 5 }: LocalRankCardsProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
    );
  }

  if (ranks.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground border rounded-lg">
        No local rankings yet
      </div>
    );
  }

  const getDeviceIcon = (device: string) => {
    return device === "mobile" ? (
      <Smartphone className="h-4 w-4" />
    ) : (
      <Monitor className="h-4 w-4" />
    );
  };

  const getRankColor = (rank?: number) => {
    if (!rank) return "text-muted-foreground";
    if (rank <= 3) return "text-green-600";
    if (rank <= 10) return "text-blue-600";
    if (rank <= 20) return "text-amber-600";
    return "text-red-600";
  };

  const getRankBadgeVariant = (rank?: number): "default" | "secondary" | "outline" | "destructive" => {
    if (!rank) return "secondary";
    if (rank <= 3) return "default";
    if (rank <= 10) return "secondary";
    return "outline";
  };

  return (
    <div className="grid gap-3">
      {ranks.slice(0, maxRows).map((rank, index) => (
        <Card key={rank.id} className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-base mb-2 truncate">{rank.keyword}</div>
              <div className="flex flex-wrap gap-3 text-sm">
                {rank.google_maps_rank !== undefined && (
                  <div className="flex items-center gap-1">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Maps:</span>
                    <span className={cn("font-semibold", getRankColor(rank.google_maps_rank))}>
                      #{rank.google_maps_rank}
                    </span>
                  </div>
                )}
                {rank.local_pack_position !== undefined && (
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Local Pack:</span>
                    <span className={cn("font-semibold", getRankColor(rank.local_pack_position))}>
                      #{rank.local_pack_position}
                    </span>
                  </div>
                )}
                {rank.local_search_rank !== undefined && (
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Local:</span>
                    <span className={cn("font-semibold", getRankColor(rank.local_search_rank))}>
                      #{rank.local_search_rank}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                {getDeviceIcon(rank.device)}
                {rank.device}
              </Badge>
            </div>
          </div>
        </Card>
      ))}
      {ranks.length > maxRows && (
        <div className="text-center text-sm text-muted-foreground py-2">
          +{ranks.length - maxRows} more rankings
        </div>
      )}
    </div>
  );
}
