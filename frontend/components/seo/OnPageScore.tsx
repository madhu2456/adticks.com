"use client";
import React, { useState } from "react";
import { CheckCircle, XCircle, AlertCircle, Search, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useOnPageAudit } from "@/hooks/useSEO";
import { getScoreColor, cn } from "@/lib/utils";
import { ScanModal } from "@/components/layout/ScanModal";

interface OnPageScoreProps {
  projectId: string;
}

export function OnPageScore({ projectId }: OnPageScoreProps) {
  const [url, setUrl] = useState("");
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const { data: auditResponse, isLoading, refetch } = useOnPageAudit(projectId);
  
  const audit = auditResponse?.on_page;

  const icons = {
    pass: <CheckCircle className="h-4 w-4 text-success shrink-0" />,
    fail: <XCircle className="h-4 w-4 text-danger shrink-0" />,
    warning: <AlertCircle className="h-4 w-4 text-warning shrink-0" />,
  };

  const handleRunAudit = () => {
    if (!url) return;
    setIsScanModalOpen(true);
  };

  const handleModalClose = () => {
    setIsScanModalOpen(false);
    // Refresh the data after the scan modal closes
    refetch();
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
          <Input 
            placeholder="Enter URL to audit (e.g., https://example.com/page)" 
            value={url} 
            onChange={(e) => setUrl(e.target.value)} 
            className="pl-9" 
          />
        </div>
        <Button 
          onClick={handleRunAudit}
          disabled={!url || isLoading}
          className="gap-2"
        >
          <Zap size={16} />
          Run Audit
        </Button>
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

      {!isLoading && !audit && (
        <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-border rounded-xl bg-surface1/30">
          <Search className="h-12 w-12 text-text-muted mb-4 opacity-20" />
          <h3 className="text-lg font-medium text-text-primary">No Audit Results</h3>
          <p className="text-sm text-text-muted mt-1 max-w-xs text-center">
            Enter a URL above and click &quot;Run Audit&quot; to perform an on-page SEO analysis.
          </p>
        </div>
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
              {(audit.items || []).map((item: any) => (
                <div key={item.check} className={cn(
                  "flex items-start gap-3 rounded-lg p-3 border",
                  item.status === "pass" ? "bg-success/5 border-success/20" :
                  item.status === "fail" ? "bg-danger/5 border-danger/20" :
                  "bg-warning/5 border-warning/20"
                )}>
                  {icons[item.status as keyof typeof icons]}
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

      <ScanModal 
        isOpen={isScanModalOpen}
        onClose={handleModalClose}
        projectId={projectId}
        featureType="seo"
      />
    </div>
  );
}
