"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FileDown, FileText, RefreshCw } from "lucide-react";
import { useReports, useGenerateReport } from "@/hooks/useSEO";

const REPORT_TYPES = [
  { value: "full_seo", label: "Full SEO Report" },
  { value: "technical_audit", label: "Technical Audit" },
  { value: "keyword_research", label: "Keyword Research" },
  { value: "backlinks", label: "Backlink Profile" },
  { value: "local_seo", label: "Local SEO" },
  { value: "content", label: "Content Performance" },
];

export function ReportBuilder({ projectId }: { projectId: string }) {
  const [type, setType] = useState("full_seo");
  const [title, setTitle] = useState("Monthly SEO Report");
  const [brand, setBrand] = useState("AdTicks");
  const [color, setColor] = useState("#6366F1");
  const { data: reports, isLoading } = useReports(projectId);
  const generate = useGenerateReport();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><FileText size={18}/> White-Label Report Builder</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-text-muted mb-1 block">Report Type</label>
              <select value={type} onChange={(e) => setType(e.target.value)} className="w-full px-3 py-2 rounded border bg-card text-sm">
                {REPORT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Title</label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)}/>
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Brand name</label>
              <Input value={brand} onChange={(e) => setBrand(e.target.value)}/>
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Primary color</label>
              <div className="flex gap-2">
                <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="w-12 h-10 rounded border bg-card"/>
                <Input value={color} onChange={(e) => setColor(e.target.value)} className="flex-1"/>
              </div>
            </div>
          </div>
          <Button
            onClick={() => generate.mutate({ projectId, payload: { report_type: type, title, branding: { brand_name: brand, primary_color: color } } })}
            disabled={generate.isPending}
            className="gap-2"
          >
            {generate.isPending ? <RefreshCw size={16} className="animate-spin"/> : <FileDown size={16}/>}
            Generate Report
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Generated Reports</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32"/> : !reports?.length ? (
            <p className="text-sm text-text-muted text-center py-8">No reports generated yet.</p>
          ) : (
            <div className="space-y-2">
              {reports.map((r: any) => (
                <div key={r.id} className="p-3 rounded border flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{r.title}</p>
                    <p className="text-xs text-text-muted">
                      <Badge className="bg-card-hover text-text-muted border-0 mr-1">{r.report_type}</Badge>
                      {new Date(r.timestamp).toLocaleString()}
                    </p>
                  </div>
                  {r.file_url && (
                    <Button variant="outline" size="sm" asChild className="gap-2">
                      <a href={r.file_url} target="_blank" rel="noreferrer">
                        <FileDown size={14}/> Download
                      </a>
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
