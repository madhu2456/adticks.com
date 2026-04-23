"use client";
import React, { useState } from "react";
import { CheckCircle, XCircle, AlertCircle, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useOnPageAudit } from "@/hooks/useSEO";
import { getScoreColor, cn } from "@/lib/utils";

interface OnPageScoreProps {
  projectId: string;
}

export function OnPageScore({ projectId }: OnPageScoreProps) {
  const [url, setUrl] = useState("");
  const { data: audit, isLoading } = useOnPageAudit(projectId, url);

  const icons = {
    pass: <CheckCircle className="h-4 w-4 text-success shrink-0" />,
    fail: <XCircle className="h-4 w-4 text-danger shrink-0" />,
    warning: <AlertCircle className="h-4 w-4 text-warning shrink-0" />,
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
          <Input placeholder="https://yoursite.com/page" value={url} onChange={(e) => setUrl(e.target.value)} className="pl-9" />
        </div>
        <Button loading={isLoading} disabled={!url}>Run Audit</Button>
      </div>

      {isLoading && (
        <Card>
          <CardHeader>
            <Skeleton className="h-4 w-32" />
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </CardContent>
        </Card>
      )}

      {audit && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>On-Page Audit</CardTitle>
              <p className="text-xs text-text-muted mt-0.5 font-mono">{audit.url}</p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-bold" style={{ color: getScoreColor(audit.overall_score) }}>
                {audit.overall_score}
              </span>
              <p className="text-xs text-text-muted">/ 100</p>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {audit.items.map((item) => (
                <div key={item.check} className={cn(
                  "flex items-start gap-3 rounded-lg p-3 border",
                  item.status === "pass" ? "bg-success/5 border-success/20" :
                  item.status === "fail" ? "bg-danger/5 border-danger/20" :
                  "bg-warning/5 border-warning/20"
                )}>
                  {icons[item.status]}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary">{item.check}</p>
                    <p className="text-xs text-text-muted mt-0.5">{item.message}</p>
                  </div>
                  <span className="text-xs font-semibold text-text-muted shrink-0">{item.score}/100</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
