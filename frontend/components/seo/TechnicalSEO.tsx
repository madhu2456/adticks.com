"use client";
import React from "react";
import { CheckCircle, XCircle, AlertCircle, TrendingUp, History } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TechnicalCheck } from "@/lib/types";
import { cn } from "@/lib/utils";
import { LineChart } from "@/components/charts/LineChart";
import { useAuditHistory } from "@/hooks/useSEO";

interface TechnicalSEOProps {
  projectId: string;
  checks?: TechnicalCheck[];
  loading?: boolean;
}

export function TechnicalSEO({ projectId, checks = [], loading }: TechnicalSEOProps) {
  const { data: historyData, isLoading: historyLoading } = useAuditHistory(projectId);

  if (loading) return <Skeleton className="h-96 w-full" />;

  const icons = {
    pass: <CheckCircle className="h-5 w-5 text-success" />,
    fail: <XCircle className="h-5 w-5 text-danger" />,
    warning: <AlertCircle className="h-5 w-5 text-warning" />,
  };

  const counts = {
    pass: checks.filter((c) => c.status === "pass").length,
    fail: checks.filter((c) => c.status === "fail").length,
    warning: checks.filter((c) => c.status === "warning").length,
  };

  const formattedHistory = (historyData || [])
    .map((h: any) => ({
      date: new Date(h.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      score: h.score,
      errors: h.total_errors,
      warnings: h.total_warnings
    }))
    .reverse();

  return (
    <div className="space-y-6">
      {/* Historical Performance Chart */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Audit History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <Skeleton className="h-[250px] w-full" />
          ) : formattedHistory.length > 0 ? (
            <div className="pt-2">
               <LineChart 
                data={formattedHistory}
                xKey="date"
                height={250}
                lines={[
                  { key: "score", color: "#6366f1", name: "Health Score" },
                  { key: "errors", color: "#ef4444", name: "Errors" }
                ]}
               />
            </div>
          ) : (
            <div className="h-[200px] flex flex-col items-center justify-center text-text-muted border-2 border-dashed border-border rounded-xl">
               <TrendingUp className="h-8 w-8 mb-2 opacity-20" />
               <p className="text-sm">No audit history available yet.</p>
               <p className="text-xs">Run a technical audit to start tracking performance.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Passed", count: counts.pass, color: "text-success", bg: "bg-success/10 border-success/20" },
          { label: "Warnings", count: counts.warning, color: "text-warning", bg: "bg-warning/10 border-warning/20" },
          { label: "Failed", count: counts.fail, color: "text-danger", bg: "bg-danger/10 border-danger/20" },
        ].map((s) => (
          <Card key={s.label} className={cn("border shadow-none", s.bg)}>
            <CardContent className="p-3 text-center">
              <p className={cn("text-2xl font-bold", s.color)}>{s.count}</p>
              <p className="text-xs text-text-muted font-medium">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Checks List */}
      <div className="space-y-3">
        <h3 className="font-semibold text-text-primary px-1">Detailed Findings</h3>
        <div className="space-y-2">
          {checks.map((check) => (
            <div
              key={check.check}
              className={cn(
                "flex items-start gap-3 rounded-xl p-4 border transition-colors",
                check.status === "pass" ? "bg-surface2/30 border-border hover:bg-success/5" :
                check.status === "fail" ? "bg-danger/5 border-danger/10 hover:bg-danger/10" :
                "bg-warning/5 border-warning/10 hover:bg-warning/10"
              )}
            >
              <div className="mt-0.5 shrink-0">{icons[check.status]}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-text-primary">{check.check}</p>
                  <Badge variant="outline" className="text-[10px] uppercase font-bold tracking-tight">
                    {check.status === 'pass' ? 'Healthy' : 'Action Required'}
                  </Badge>
                </div>
                <p className="text-xs text-text-muted mt-1 leading-relaxed">{check.description}</p>
                {check.fix && (
                  <div className="mt-3 p-2.5 rounded-lg bg-background/50 border border-border/50">
                    <p className="text-[11px] text-text-muted">
                      <span className="font-bold text-primary uppercase mr-1.5 text-[10px]">Fix Recommendation</span>
                      {check.fix}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
