"use client";

import React from "react";
import { CheckCircle2, AlertCircle, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Citation, NAPCheckResult } from "@/lib/types";
import { cn } from "@/lib/utils";

interface CitationAuditProps {
  citations?: Citation[];
  napCheck?: NAPCheckResult;
  loading?: boolean;
  maxRows?: number;
}

export function CitationAudit({
  citations = [],
  napCheck,
  loading = false,
  maxRows = 10,
}: CitationAuditProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
    );
  }

  if (citations.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground border rounded-lg">
        No citations found
      </div>
    );
  }

  const getConsistencyColor = (score: number) => {
    if (score >= 0.8) return "text-green-600 bg-green-50";
    if (score >= 0.5) return "text-amber-600 bg-amber-50";
    return "text-red-600 bg-red-50";
  };

  const getConsistencyLabel = (score: number) => {
    if (score >= 0.8) return "Good";
    if (score >= 0.5) return "Fair";
    return "Poor";
  };

  return (
    <div className="space-y-4">
      {/* NAP Check Summary */}
      {napCheck && (
        <Card className="p-6 bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">NAP Consistency Check</h3>
              <div className="text-right">
                <div className="text-3xl font-bold text-primary">
                  {napCheck.consistency_percentage.toFixed(0)}%
                </div>
                <div className="text-xs text-muted-foreground">
                  {napCheck.consistent_citations}/{napCheck.total_citations} consistent
                </div>
              </div>
            </div>

            {napCheck.consistency_percentage === 100 ? (
              <div className="flex items-center gap-2 text-green-600 text-sm">
                <CheckCircle2 className="h-4 w-4" />
                All citations have matching Name, Address, and Phone
              </div>
            ) : napCheck.consistency_percentage >= 75 ? (
              <div className="flex items-center gap-2 text-amber-600 text-sm">
                <AlertCircle className="h-4 w-4" />
                Most citations are consistent, but some issues found
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-600 text-sm">
                <AlertCircle className="h-4 w-4" />
                Multiple NAP inconsistencies detected
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Citations List */}
      <div className="space-y-3">
        {citations.slice(0, maxRows).map((citation) => (
          <Card key={citation.id} className="p-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold flex items-center gap-2">
                    {citation.source_name}
                    <a
                      href={citation.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-primary hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
                <Badge
                  className={cn(
                    "whitespace-nowrap",
                    getConsistencyColor(citation.consistency_score)
                  )}
                >
                  {getConsistencyLabel(citation.consistency_score)} ({(citation.consistency_score * 100).toFixed(0)}%)
                </Badge>
              </div>

              {/* NAP Matches */}
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="p-2 rounded bg-secondary">
                  <div className="font-medium text-xs text-muted-foreground mb-1">Name</div>
                  <div className="flex items-center gap-1">
                    {citation.name_match ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <span className="text-xs">{citation.name_match ? "Match" : "Mismatch"}</span>
                  </div>
                </div>
                <div className="p-2 rounded bg-secondary">
                  <div className="font-medium text-xs text-muted-foreground mb-1">Address</div>
                  <div className="flex items-center gap-1">
                    {citation.address_match ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <span className="text-xs">{citation.address_match ? "Match" : "Mismatch"}</span>
                  </div>
                </div>
                <div className="p-2 rounded bg-secondary">
                  <div className="font-medium text-xs text-muted-foreground mb-1">Phone</div>
                  <div className="flex items-center gap-1">
                    {citation.phone_match ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <span className="text-xs">{citation.phone_match ? "Match" : "Mismatch"}</span>
                  </div>
                </div>
              </div>

              {/* Citation Details */}
              {(citation.business_name || citation.citation_address || citation.citation_phone) && (
                <div className="pt-2 border-t text-xs space-y-1 text-muted-foreground">
                  {citation.business_name && (
                    <div>
                      <span className="font-medium">Business Name:</span> {citation.business_name}
                    </div>
                  )}
                  {citation.citation_address && (
                    <div>
                      <span className="font-medium">Address:</span> {citation.citation_address}
                    </div>
                  )}
                  {citation.citation_phone && (
                    <div>
                      <span className="font-medium">Phone:</span> {citation.citation_phone}
                    </div>
                  )}
                </div>
              )}

              {/* Last Verified */}
              {citation.last_verified && (
                <div className="text-xs text-muted-foreground">
                  Last verified: {new Date(citation.last_verified).toLocaleDateString()}
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>

      {citations.length > maxRows && (
        <div className="text-center text-sm text-muted-foreground py-2">
          +{citations.length - maxRows} more citations
        </div>
      )}
    </div>
  );
}
