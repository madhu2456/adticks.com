"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layers, RefreshCw } from "lucide-react";
import { useDomainCompareHistory, useCompareDomains } from "@/hooks/useSEO";

export function DomainCompare({ projectId, defaultDomain = "" }: { projectId: string; defaultDomain?: string }) {
  const [primary, setPrimary] = useState(defaultDomain);
  const [competitors, setCompetitors] = useState("");
  const { data: history, isLoading } = useDomainCompareHistory(projectId);
  const compare = useCompareDomains();

  const run = () => {
    const list = competitors.split(/[\s,]+/).filter(Boolean);
    if (!primary || list.length === 0) return;
    compare.mutate({ projectId, primary, competitors: list });
  };

  const latest = compare.data || history?.[0];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Layers size={18}/> Domain Comparison</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Your domain (e.g. example.com)" value={primary} onChange={(e) => setPrimary(e.target.value)}/>
          <Input placeholder="Competitors (comma or space separated)" value={competitors} onChange={(e) => setCompetitors(e.target.value)}/>
          <Button onClick={run} disabled={!primary || !competitors || compare.isPending} className="gap-2">
            {compare.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Layers size={16}/>}
            Compare
          </Button>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-32"/> : latest && (
        <Card>
          <CardHeader>
            <CardTitle>Side-by-side metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-text-muted">
                  <tr>
                    <th className="text-left p-2">Domain</th>
                    <th className="text-right p-2">DA</th>
                    <th className="text-right p-2">Status</th>
                    <th className="text-right p-2">Response</th>
                    <th className="text-right p-2">Indexable</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(latest.metrics || {}).map(([domain, m]: [string, any]) => (
                    <tr key={domain} className={`border-t ${domain === latest.primary_domain ? "bg-primary/5" : ""}`}>
                      <td className="p-2">
                        <span className="font-medium">{domain}</span>
                        {domain === latest.primary_domain && <Badge className="ml-2 bg-primary/10 text-primary">You</Badge>}
                      </td>
                      <td className="p-2 text-right tabular-nums">{m.domain_authority?.toFixed(0)}</td>
                      <td className="p-2 text-right">{m.homepage_status ?? "—"}</td>
                      <td className="p-2 text-right tabular-nums">{m.homepage_response_ms ?? "—"}ms</td>
                      <td className="p-2 text-right">{m.indexable ? "✓" : "✗"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
