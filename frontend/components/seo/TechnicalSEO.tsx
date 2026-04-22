"use client";
import React from "react";
import { CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TechnicalCheck } from "@/lib/types";
import { cn } from "@/lib/utils";

interface TechnicalSEOProps {
  checks?: TechnicalCheck[];
  loading?: boolean;
}

export function TechnicalSEO({ checks = [], loading }: TechnicalSEOProps) {
  if (loading) return <Skeleton className="h-64 w-full" />;

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

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Passed", count: counts.pass, color: "text-success", bg: "bg-success/10 border-success/20" },
          { label: "Warnings", count: counts.warning, color: "text-warning", bg: "bg-warning/10 border-warning/20" },
          { label: "Failed", count: counts.fail, color: "text-danger", bg: "bg-danger/10 border-danger/20" },
        ].map((s) => (
          <Card key={s.label} className={cn("border", s.bg)}>
            <CardContent className="p-3 text-center">
              <p className={cn("text-2xl font-bold", s.color)}>{s.count}</p>
              <p className="text-xs text-text-muted">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Checks */}
      <div className="space-y-2">
        {checks.map((check) => (
          <div
            key={check.check}
            className={cn(
              "flex items-start gap-3 rounded-xl p-4 border",
              check.status === "pass" ? "bg-success/5 border-success/20" :
              check.status === "fail" ? "bg-danger/5 border-danger/20" :
              "bg-warning/5 border-warning/20"
            )}
          >
            <div className="mt-0.5 shrink-0">{icons[check.status]}</div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-text-primary">{check.check}</p>
              <p className="text-xs text-text-muted mt-0.5">{check.description}</p>
              {check.fix && (
                <p className="text-xs text-warning mt-1.5">
                  <span className="font-semibold">Fix: </span>{check.fix}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
