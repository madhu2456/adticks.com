"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileCode2, ShieldQuestion, Map, Layers3, RefreshCw, FileDown,
  Globe, Megaphone, Bell, FileSearch, ChevronRight, Presentation, Zap, Network
} from "lucide-react";
import {
  useGenerateSitemap, useValidateRobots, useGenerateSchema, useSchemaTemplates,
  useRunBulk, useBulkJobs, useBulkItems,
  useClusters, useBuildCluster, useDeleteCluster,
} from "@/hooks/useSEO";
import { TrafficAnalytics } from "./TrafficAnalytics";
import { PPCResearch } from "./PPCResearch";
import { BrandMonitor } from "./BrandMonitor";
import { ContentExplorer } from "./ContentExplorer";
import { DomainOverview } from "./DomainOverview";
import { BulkKeywordChecker } from "./BulkKeywordChecker";
import { TopicClusters } from "./TopicClusters";

type ToolId = "traffic" | "ppc" | "brand" | "content" | "bulk" | "sitemap" | "robots" | "schema" | "overview" | "bulk-kw" | "clusters";

export function ToolsHub({ projectId }: { projectId: string }) {
  const [activeTool, setActiveTool] = useState<ToolId>("overview");

  const categories = [
    {
      name: "Competitive Intelligence",
      tools: [
        { id: "overview", name: "Site Explorer", icon: Presentation, desc: "Deep dive into any domain" },
        { id: "traffic", name: "Traffic Analytics", icon: Globe, desc: "Estimate domain traffic & engagement" },
        { id: "ppc", name: "PPC Research", icon: Megaphone, desc: "Spy on competitor ad spend & keywords" },
        { id: "content", name: "Content Explorer", icon: FileSearch, desc: "Find most shared content by topic" },
      ]
    },
    {
      name: "Keyword Strategy",
      tools: [
        { id: "bulk-kw", name: "Bulk Checker", icon: Zap, desc: "Check volume/KD for keyword lists" },
        { id: "clusters", name: "Topic Clusters", icon: Network, desc: "Group keywords semantically" },
      ]
    },
    {
      name: "Brand & PR",
      tools: [
        { id: "brand", name: "Brand Monitor", icon: Bell, desc: "Track unlinked brand mentions" },
      ]
    },
    {
      name: "Technical Utilities",
      tools: [
        { id: "bulk", name: "Bulk Analyzer", icon: Layers3, desc: "Run audits on multiple URLs" },
        { id: "sitemap", name: "Sitemap Generator", icon: Map, desc: "Create XML sitemaps" },
        { id: "robots", name: "Robots.txt Validator", icon: ShieldQuestion, desc: "Check robots.txt rules" },
        { id: "schema", name: "Schema Generator", icon: FileCode2, desc: "Build JSON-LD structured data" },
      ]
    }
  ];

  const renderActiveTool = () => {
    switch (activeTool) {
      case "overview": return <DomainOverview projectId={projectId} />;
      case "traffic": return <TrafficAnalytics projectId={projectId} />;
      case "ppc": return <PPCResearch projectId={projectId} />;
      case "brand": return <BrandMonitor projectId={projectId} />;
      case "content": return <ContentExplorer projectId={projectId} />;
      case "bulk-kw": return <BulkKeywordChecker projectId={projectId} />;
      case "clusters": return <TopicClusters projectId={projectId} />;
      case "bulk": return <BulkTab projectId={projectId} />;
      case "sitemap": return <SitemapTab projectId={projectId} />;
      case "robots": return <RobotsTab projectId={projectId} />;
      case "schema": return <SchemaTab projectId={projectId} />;
      default: return null;
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6">
      {/* Sidebar Navigation */}
      <div className="w-full md:w-64 flex-shrink-0 space-y-6">
        {categories.map((category) => (
          <div key={category.name}>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-2">
              {category.name}
            </h4>
            <div className="space-y-1">
              {category.tools.map((tool) => {
                const isActive = activeTool === tool.id;
                const Icon = tool.icon;
                return (
                  <button
                    key={tool.id}
                    onClick={() => setActiveTool(tool.id as ToolId)}
                    className={`w-full flex items-center justify-between p-2 rounded-lg text-sm transition-all duration-200 group
                      ${isActive 
                        ? "bg-primary/10 text-primary font-medium" 
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-1.5 rounded-md ${isActive ? "bg-primary/20" : "bg-transparent group-hover:bg-slate-200 dark:group-hover:bg-slate-700"}`}>
                        <Icon size={16} />
                      </div>
                      <div className="text-left">
                        <div className="leading-none mb-1">{tool.name}</div>
                        <div className={`text-[10px] hidden md:block ${isActive ? "text-primary/70" : "text-muted-foreground"}`}>
                          {tool.desc}
                        </div>
                      </div>
                    </div>
                    {isActive && <ChevronRight size={14} className="opacity-50" />}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 bg-slate-50/50 dark:bg-slate-900/20 p-1 md:p-4 rounded-xl border border-transparent md:border-slate-100 dark:md:border-slate-800">
        {renderActiveTool()}
      </div>
    </div>
  );
}

// --- Technical Utilities Components (Polished UI versions) ---

function SitemapTab({ projectId }: { projectId: string }) {
  const [urls, setUrls] = useState("");
  const gen = useGenerateSitemap();
  const run = () => {
    const list = urls.split(/[\s,]+/).filter(Boolean).map((u) => ({ url: u }));
    gen.mutate({ projectId, payload: { urls: list } });
  };

  return (
    <Card className="border-none shadow-none bg-transparent">
      <CardHeader className="px-0">
        <CardTitle className="text-xl">XML Sitemap Generator</CardTitle>
        <CardDescription>Generate standard XML sitemaps for your crawled pages or a custom URL list.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 px-0">
        <textarea
          placeholder="Paste one URL per line..."
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          className="w-full min-h-[200px] p-4 rounded-lg border bg-background text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none transition-shadow"
        />
        <Button onClick={run} disabled={!urls || gen.isPending} className="gap-2 w-full md:w-auto">
          {gen.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Map size={16}/>}
          Generate Sitemap
        </Button>
        {gen.data && (
          <div className="p-4 rounded-lg border bg-card shadow-sm animate-in fade-in slide-in-from-bottom-4 mt-6">
            <div className="flex items-center justify-between mb-4 pb-4 border-b">
              <p className="text-sm font-medium">Generated {gen.data.url_count} URLs successfully</p>
              {gen.data.file_url && (
                <a href={gen.data.file_url} target="_blank" rel="noreferrer">
                  <Button variant="outline" size="sm" className="gap-2"><FileDown size={14}/> Download XML</Button>
                </a>
              )}
            </div>
            <pre className="text-xs overflow-auto max-h-96 p-4 bg-slate-950 text-slate-50 rounded-md">
              {gen.data.xml_preview}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RobotsTab({ projectId }: { projectId: string }) {
  const [content, setContent] = useState("");
  const [url, setUrl] = useState("");
  const validate = useValidateRobots();

  return (
    <Card className="border-none shadow-none bg-transparent">
      <CardHeader className="px-0">
        <CardTitle className="text-xl">robots.txt Validator</CardTitle>
        <CardDescription>Ensure search engines can properly crawl your site without hitting blocked paths.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 px-0">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-4">
             <Input 
              placeholder="Fetch from URL (e.g. https://example.com/robots.txt)" 
              value={url} 
              onChange={(e) => setUrl(e.target.value)}
              className="bg-background"
            />
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="flex-1 h-px bg-border"></div>
              <span>OR</span>
              <div className="flex-1 h-px bg-border"></div>
            </div>
            <textarea
              placeholder="Paste robots.txt content here directly..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full min-h-[200px] p-4 rounded-lg border bg-background text-sm font-mono focus:ring-2 outline-none"
            />
            <Button onClick={() => validate.mutate({ projectId, payload: { url: url || undefined, raw_content: content || undefined } })}
                    disabled={(!content && !url) || validate.isPending} className="gap-2 w-full">
              {validate.isPending ? <RefreshCw size={16} className="animate-spin"/> : <ShieldQuestion size={16}/>}
              Validate Rules
            </Button>
          </div>

          <div>
            {validate.data ? (
              <div className="space-y-4 p-4 rounded-lg border bg-card h-full">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-sm">Validation Results</h4>
                  <Badge className={validate.data.is_valid
                    ? "bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/20 border-none"
                    : "bg-red-500/10 text-red-700 hover:bg-red-500/20 border-none"}>
                    {validate.data.is_valid ? "Valid Syntax" : "Syntax Errors Found"}
                  </Badge>
                </div>
                
                {validate.data.issues?.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground mb-2">Issues detected:</p>
                    {validate.data.issues.map((i: any, idx: number) => (
                      <div key={idx} className={`p-3 rounded-md text-xs border ${
                        i.severity === "error" ? "bg-red-50 text-red-900 border-red-200" :
                        i.severity === "warning" ? "bg-amber-50 text-amber-900 border-amber-200" :
                        "bg-blue-50 text-blue-900 border-blue-200"
                      }`}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono bg-white/50 px-1 rounded">Line {i.line}</span>
                          <span className="font-semibold capitalize">{i.severity}</span>
                        </div>
                        <p>{i.message}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-8 text-center text-emerald-600 text-sm">
                    No syntax errors found. Good to go!
                  </div>
                )}

                {validate.data.sitemap_directives?.length > 0 && (
                  <div className="pt-4 border-t mt-4">
                    <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Detected Sitemaps</p>
                    <ul className="text-xs space-y-1">
                      {validate.data.sitemap_directives.map((s: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <Map size={12} className="mt-0.5 text-primary" />
                          <span className="break-all">{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center border border-dashed rounded-lg bg-slate-50/50 dark:bg-slate-900/50 p-6 text-center text-muted-foreground text-sm">
                Enter a URL or paste rules to see validation results here.
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

const SCHEMA_TYPES = [
  "Article", "BlogPosting", "Product", "FAQPage", "HowTo",
  "BreadcrumbList", "Organization", "LocalBusiness", "Event",
  "Recipe", "Review", "VideoObject", "JobPosting", "WebSite", "Person",
];

function SchemaTab({ projectId }: { projectId: string }) {
  const [schemaType, setSchemaType] = useState("Article");
  const [name, setName] = useState("My schema");
  const [inputs, setInputs] = useState<string>('{\n  "headline": "Example article",\n  "author_name": "Jane",\n  "date_published": "2026-01-01",\n  "publisher_name": "Adticks"\n}');
  const gen = useGenerateSchema();
  const { data: templates } = useSchemaTemplates(projectId);

  const run = () => {
    let parsed: any = {};
    try { parsed = JSON.parse(inputs); } catch { return alert("Invalid JSON in inputs"); }
    gen.mutate({ projectId, payload: { schema_type: schemaType, name, inputs: parsed } });
  };

  return (
    <div className="space-y-6">
      <Card className="border-none shadow-none bg-transparent">
        <CardHeader className="px-0">
          <CardTitle className="text-xl">JSON-LD Schema Generator</CardTitle>
          <CardDescription>Generate structured data markup to help search engines understand your content.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-medium px-1">Schema Type</label>
              <select 
                value={schemaType} 
                onChange={(e) => setSchemaType(e.target.value)} 
                className="w-full px-3 py-2 rounded-md border bg-background text-sm outline-none focus:ring-2 focus:ring-primary/20"
              >
                {SCHEMA_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium px-1">Template Name (for saving)</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Default Blog Post" className="bg-background"/>
            </div>
          </div>
          
          <div className="space-y-2">
            <label className="text-xs font-medium px-1">Input Properties (JSON)</label>
            <textarea
              value={inputs}
              onChange={(e) => setInputs(e.target.value)}
              className="w-full min-h-[200px] p-4 rounded-lg border bg-slate-950 text-slate-50 text-sm font-mono outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          
          <Button onClick={run} disabled={gen.isPending} className="gap-2 w-full md:w-auto">
            {gen.isPending ? <RefreshCw size={16} className="animate-spin"/> : <FileCode2 size={16}/>}
            Generate JSON-LD
          </Button>
          
          {gen.data && (
            <div className="mt-6 animate-in fade-in">
              <h4 className="text-sm font-semibold mb-2">Generated Output:</h4>
              <pre className="p-4 rounded-lg border bg-slate-950 text-emerald-400 text-sm overflow-auto max-h-96 shadow-inner">
{`<script type="application/ld+json">
${JSON.stringify(gen.data.json_ld, null, 2)}
</script>`}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {templates && templates.length > 0 && (
        <Card>
          <CardHeader className="py-4">
            <CardTitle className="text-sm font-semibold">Saved Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {templates.map((t: any) => (
                <div key={t.id} className="p-3 rounded-lg border flex items-center justify-between text-sm bg-card hover:bg-accent transition-colors cursor-pointer">
                  <div className="flex items-center gap-3">
                    <FileCode2 size={16} className="text-muted-foreground" />
                    <div>
                      <span className="font-medium">{t.name}</span>
                      <Badge variant="secondary" className="ml-2 text-[10px] h-5">{t.schema_type}</Badge>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">{new Date(t.timestamp).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function BulkTab({ projectId }: { projectId: string }) {
  const [urls, setUrls] = useState("");
  const [jobType, setJobType] = useState<"onpage" | "cwv">("onpage");
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const { data: jobs } = useBulkJobs(projectId);
  const { data: items } = useBulkItems(projectId, activeJob);
  const run = useRunBulk();

  const launch = () => {
    const list = urls.split(/[\s,]+/).filter(Boolean);
    if (list.length === 0) return;
    run.mutateAsync({ projectId, urls: list, job_type: jobType }).then((j) => setActiveJob(j.id));
  };

  return (
    <div className="space-y-6">
      <Card className="border-none shadow-none bg-transparent">
        <CardHeader className="px-0">
          <CardTitle className="text-xl">Bulk URL Analyzer</CardTitle>
          <CardDescription>Run intensive checks across multiple specific pages asynchronously.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <textarea
            placeholder={"Paste one URL per line..."}
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            className="w-full min-h-[160px] p-4 rounded-lg border bg-background text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none"
          />
          <div className="flex flex-col sm:flex-row gap-3">
            <select 
              value={jobType} 
              onChange={(e) => setJobType(e.target.value as any)} 
              className="px-4 py-2.5 rounded-md border bg-background text-sm outline-none"
            >
              <option value="onpage">On-Page SEO Audit</option>
              <option value="cwv">Core Web Vitals Check</option>
            </select>
            <Button onClick={launch} disabled={run.isPending || !urls} className="gap-2 sm:flex-1 md:flex-none">
              {run.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Layers3 size={16}/>}
              Launch Bulk Analysis
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-4">
          <h3 className="font-semibold text-sm">Recent Jobs</h3>
          {jobs && jobs.length > 0 ? (
            <div className="space-y-2">
              {jobs.map((j: any) => (
                <button
                  key={j.id}
                  onClick={() => setActiveJob(j.id)}
                  className={`w-full text-left p-3 rounded-lg border text-sm transition-all duration-200 
                    ${activeJob === j.id 
                      ? "border-primary bg-primary/5 ring-1 ring-primary/20 shadow-sm" 
                      : "bg-card hover:bg-accent border-border"}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline" className="text-[10px] uppercase tracking-wider">{j.job_type}</Badge>
                    <Badge className={`text-[10px] ${j.status === "done" ? "bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/20 border-none" : "bg-amber-500/10 text-amber-700 hover:bg-amber-500/20 border-none"}`}>
                      {j.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{new Date(j.created_at).toLocaleDateString()}</span>
                    <span className="font-medium">{j.completed_urls} / {j.total_urls} URLs</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg text-center">
              No recent jobs
            </div>
          )}
        </div>

        <div className="md:col-span-2">
          {activeJob && items ? (
            <Card className="h-full overflow-hidden">
              <CardHeader className="py-4">
                <CardTitle className="text-sm font-semibold">Job Results</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-auto max-h-[500px]">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50 text-xs text-muted-foreground sticky top-0">
                      <tr>
                        <th className="text-left font-medium p-3">URL</th>
                        <th className="text-left font-medium p-3 w-24">Status</th>
                        <th className="text-left font-medium p-3">Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {items.map((it: any) => (
                        <tr key={it.id} className="hover:bg-muted/30 transition-colors">
                          <td className="p-3">
                            <div className="truncate max-w-[200px] text-xs font-medium" title={it.url}>
                              {it.url.replace(/^https?:\/\//, '')}
                            </div>
                          </td>
                          <td className="p-3">
                            <Badge variant="outline" className={`text-[10px] ${it.status === "done" ? "border-emerald-200 text-emerald-700" : "border-red-200 text-red-700"}`}>
                              {it.status}
                            </Badge>
                          </td>
                          <td className="p-3">
                            <div className="text-xs text-muted-foreground truncate max-w-xs font-mono bg-slate-50 dark:bg-slate-900 p-1.5 rounded">
                              {it.error || JSON.stringify(it.result).slice(0, 60) + '...'}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="h-full min-h-[300px] flex items-center justify-center border border-dashed rounded-lg text-muted-foreground text-sm">
              Select a job to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
