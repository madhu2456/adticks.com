"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { MapPin, Grid3x3, RefreshCw, BadgeCheck } from "lucide-react";
import {
  useCitations, useConsistency, useLocalGrid, useRunLocalGrid,
} from "@/hooks/useSEO";

export function LocalSEOSuite({ projectId }: { projectId: string }) {
  return (
    <Tabs defaultValue="consistency" className="space-y-4">
      <TabsList>
        <TabsTrigger value="consistency">NAP Consistency</TabsTrigger>
        <TabsTrigger value="grid">Local Rank Grid</TabsTrigger>
      </TabsList>
      <TabsContent value="consistency"><ConsistencyTab projectId={projectId}/></TabsContent>
      <TabsContent value="grid"><GridTab projectId={projectId}/></TabsContent>
    </Tabs>
  );
}

function ConsistencyTab({ projectId }: { projectId: string }) {
  const { data: citations, isLoading: cLoading } = useCitations(projectId);
  const { data: consistency, isLoading: kLoading } = useConsistency(projectId);

  return (
    <div className="space-y-4">
      {kLoading ? <Skeleton className="h-32"/> : consistency && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Stat label="Consistency Score" value={`${consistency.score}/100`} highlight={consistency.score >= 80}/>
          <Stat label="Listed In" value={`${consistency.directories_listed}/${consistency.directories_total}`}/>
          <Stat label="NAP Issues" value={consistency.issues_count} bad={consistency.issues_count > 0}/>
          <Stat label="Missing Directories" value={consistency.directories_missing?.length ?? 0}/>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><MapPin size={18}/> Citation Listings</CardTitle>
        </CardHeader>
        <CardContent>
          {cLoading ? <Skeleton className="h-32"/> : !citations?.length ? (
            <p className="text-sm text-text-muted text-center py-8">No citations tracked yet.</p>
          ) : (
            <div className="space-y-2">
              {citations.map((c: any) => (
                <div key={c.id} className="p-3 rounded border">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-sm">{c.directory}</p>
                      <p className="text-xs text-text-muted">{c.business_name} • {c.address}</p>
                      <p className="text-xs text-text-muted">{c.phone}</p>
                    </div>
                    <Badge className={c.consistency_score >= 80
                      ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30"
                      : "bg-red-500/10 text-red-700 border-red-500/30"}>
                      {c.consistency_score}/100
                    </Badge>
                  </div>
                  {c.issues?.length > 0 && (
                    <ul className="text-xs text-amber-700 mt-2">
                      {c.issues.map((i: string, idx: number) => <li key={idx}>• {i}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {consistency?.directories_missing?.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Directories you're missing from</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {consistency.directories_missing.slice(0, 20).map((d: string) => (
                <Badge key={d} className="bg-amber-500/10 text-amber-700 border-amber-500/30">{d}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function GridTab({ projectId }: { projectId: string }) {
  const [keyword, setKeyword] = useState("");
  const [lat, setLat] = useState(40.7128);
  const [lng, setLng] = useState(-74.0060);
  const [radius, setRadius] = useState(5);
  const [size, setSize] = useState(5);
  const { data: grid } = useLocalGrid(projectId, keyword || undefined);
  const run = useRunLocalGrid();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Grid3x3 size={18}/> Local Rank Grid</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            <Input placeholder="Keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)}/>
            <Input type="number" step="0.0001" placeholder="Center lat" value={lat} onChange={(e) => setLat(Number(e.target.value))}/>
            <Input type="number" step="0.0001" placeholder="Center lng" value={lng} onChange={(e) => setLng(Number(e.target.value))}/>
            <Input type="number" placeholder="Radius (km)" value={radius} onChange={(e) => setRadius(Number(e.target.value) || 5)}/>
            <Input type="number" placeholder="Grid size" value={size} onChange={(e) => setSize(Number(e.target.value) || 5)}/>
          </div>
          <Button
            className="mt-3 gap-2"
            onClick={() => keyword && run.mutate({ projectId, params: { keyword, center_lat: lat, center_lng: lng, radius_km: radius, grid_size: size } })}
            disabled={!keyword || run.isPending}
          >
            {run.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Grid3x3 size={16}/>}
            Run Grid
          </Button>
        </CardContent>
      </Card>

      {grid && grid.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Heatmap</CardTitle></CardHeader>
          <CardContent>
            <div
              className="grid gap-1"
              style={{ gridTemplateColumns: `repeat(${size}, 1fr)`, maxWidth: 400 }}
            >
              {grid.slice(0, size * size).map((cell: any, i: number) => {
                const r = cell.rank;
                let bg = "bg-slate-200 dark:bg-slate-700";
                if (r != null) {
                  if (r <= 3) bg = "bg-emerald-500";
                  else if (r <= 7) bg = "bg-amber-500";
                  else if (r <= 20) bg = "bg-orange-500";
                  else bg = "bg-red-500";
                }
                return (
                  <div key={i} className={`aspect-square ${bg} flex items-center justify-center text-white text-xs font-bold rounded`}>
                    {r ?? "—"}
                  </div>
                );
              })}
            </div>
            <div className="flex gap-3 mt-3 text-xs">
              <Legend color="bg-emerald-500" label="Top 3"/>
              <Legend color="bg-amber-500" label="4–7"/>
              <Legend color="bg-orange-500" label="8–20"/>
              <Legend color="bg-red-500" label="20+"/>
              <Legend color="bg-slate-200" label="Not ranked"/>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value, highlight, bad }: { label: string; value: any; highlight?: boolean; bad?: boolean }) {
  const color = highlight ? "text-emerald-600" : bad ? "text-red-600" : "";
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
        <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      </CardContent>
    </Card>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-3 h-3 rounded ${color}`}/>
      <span className="text-text-muted">{label}</span>
    </div>
  );
}
