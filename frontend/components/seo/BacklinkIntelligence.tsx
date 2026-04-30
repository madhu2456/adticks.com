"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Link2, Shield, RefreshCw, Download, Network, Trash2,
} from "lucide-react";
import {
  useAnchors, useRefreshAnchors, useToxic, useScanToxic, useDisavowToxic,
  useLinkIntersect,
} from "@/hooks/useSEO";
import { api } from "@/lib/api";

const CLASS_COLORS: Record<string, string> = {
  branded: "bg-emerald-500/10 text-emerald-700 border-emerald-500/30",
  exact: "bg-amber-500/10 text-amber-700 border-amber-500/30",
  partial: "bg-blue-500/10 text-blue-700 border-blue-500/30",
  generic: "bg-slate-500/10 text-slate-700 border-slate-500/30",
  naked_url: "bg-violet-500/10 text-violet-700 border-violet-500/30",
  image: "bg-pink-500/10 text-pink-700 border-pink-500/30",
};

export function BacklinkIntelligence({ projectId }: { projectId: string }) {
  const { data: anchors, isLoading: anchorsLoading } = useAnchors(projectId);
  const refresh = useRefreshAnchors();
  const { data: toxic, isLoading: toxicLoading } = useToxic(projectId);
  const scan = useScanToxic();
  const disavow = useDisavowToxic();
  const intersect = useLinkIntersect();

  const totalAnchors = anchors?.reduce((s: number, a: any) => s + a.count, 0) ?? 0;

  const downloadDisavow = async () => {
    const data = await api.seoAdvanced.exportDisavow(projectId);
    const blob = new Blob([data.content], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "disavow.txt";
    link.click();
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="anchors">
        <TabsList>
          <TabsTrigger value="anchors">Anchor Text Distribution</TabsTrigger>
          <TabsTrigger value="toxic">Toxic Backlinks</TabsTrigger>
          <TabsTrigger value="intersect">Link Intersect</TabsTrigger>
        </TabsList>

        <TabsContent value="anchors" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2"><Link2 size={18}/> Anchor Text Distribution</CardTitle>
              <Button onClick={() => refresh.mutate({ projectId })} disabled={refresh.isPending} className="gap-2">
                <RefreshCw size={14} className={refresh.isPending ? "animate-spin" : ""}/> Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {anchorsLoading ? <Skeleton className="h-32"/> : !anchors?.length ? (
                <p className="text-sm text-text-muted text-center py-8">No anchor data yet. Click Refresh to compute from current backlinks.</p>
              ) : (
                <>
                  {/* Distribution bar */}
                  <div className="mb-4 flex h-3 rounded-full overflow-hidden">
                    {Object.entries(
                      anchors.reduce((acc: any, a: any) => {
                        acc[a.classification] = (acc[a.classification] || 0) + a.count;
                        return acc;
                      }, {})
                    ).map(([cls, count]) => {
                      const pct = ((count as number) / totalAnchors) * 100;
                      const colorMap: any = {
                        branded: "bg-emerald-500", exact: "bg-amber-500", partial: "bg-blue-500",
                        generic: "bg-slate-400", naked_url: "bg-violet-500", image: "bg-pink-500",
                      };
                      return <div key={cls} style={{ width: `${pct}%` }} className={colorMap[cls] || "bg-slate-400"} title={`${cls}: ${pct.toFixed(1)}%`}/>;
                    })}
                  </div>
                  <div className="flex flex-wrap gap-3 mb-4 text-xs">
                    {["branded","exact","partial","generic","naked_url","image"].map((c) => {
                      const count = anchors.filter((a: any) => a.classification === c).reduce((s: number, a: any) => s + a.count, 0);
                      const pct = totalAnchors ? ((count / totalAnchors) * 100).toFixed(1) : "0";
                      return (
                        <div key={c} className="flex items-center gap-1.5">
                          <Badge className={CLASS_COLORS[c]}>{c}</Badge>
                          <span className="text-text-muted">{count} ({pct}%)</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="overflow-auto max-h-96">
                    <table className="w-full text-sm">
                      <thead className="text-xs text-text-muted">
                        <tr>
                          <th className="text-left p-2">Anchor</th>
                          <th className="text-left p-2">Type</th>
                          <th className="text-right p-2">Count</th>
                          <th className="text-right p-2">Domains</th>
                        </tr>
                      </thead>
                      <tbody>
                        {anchors.map((a: any) => (
                          <tr key={a.id} className="border-t">
                            <td className="p-2 truncate max-w-md">{a.anchor}</td>
                            <td className="p-2"><Badge className={CLASS_COLORS[a.classification]}>{a.classification}</Badge></td>
                            <td className="p-2 text-right">{a.count}</td>
                            <td className="p-2 text-right">{a.referring_domains}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="toxic" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2"><Shield size={18}/> Toxic Backlinks</CardTitle>
              <div className="flex gap-2">
                <Button onClick={() => scan.mutate({ projectId })} disabled={scan.isPending} className="gap-2">
                  <RefreshCw size={14} className={scan.isPending ? "animate-spin" : ""}/> Scan
                </Button>
                <Button variant="outline" onClick={downloadDisavow} className="gap-2">
                  <Download size={14}/> Export disavow.txt
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {toxicLoading ? <Skeleton className="h-32"/> : !toxic?.length ? (
                <p className="text-sm text-text-muted text-center py-8">No toxic backlinks detected. Click Scan to evaluate the project's backlink set.</p>
              ) : (
                <div className="space-y-2">
                  {toxic.map((t: any) => (
                    <div key={t.id} className={`p-3 rounded border ${t.disavowed ? "opacity-50" : ""}`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">{t.referring_domain}</span>
                            <Badge className={t.spam_score >= 70 ? "bg-red-500/15 text-red-700 border-red-500/30" : "bg-amber-500/15 text-amber-700 border-amber-500/30"}>
                              Spam {t.spam_score.toFixed(0)}
                            </Badge>
                            {t.disavowed && <Badge className="bg-slate-500/15 text-slate-700">Disavowed</Badge>}
                          </div>
                          <ul className="text-xs text-text-muted mt-1 space-y-0.5">
                            {t.reasons?.map((r: string, i: number) => <li key={i}>• {r}</li>)}
                          </ul>
                        </div>
                        {!t.disavowed && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => disavow.mutate({ projectId, toxicId: t.id })}
                            className="gap-1.5"
                          >
                            <Trash2 size={12}/> Disavow
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="intersect" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2"><Network size={18}/> Link Intersect</CardTitle>
              <Button onClick={() => intersect.mutate({ projectId })} disabled={intersect.isPending} className="gap-2">
                <RefreshCw size={14} className={intersect.isPending ? "animate-spin" : ""}/> Compute
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-text-muted mb-3">
                Domains that link to your competitors but not to you — high-value outreach targets.
              </p>
              {!intersect.data?.length ? (
                <p className="text-sm text-text-muted text-center py-8">Click Compute to find opportunity domains.</p>
              ) : (
                <div className="overflow-auto max-h-96">
                  <table className="w-full text-sm">
                    <thead className="text-xs text-text-muted">
                      <tr>
                        <th className="text-left p-2">Domain</th>
                        <th className="text-left p-2">Linking to</th>
                        <th className="text-right p-2">Competitors</th>
                        <th className="text-right p-2">DA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {intersect.data.map((r: any) => (
                        <tr key={r.id} className="border-t">
                          <td className="p-2 font-medium">{r.referring_domain}</td>
                          <td className="p-2 text-xs text-text-muted">{r.competitors.join(", ")}</td>
                          <td className="p-2 text-right">{r.competitor_count}</td>
                          <td className="p-2 text-right">{r.domain_authority.toFixed(0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
