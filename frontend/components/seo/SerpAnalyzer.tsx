"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ListChecks, Search, RefreshCw } from "lucide-react";
import { useAnalyzeSerp } from "@/hooks/useSEO";

export function SerpAnalyzer({ projectId }: { projectId: string }) {
  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("us");
  const [device, setDevice] = useState("desktop");
  const analyze = useAnalyzeSerp();

  const data = analyze.data;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><ListChecks size={18}/> SERP Analyzer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-3">
            <Input
              placeholder="Keyword (e.g. 'best running shoes')"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="flex-1"
            />
            <select value={location} onChange={(e) => setLocation(e.target.value)} className="px-2 py-2 rounded border bg-card text-sm">
              <option value="us">United States</option>
              <option value="uk">United Kingdom</option>
              <option value="in">India</option>
              <option value="de">Germany</option>
              <option value="ca">Canada</option>
            </select>
            <select value={device} onChange={(e) => setDevice(e.target.value)} className="px-2 py-2 rounded border bg-card text-sm">
              <option value="desktop">Desktop</option>
              <option value="mobile">Mobile</option>
            </select>
            <Button
              onClick={() => keyword && analyze.mutate({ projectId, keyword, location, device })}
              disabled={!keyword || analyze.isPending}
              className="gap-2"
            >
              {analyze.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Search size={16}/>}
              Analyze
            </Button>
          </div>
        </CardContent>
      </Card>

      {data && (
        <>
          {data.features_present?.length > 0 && (
            <Card>
              <CardHeader><CardTitle>SERP Features Detected</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {data.features_present.map((f: string) => (
                    <Badge key={f} className="bg-indigo-500/10 text-indigo-700 border-indigo-500/30">{f}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader><CardTitle>Top 10 Organic Results</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {(data.results || []).map((r: any) => (
                  <div key={r.position} className="p-3 rounded border hover:bg-card-hover">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-bold shrink-0">
                        {r.position}
                      </div>
                      <div className="flex-1 min-w-0">
                        <a href={r.url} target="_blank" rel="noreferrer" className="text-sm font-medium hover:underline line-clamp-1">
                          {r.title}
                        </a>
                        <p className="text-xs text-emerald-700 truncate">{r.url}</p>
                        <p className="text-xs text-text-muted line-clamp-2 mt-1">{r.snippet}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <Badge className="bg-card-hover text-text-muted border-0">DA {r.domain_authority?.toFixed(0) ?? "—"}</Badge>
                        <p className="text-xs text-text-muted mt-1">{r.domain}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
