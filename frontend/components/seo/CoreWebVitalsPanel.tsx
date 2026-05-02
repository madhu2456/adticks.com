"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, RefreshCw, Smartphone, Monitor } from "lucide-react";
import { useCWV, useRunCWV } from "@/hooks/useSEO";

interface Props { projectId: string; defaultUrl?: string; }

const RANGES = {
  lcp: { good: 2500, poor: 4000, unit: "ms", label: "LCP" },
  inp: { good: 200, poor: 500, unit: "ms", label: "INP" },
  cls: { good: 0.1, poor: 0.25, unit: "", label: "CLS" },
  fcp: { good: 1800, poor: 3000, unit: "ms", label: "FCP" },
  ttfb: { good: 800, poor: 1800, unit: "ms", label: "TTFB" },
} as const;

function rate(metric: keyof typeof RANGES, value: number | null | undefined) {
  if (value == null) return { label: "—", color: "text-text-muted" };
  const r = RANGES[metric];
  if (value <= r.good) return { label: "Good", color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/30" };
  if (value <= r.poor) return { label: "Needs improvement", color: "text-amber-600 bg-amber-500/10 border-amber-500/30" };
  return { label: "Poor", color: "text-red-600 bg-red-500/10 border-red-500/30" };
}

export function CoreWebVitalsPanel({ projectId, defaultUrl = "" }: Props) {
  const [url, setUrl] = useState(defaultUrl);
  const [strategy, setStrategy] = useState<"mobile" | "desktop">("mobile");
  const { data: history, isLoading } = useCWV(projectId);
  const run = useRunCWV();

  const latest = history?.[0];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Activity size={18}/> Core Web Vitals + Lighthouse</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-3">
            <Input
              placeholder="https://example.com/page"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1"
            />
            <div className="flex bg-card-hover rounded-md p-1">
              <button
                className={`px-3 py-1.5 text-sm rounded gap-1 flex items-center ${strategy === "mobile" ? "bg-card shadow" : "text-text-muted"}`}
                onClick={() => setStrategy("mobile")}
              >
                <Smartphone size={14}/> Mobile
              </button>
              <button
                className={`px-3 py-1.5 text-sm rounded gap-1 flex items-center ${strategy === "desktop" ? "bg-card shadow" : "text-text-muted"}`}
                onClick={() => setStrategy("desktop")}
              >
                <Monitor size={14}/> Desktop
              </button>
            </div>
            <Button
              onClick={() => url && run.mutate({ projectId, url, strategy })}
              disabled={!url || run.isPending}
              className="gap-2"
            >
              {run.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Activity size={16}/>}
              Analyze
            </Button>
          </div>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-32"/> : latest && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <ScoreCard label="Performance" value={latest.performance_score}/>
            <ScoreCard label="SEO" value={latest.seo_score}/>
            <ScoreCard label="Accessibility" value={latest.accessibility_score}/>
            <ScoreCard label="Best Practices" value={latest.best_practices_score}/>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Web Vitals — {latest.strategy} — <span className="text-xs text-text-muted truncate">{latest.url}</span></CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <Vital metric="lcp" value={latest.lcp_ms}/>
                <Vital metric="inp" value={latest.inp_ms}/>
                <Vital metric="cls" value={latest.cls}/>
                <Vital metric="fcp" value={latest.fcp_ms}/>
                <Vital metric="ttfb" value={latest.ttfb_ms}/>
              </div>
            </CardContent>
          </Card>

          {latest.opportunities?.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Top Performance Opportunities & Diagnostics</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {latest.opportunities.map((op: any) => (
                    <div key={op.id} className="p-4 rounded-lg border bg-amber-500/5 border-amber-500/10">
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <p className="text-sm font-bold text-text-1">{op.title}</p>
                        <div className="flex gap-2">
                          {op.display_value && (
                            <Badge variant="outline" className="text-[10px] py-0">
                              {op.display_value}
                            </Badge>
                          )}
                          {op.savings_ms > 0 && (
                            <Badge className="bg-amber-500/20 text-amber-600 border-amber-500/30">
                              Save {(op.savings_ms / 1000).toFixed(2)}s
                            </Badge>
                          )}
                        </div>
                      </div>
                      <p className="text-xs text-text-2 leading-relaxed opacity-90">
                        {op.description?.replace(/\[(.*?)\]\((.*?)\)/g, '$1')}
                      </p>
                      {op.description?.includes('http') && (
                        <div className="mt-2">
                           <a 
                             href={op.description.match(/\((https?:\/\/.*?)\)/)?.[1]} 
                             target="_blank" 
                             rel="noopener noreferrer"
                             className="text-[10px] text-primary hover:underline font-medium"
                           >
                             Learn more in Lighthouse docs →
                           </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {history && history.length > 1 && (
        <Card>
          <CardHeader><CardTitle>Recent runs</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-text-muted">
                  <tr>
                    <th className="text-left p-2">URL</th>
                    <th className="text-left p-2">Strategy</th>
                    <th className="text-right p-2">Perf</th>
                    <th className="text-right p-2">SEO</th>
                    <th className="text-right p-2">LCP</th>
                    <th className="text-right p-2">INP</th>
                    <th className="text-right p-2">CLS</th>
                    <th className="text-right p-2">When</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((r: any) => (
                    <tr key={r.id} className="border-t">
                      <td className="p-2 truncate max-w-xs">{r.url}</td>
                      <td className="p-2">{r.strategy}</td>
                      <td className="p-2 text-right">{r.performance_score ?? "—"}</td>
                      <td className="p-2 text-right">{r.seo_score ?? "—"}</td>
                      <td className="p-2 text-right">{r.lcp_ms?.toFixed(0) ?? "—"}</td>
                      <td className="p-2 text-right">{r.inp_ms?.toFixed(0) ?? "—"}</td>
                      <td className="p-2 text-right">{r.cls?.toFixed(2) ?? "—"}</td>
                      <td className="p-2 text-right text-xs text-text-muted">{new Date(r.timestamp).toLocaleString()}</td>
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

function ScoreCard({ label, value }: { label: string; value: number | null }) {
  const color = value == null ? "text-text-muted"
    : value >= 90 ? "text-emerald-600"
    : value >= 50 ? "text-amber-600" : "text-red-600";
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
        <p className={`text-3xl font-bold ${color} mt-1`}>{value ?? "—"}</p>
      </CardContent>
    </Card>
  );
}

function Vital({ metric, value }: { metric: keyof typeof RANGES; value: number | null }) {
  const r = RANGES[metric];
  const status = rate(metric, value);
  const display = value == null ? "—" : metric === "cls" ? value.toFixed(2) : `${Math.round(value)}${r.unit}`;
  return (
    <div className="p-3 rounded border">
      <p className="text-xs uppercase tracking-wider text-text-muted">{r.label}</p>
      <p className="text-2xl font-bold mt-1">{display}</p>
      <Badge className={`${status.color} mt-2`}>{status.label}</Badge>
    </div>
  );
}
