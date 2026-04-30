"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Mail, Plus, RefreshCw } from "lucide-react";
import {
  useCampaigns, useCreateCampaign, useProspects, useCreateProspect, useUpdateProspect,
} from "@/hooks/useSEO";

const STATUS_COLOR: Record<string, string> = {
  new: "bg-slate-500/10 text-slate-700 border-slate-500/30",
  contacted: "bg-blue-500/10 text-blue-700 border-blue-500/30",
  replied: "bg-amber-500/10 text-amber-700 border-amber-500/30",
  won: "bg-emerald-500/10 text-emerald-700 border-emerald-500/30",
  lost: "bg-red-500/10 text-red-700 border-red-500/30",
};

const STATUS_FLOW = ["new", "contacted", "replied", "won", "lost"];

export function OutreachTracker({ projectId }: { projectId: string }) {
  const [activeCampaign, setActiveCampaign] = useState<string | null>(null);
  const [newCampaignName, setNewCampaignName] = useState("");
  const { data: campaigns, isLoading } = useCampaigns(projectId);
  const create = useCreateCampaign();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Mail size={18}/> Link-Building Outreach</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input placeholder="New campaign name" value={newCampaignName} onChange={(e) => setNewCampaignName(e.target.value)}/>
            <Button
              onClick={() => newCampaignName && create.mutate({ projectId, payload: { name: newCampaignName } })}
              disabled={!newCampaignName || create.isPending} className="gap-2"
            >
              {create.isPending ? <RefreshCw size={16} className="animate-spin"/> : <Plus size={16}/>}
              New campaign
            </Button>
          </div>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-32"/> : !campaigns?.length ? (
        <p className="text-sm text-text-muted text-center py-8">No campaigns yet.</p>
      ) : (
        <Card>
          <CardHeader><CardTitle className="text-base">Campaigns</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {campaigns.map((c: any) => (
                <button
                  key={c.id}
                  onClick={() => setActiveCampaign(c.id)}
                  className={`w-full text-left p-3 rounded border hover:bg-card-hover ${activeCampaign === c.id ? "border-primary" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-sm">{c.name}</p>
                    <div className="flex gap-2">
                      <Badge className="bg-card-hover">{c.won_link_count}/{c.target_link_count} links</Badge>
                      <Badge className={STATUS_COLOR[c.status] || ""}>{c.status}</Badge>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeCampaign && <ProspectList projectId={projectId} campaignId={activeCampaign}/>}
    </div>
  );
}

function ProspectList({ projectId, campaignId }: { projectId: string; campaignId: string }) {
  const { data: prospects } = useProspects(projectId, campaignId);
  const create = useCreateProspect();
  const update = useUpdateProspect();
  const [newDomain, setNewDomain] = useState("");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Prospects</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2 mb-3">
          <Input placeholder="example.com" value={newDomain} onChange={(e) => setNewDomain(e.target.value)}/>
          <Button
            onClick={() => newDomain && create.mutate({ projectId, campaignId, payload: { domain: newDomain } })}
            disabled={!newDomain || create.isPending}
            className="gap-2"
          >
            <Plus size={16}/> Add
          </Button>
        </div>
        {!prospects?.length ? (
          <p className="text-sm text-text-muted text-center py-4">No prospects yet.</p>
        ) : (
          <div className="space-y-2">
            {prospects.map((p: any) => (
              <div key={p.id} className="p-3 rounded border flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-sm">{p.domain}</p>
                  <p className="text-xs text-text-muted">{p.contact_email || "—"} · DA {p.domain_authority}</p>
                </div>
                <select
                  value={p.status}
                  onChange={(e) => update.mutate({ projectId, prospectId: p.id, payload: { status: e.target.value } })}
                  className="px-2 py-1 rounded border bg-card text-xs"
                >
                  {STATUS_FLOW.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
