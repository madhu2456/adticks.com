"use client";
import React, { useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FileUp, ScanText, RefreshCw } from "lucide-react";
import { useLogEvents, useUploadLogFile } from "@/hooks/useSEO";

export function LogFileAnalyzer({ projectId }: { projectId: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [bot, setBot] = useState("");
  const [summary, setSummary] = useState<any>(null);
  const { data: events, isLoading } = useLogEvents(projectId, bot || undefined);
  const upload = useUploadLogFile();

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const res = await upload.mutateAsync({ projectId, file });
    setSummary(res.summary);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2"><ScanText size={18}/> Log File Analyzer</CardTitle>
          <div>
            <input
              ref={inputRef}
              type="file"
              accept=".log,.txt,.gz"
              onChange={onChange}
              className="hidden"
            />
            <Button
              onClick={() => inputRef.current?.click()}
              disabled={upload.isPending}
              className="gap-2"
            >
              {upload.isPending ? <RefreshCw size={16} className="animate-spin"/> : <FileUp size={16}/>}
              Upload Log File
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-text-muted">Supports Apache/Nginx Combined Log Format. Parses Googlebot, Bingbot, GPTBot, ClaudeBot, PerplexityBot and more.</p>
        </CardContent>
      </Card>

      {summary && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Total bot hits" value={summary.total_hits.toLocaleString()}/>
            <Stat label="Unique URLs" value={summary.unique_urls.toLocaleString()}/>
            <Stat label="Crawl waste" value={`${summary.crawl_waste_pct}%`} bad={summary.crawl_waste_pct > 10}/>
            <Stat label="Bots detected" value={Object.keys(summary.bots ?? {}).length}/>
          </div>

          <Card>
            <CardHeader><CardTitle>Bot distribution</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.bots ?? {}).map(([b, c]) => (
                  <Badge
                    key={b}
                    onClick={() => setBot(b === bot ? "" : b)}
                    className={`cursor-pointer ${bot === b ? "bg-primary text-white" : "bg-card-hover text-text-muted"} border-0`}
                  >
                    {b}: {String(c)}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      <Card>
        <CardHeader><CardTitle>Crawled URLs {bot && <Badge className="bg-primary/10 text-primary ml-2">{bot}</Badge>}</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32"/> : !events?.length ? (
            <p className="text-sm text-text-muted text-center py-8">Upload a log file to see bot crawl data.</p>
          ) : (
            <div className="overflow-auto max-h-[500px]">
              <table className="w-full text-sm">
                <thead className="text-xs text-text-muted">
                  <tr>
                    <th className="text-left p-2">Bot</th>
                    <th className="text-left p-2">URL</th>
                    <th className="text-right p-2">Status</th>
                    <th className="text-right p-2">Hits</th>
                    <th className="text-right p-2">Last Crawl</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((e: any) => (
                    <tr key={e.id} className="border-t">
                      <td className="p-2"><Badge className="bg-card-hover text-text-muted border-0 text-[10px]">{e.bot}</Badge></td>
                      <td className="p-2 truncate max-w-md">{e.url}</td>
                      <td className="p-2 text-right">
                        <Badge className={e.status_code === 200 ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30" : "bg-red-500/10 text-red-700 border-red-500/30"}>
                          {e.status_code}
                        </Badge>
                      </td>
                      <td className="p-2 text-right tabular-nums">{e.hits}</td>
                      <td className="p-2 text-right text-xs text-text-muted">{new Date(e.last_crawled).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value, bad }: { label: string; value: any; bad?: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
        <p className={`text-2xl font-bold mt-1 ${bad ? "text-red-600" : ""}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
