"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import {
  AlertCircle, AlertTriangle, Info, CheckCircle2, Play, RefreshCw, Search, Globe, ChevronDown, Check, X
} from "lucide-react";
import { useAuditSummary, useAuditIssues, useRunSiteAudit, useCrawledPages } from "@/hooks/useSEO";
import { useScanProgress } from "@/hooks/useScanProgress";
import { getAccessToken } from "@/lib/auth";

const SEVERITY_META: Record<string, { label: string; color: string; Icon: any }> = {
  error: { label: "Errors", color: "text-red-600 bg-red-500/10 border-red-500/30", Icon: AlertCircle },
  warning: { label: "Warnings", color: "text-amber-700 bg-amber-500/10 border-amber-500/30", Icon: AlertTriangle },
  notice: { label: "Notices", color: "text-blue-700 bg-blue-500/10 border-blue-500/30", Icon: Info },
};

const CATEGORIES = [
  "all", "crawlability", "indexability", "on_page", "performance", "security",
  "international", "structured", "links", "images", "mobile", "content",
];

interface Props {
  projectId: string;
  defaultUrl?: string;
}

export function SiteAuditDashboard({ projectId, defaultUrl = "" }: Props) {
  const [url, setUrl] = useState(defaultUrl);
  const [maxPages, setMaxPages] = useState(50);
  const [severity, setSeverity] = useState<string>("");
  const [category, setCategory] = useState<string>("all");
  const [selectedUrls, setSelectedUrls] = useState<string[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);

  const { data: summary, isLoading: summaryLoading, refetch: refetchSummary } = useAuditSummary(projectId);
  const { data: issues, isLoading: issuesLoading, refetch: refetchIssues } =
    useAuditIssues(projectId, severity || undefined, category === "all" ? undefined : category, selectedUrls);
  const { data: pages, refetch: refetchPages } = useCrawledPages(projectId);
  const runAudit = useRunSiteAudit();

  const token = getAccessToken();
  const { progress, stage, message, isConnected } = useScanProgress(taskId, token);

  const handleRun = async () => {
    if (!url) return;
    setTaskId(null);
    try {
      const res = await runAudit.mutateAsync({ projectId, url, max_pages: maxPages, max_depth: 3 });
      if (res.task_id) {
        setTaskId(res.task_id);
      }
    } catch (e) {
      console.error("Failed to start audit:", e);
    }
  };

  // Sync results when audit completes
  useEffect(() => {
    if (progress === 100) {
      refetchSummary();
      refetchIssues();
      refetchPages();
    }
  }, [progress, refetchSummary, refetchIssues, refetchPages]);

  const score = summary?.score ?? 0;
  const scoreColor = score >= 80 ? "text-emerald-600" : score >= 60 ? "text-amber-600" : "text-red-600";

  return (
    <div className="space-y-6">
      {/* Run audit panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Globe size={18}/> Run Site Audit</CardTitle>
          <CardDescription>Crawl your domain to find technical and on-page SEO issues.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            <Input
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1"
            />
            <Input
              type="number"
              placeholder="Max pages"
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value) || 50)}
              className="w-32"
            />
            <Button onClick={handleRun} disabled={!url || runAudit.isPending || (!!taskId && progress < 100)} className="gap-2">
              {runAudit.isPending || (!!taskId && progress < 100) ? <RefreshCw size={16} className="animate-spin"/> : <Play size={16}/>}
              {runAudit.isPending ? "Starting…" : (!!taskId && progress < 100) ? "Crawling…" : "Run Audit"}
            </Button>
          </div>

          {/* Real-time Progress Bar */}
          {taskId && progress < 100 && (
            <div className="space-y-2 pt-2 animate-in fade-in slide-in-from-top-1">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-primary uppercase tracking-wider">{stage || "Crawl"}</span>
                <span>{progress === 0 ? "Initializing" : `${progress}%`}</span>
              </div>
              <Progress value={progress === 0 ? 5 : progress} className="h-2" />
              <p className="text-[10px] text-muted-foreground italic">{message || "Connecting to crawler engine..."}</p>
            </div>
          )}

          {runAudit.isError && (
            <p className="text-sm text-red-500 mt-2">Audit failed. Try a different URL.</p>
          )}
        </CardContent>
      </Card>

      {/* Summary cards */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-28"/>)}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase tracking-wider text-text-muted">Health Score</p>
              <p className={`text-3xl font-bold ${scoreColor} mt-1`}>{score}</p>
              <Progress value={score} className="mt-2 h-2"/>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase tracking-wider text-text-muted">Pages Crawled</p>
              <p className="text-3xl font-bold mt-1">{summary.total_pages}</p>
              <p className="text-xs text-text-muted mt-2">avg {summary.avg_response_time_ms}ms</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase tracking-wider text-text-muted">Errors</p>
              <p className="text-3xl font-bold text-red-600 mt-1">{summary.errors}</p>
              <p className="text-xs text-text-muted mt-2">{summary.warnings} warnings</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase tracking-wider text-text-muted">Total Issues</p>
              <p className="text-3xl font-bold mt-1">{summary.total_issues}</p>
              <p className="text-xs text-text-muted mt-2">{summary.notices} notices</p>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Issues by category */}
      {summary?.issues_by_category && Object.keys(summary.issues_by_category).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Issues by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(summary.issues_by_category).map(([cat, count]) => (
                <Badge
                  key={cat}
                  className="cursor-pointer bg-indigo-500/10 text-indigo-700 border border-indigo-500/30 hover:bg-indigo-500/20"
                  onClick={() => setCategory(cat)}
                >
                  {cat}: {String(count)}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Issue list */}
      <Card>
        <CardHeader className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <CardTitle>Issues</CardTitle>
          <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
            <URLMultiSelect 
              options={pages?.map(p => p.url) || []} 
              selected={selectedUrls} 
              onChange={setSelectedUrls} 
            />
            
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="text-xs h-8 px-2 py-1 rounded border bg-card focus:ring-1 focus:ring-primary outline-none"
            >
              <option value="">All severities</option>
              <option value="error">Errors</option>
              <option value="warning">Warnings</option>
              <option value="notice">Notices</option>
            </select>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="text-xs h-8 px-2 py-1 rounded border bg-card focus:ring-1 focus:ring-primary outline-none"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c === "all" ? "All types" : c.charAt(0).toUpperCase() + c.slice(1).replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {issuesLoading ? (
            <div className="space-y-2">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12"/>)}</div>
          ) : !issues?.length ? (
            <p className="text-sm text-text-muted text-center py-8">No issues found. Run an audit to populate this list.</p>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-auto">
              {issues.map((issue: any) => {
                const meta = SEVERITY_META[issue.severity] || SEVERITY_META.notice;
                const Icon = meta.Icon;
                return (
                  <div key={issue.id} className={`p-3 rounded-lg border ${meta.color}`}>
                    <div className="flex items-start gap-3">
                      <Icon size={16} className="shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge className="bg-white/40 text-current border-0 text-[10px]">{issue.category}</Badge>
                          <Badge className="bg-white/40 text-current border-0 text-[10px]">{issue.code}</Badge>
                        </div>
                        <p className="text-sm font-medium mt-1">{issue.message}</p>
                        {issue.recommendation && (
                          <p className="text-xs text-text-muted mt-1">→ {issue.recommendation}</p>
                        )}
                        <a href={issue.url} target="_blank" rel="noreferrer"
                           className="text-xs text-blue-600 hover:underline truncate block mt-1">
                          {issue.url}
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Crawled pages summary */}
      {pages && pages.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Crawled Pages ({pages.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="text-xs text-text-muted">
                  <tr>
                    <th className="text-left p-2">URL</th>
                    <th className="text-right p-2">Status</th>
                    <th className="text-right p-2">Words</th>
                    <th className="text-right p-2">Internal</th>
                    <th className="text-right p-2">Images</th>
                    <th className="text-right p-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {pages.slice(0, 50).map((p: any) => (
                    <tr key={p.id} className="border-t hover:bg-card-hover">
                      <td className="p-2 truncate max-w-md">{p.url}</td>
                      <td className="p-2 text-right">
                        <Badge className={p.status_code === 200 ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30" : "bg-red-500/10 text-red-700 border-red-500/30"}>
                          {p.status_code}
                        </Badge>
                      </td>
                      <td className="p-2 text-right">{p.word_count}</td>
                      <td className="p-2 text-right">{p.internal_links}</td>
                      <td className="p-2 text-right">{p.images}</td>
                      <td className="p-2 text-right">{p.response_time_ms}ms</td>
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

function URLMultiSelect({ options, selected, onChange }: { options: string[], selected: string[], onChange: (val: string[]) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const uniqueOptions = Array.from(new Set(options));
  const filteredOptions = uniqueOptions.filter(o => o.toLowerCase().includes(search.toLowerCase())).slice(0, 50);

  const toggle = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter(s => s !== opt));
    } else {
      onChange([...selected, opt]);
    }
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between gap-2 px-3 h-8 bg-card border rounded-md text-xs min-w-[200px] hover:bg-accent transition-colors"
      >
        <span className="truncate max-w-[150px]">
          {selected.length === 0 ? "Filter by URL..." : `${selected.length} URLs selected`}
        </span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-[320px] bg-card border rounded-lg shadow-xl z-50 p-2 animate-in fade-in zoom-in duration-150">
          <div className="relative mb-2">
            <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search URLs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 h-8 text-xs bg-background"
              autoFocus
            />
          </div>
          
          <div className="max-h-[250px] overflow-auto space-y-0.5 custom-scrollbar">
            {filteredOptions.length === 0 ? (
              <p className="text-[10px] text-muted-foreground text-center py-4">No URLs found</p>
            ) : (
              filteredOptions.map((opt) => {
                const isSel = selected.includes(opt);
                return (
                  <button
                    key={opt}
                    onClick={() => toggle(opt)}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-[10px] text-left transition-colors ${isSel ? "bg-primary/10 text-primary" : "hover:bg-accent"}`}
                  >
                    <div className={`w-3.5 h-3.5 border rounded flex items-center justify-center ${isSel ? "bg-primary border-primary" : "border-muted-foreground/30"}`}>
                      {isSel && <Check size={10} className="text-white" />}
                    </div>
                    <span className="truncate flex-1">{opt.replace(/^https?:\/\//, "")}</span>
                  </button>
                );
              })
            )}
          </div>

          {selected.length > 0 && (
            <div className="mt-2 pt-2 border-t flex justify-between items-center px-1">
              <span className="text-[9px] text-muted-foreground">{selected.length} selected</span>
              <button 
                onClick={() => onChange([])}
                className="text-[9px] text-primary hover:underline font-medium flex items-center gap-1"
              >
                <X size={10} /> Clear all
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
