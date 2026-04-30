"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileCode2, ShieldQuestion, Map, Layers3, RefreshCw, FileDown,
} from "lucide-react";
import {
  useGenerateSitemap, useValidateRobots, useGenerateSchema, useSchemaTemplates,
  useRunBulk, useBulkJobs, useBulkItems,
} from "@/hooks/useSEO";

export function ToolsHub({ projectId }: { projectId: string }) {
  return (
    <Tabs defaultValue="sitemap" className="space-y-4">
      <TabsList>
        <TabsTrigger value="sitemap">Sitemap Generator</TabsTrigger>
        <TabsTrigger value="robots">robots.txt Validator</TabsTrigger>
        <TabsTrigger value="schema">Schema Generator</TabsTrigger>
        <TabsTrigger value="bulk">Bulk URL Analyzer</TabsTrigger>
      </TabsList>
      <TabsContent value="sitemap"><SitemapTab projectId={projectId}/></TabsContent>
      <TabsContent value="robots"><RobotsTab projectId={projectId}/></TabsContent>
      <TabsContent value="schema"><SchemaTab projectId={projectId}/></TabsContent>
      <TabsContent value="bulk"><BulkTab projectId={projectId}/></TabsContent>
    </Tabs>
  );
}

function SitemapTab({ projectId }: { projectId: string }) {
  const [urls, setUrls] = useState("");
  const gen = useGenerateSitemap();
  const run = () => {
    const list = urls.split(/[\s,]+/).filter(Boolean).map((u) => ({ url: u }));
    gen.mutate({ projectId, payload: { urls: list } });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Map size={18}/> XML Sitemap Generator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <textarea
          placeholder="One URL per line"
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          className="w-full min-h-[150px] p-3 rounded border bg-card text-sm font-mono"
        />
        <Button onClick={run} disabled={!urls || gen.isPending} className="gap-2">
          {gen.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Map size={16}/>}
          Generate Sitemap
        </Button>
        {gen.data && (
          <div className="p-3 rounded border bg-card-hover">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm">Generated {gen.data.url_count} URLs</p>
              {gen.data.file_url && (
                <a href={gen.data.file_url} target="_blank" rel="noreferrer">
                  <Button variant="outline" size="sm" className="gap-2"><FileDown size={14}/> Download</Button>
                </a>
              )}
            </div>
            <pre className="text-xs overflow-auto max-h-64">{gen.data.xml_preview}</pre>
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
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><ShieldQuestion size={18}/> robots.txt Validator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input placeholder="https://example.com/robots.txt (or paste content below)" value={url} onChange={(e) => setUrl(e.target.value)}/>
        <textarea
          placeholder="Paste robots.txt content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full min-h-[150px] p-3 rounded border bg-card text-sm font-mono"
        />
        <Button onClick={() => validate.mutate({ projectId, payload: { url: url || undefined, raw_content: content || undefined } })}
                disabled={(!content && !url) || validate.isPending} className="gap-2">
          {validate.isPending ? <RefreshCw size={16} className="animate-spin"/> : <ShieldQuestion size={16}/>}
          Validate
        </Button>
        {validate.data && (
          <div className="space-y-2">
            <Badge className={validate.data.is_valid
              ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30"
              : "bg-red-500/10 text-red-700 border-red-500/30"}>
              {validate.data.is_valid ? "Valid" : "Has errors"}
            </Badge>
            {validate.data.issues?.length > 0 && (
              <div className="space-y-1">
                {validate.data.issues.map((i: any, idx: number) => (
                  <div key={idx} className={`p-2 rounded text-xs border ${
                    i.severity === "error" ? "bg-red-500/5 border-red-500/30" :
                    i.severity === "warning" ? "bg-amber-500/5 border-amber-500/30" :
                    "bg-blue-500/5 border-blue-500/30"
                  }`}>
                    <span className="font-mono">L{i.line}</span> [{i.severity}] {i.message}
                  </div>
                ))}
              </div>
            )}
            {validate.data.sitemap_directives?.length > 0 && (
              <div>
                <p className="text-xs text-text-muted">Sitemap directives:</p>
                <ul className="text-xs">
                  {validate.data.sitemap_directives.map((s: string, i: number) => <li key={i}>• {s}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
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
    <div className="space-y-3">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><FileCode2 size={18}/> JSON-LD Schema Generator</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <select value={schemaType} onChange={(e) => setSchemaType(e.target.value)} className="px-3 py-2 rounded border bg-card text-sm">
              {SCHEMA_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Template name"/>
          </div>
          <textarea
            value={inputs}
            onChange={(e) => setInputs(e.target.value)}
            className="w-full min-h-[160px] p-3 rounded border bg-card text-sm font-mono"
          />
          <Button onClick={run} disabled={gen.isPending} className="gap-2">
            {gen.isPending ? <RefreshCw size={16} className="animate-spin"/> : <FileCode2 size={16}/>}
            Generate JSON-LD
          </Button>
          {gen.data && (
            <pre className="p-3 rounded border bg-card-hover text-xs overflow-auto max-h-72">
{`<script type="application/ld+json">
${JSON.stringify(gen.data.json_ld, null, 2)}
</script>`}
            </pre>
          )}
        </CardContent>
      </Card>

      {templates && templates.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Saved templates</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {templates.map((t: any) => (
                <div key={t.id} className="p-2 rounded border flex items-center justify-between text-sm">
                  <div>
                    <span className="font-medium">{t.name}</span>
                    <Badge className="ml-2 bg-card-hover text-text-muted border-0">{t.schema_type}</Badge>
                  </div>
                  <span className="text-xs text-text-muted">{new Date(t.timestamp).toLocaleDateString()}</span>
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
    <div className="space-y-3">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Layers3 size={18}/> Bulk URL Analyzer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            placeholder={"One URL per line"}
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            className="w-full min-h-[140px] p-3 rounded border bg-card text-sm font-mono"
          />
          <div className="flex gap-2">
            <select value={jobType} onChange={(e) => setJobType(e.target.value as any)} className="px-3 py-2 rounded border bg-card text-sm">
              <option value="onpage">On-page audit</option>
              <option value="cwv">Core Web Vitals</option>
            </select>
            <Button onClick={launch} disabled={run.isPending || !urls} className="gap-2">
              {run.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Layers3 size={16}/>}
              Run Bulk
            </Button>
          </div>
        </CardContent>
      </Card>

      {jobs && jobs.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Recent jobs</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {jobs.map((j: any) => (
                <button
                  key={j.id}
                  onClick={() => setActiveJob(j.id)}
                  className={`w-full text-left p-2 rounded border text-sm flex items-center justify-between hover:bg-card-hover ${activeJob === j.id ? "border-primary" : ""}`}
                >
                  <div>
                    <Badge className="bg-card-hover text-text-muted border-0">{j.job_type}</Badge>
                    <span className="ml-2">{j.completed_urls}/{j.total_urls} URLs</span>
                  </div>
                  <Badge className={j.status === "done" ? "bg-emerald-500/10 text-emerald-700" : "bg-amber-500/10 text-amber-700"}>{j.status}</Badge>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeJob && items && (
        <Card>
          <CardHeader><CardTitle className="text-base">Job results</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-auto max-h-[500px]">
              <table className="w-full text-sm">
                <thead className="text-xs text-text-muted">
                  <tr>
                    <th className="text-left p-2">URL</th>
                    <th className="text-left p-2">Status</th>
                    <th className="text-left p-2">Result preview</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it: any) => (
                    <tr key={it.id} className="border-t">
                      <td className="p-2 truncate max-w-xs">{it.url}</td>
                      <td className="p-2"><Badge className={it.status === "done" ? "bg-emerald-500/10 text-emerald-700" : "bg-red-500/10 text-red-700"}>{it.status}</Badge></td>
                      <td className="p-2 text-xs text-text-muted truncate max-w-md">
                        {it.error || JSON.stringify(it.result).slice(0, 120)}
                      </td>
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
