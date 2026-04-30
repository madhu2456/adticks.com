"use client";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { useCannibalization, useScanCannibalization } from "@/hooks/useSEO";

const SEV_COLOR: Record<string, string> = {
  high: "bg-red-500/15 text-red-700 border-red-500/30",
  medium: "bg-amber-500/15 text-amber-700 border-amber-500/30",
  low: "bg-blue-500/15 text-blue-700 border-blue-500/30",
};

export function CannibalizationDetector({ projectId }: { projectId: string }) {
  const { data, isLoading } = useCannibalization(projectId);
  const scan = useScanCannibalization();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle size={18}/> Keyword Cannibalization
          </CardTitle>
          <Button onClick={() => scan.mutate({ projectId, payload: { min_pages: 2 } })}
                  disabled={scan.isPending} className="gap-2">
            <RefreshCw size={14} className={scan.isPending ? "animate-spin" : ""}/> Scan
          </Button>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-text-muted">
            Pages on your domain competing for the same keyword — fix by consolidating, redirecting, or canonicalizing.
          </p>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-32"/> : !data?.length ? (
        <p className="text-sm text-text-muted text-center py-8">No cannibalization detected. Click Scan to run.</p>
      ) : (
        <div className="space-y-3">
          {data.map((row: any) => (
            <Card key={row.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle className="text-base">{row.keyword}</CardTitle>
                  <Badge className={SEV_COLOR[row.severity]}>{row.severity}</Badge>
                </div>
                <p className="text-xs text-text-muted">{row.recommendation}</p>
              </CardHeader>
              <CardContent>
                <table className="w-full text-sm">
                  <thead className="text-xs text-text-muted">
                    <tr>
                      <th className="text-left p-2">URL</th>
                      <th className="text-right p-2">Position</th>
                      <th className="text-right p-2">Clicks</th>
                      <th className="text-right p-2">Impressions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {row.urls?.map((u: any, i: number) => (
                      <tr key={i} className="border-t">
                        <td className="p-2 truncate max-w-md">
                          <a href={u.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                            {u.url}
                          </a>
                        </td>
                        <td className="p-2 text-right">{u.position?.toFixed(1) ?? "—"}</td>
                        <td className="p-2 text-right">{u.clicks ?? 0}</td>
                        <td className="p-2 text-right">{u.impressions ?? 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
