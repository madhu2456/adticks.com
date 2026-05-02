"use client";
import React, { useRef, useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  FileUp, ScanText, RefreshCw, Settings2, 
  Check, Globe, Activity, Terminal, ExternalLink
} from "lucide-react";
import { useLogEvents, useUploadLogFile, useSyncRemoteLogs } from "@/hooks/useSEO";
import { useProject, useUpdateProject } from "@/hooks/useProject";
import { toast } from "react-hot-toast";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

export function LogFileAnalyzer({ projectId }: { projectId: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [bot, setBot] = useState("");
  const [summary, setSummary] = useState<any>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const { data: project } = useProject(projectId);
  const updateProject = useUpdateProject();
  const syncLogs = useSyncRemoteLogs();

  const [remoteUrl, setRemoteUrl] = useState(project?.remote_log_url || "");
  const [syncEnabled, setSyncEnabled] = useState(project?.log_sync_enabled || false);

  useEffect(() => {
    if (project) {
      setRemoteUrl(project.remote_log_url || "");
      setSyncEnabled(project.log_sync_enabled || false);
    }
  }, [project]);

  const { data: events, isLoading, refetch } = useLogEvents(projectId, bot || undefined);
  const upload = useUploadLogFile();

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await upload.mutateAsync({ projectId, file });
      setSummary(res.summary);
      toast.success("Log file uploaded and analyzed!");
      refetch();
    } catch (err) {
      toast.error("Failed to analyze log file");
    }
  };

  const handleSaveSettings = async () => {
    try {
      await updateProject.mutateAsync({
        id: projectId,
        data: {
          remote_log_url: remoteUrl,
          log_sync_enabled: syncEnabled
        } as any
      });
      toast.success("Automation settings saved");
      setShowSettings(false);
    } catch (err) {
      toast.error("Failed to save settings");
    }
  };

  const handleManualSync = async () => {
    if (!project?.remote_log_url) {
      toast.error("Please configure a Remote Log URL first");
      setShowSettings(true);
      return;
    }
    
    setIsSyncing(true);
    try {
      await syncLogs.mutateAsync(projectId);
      toast.success("Remote sync triggered");
      setTimeout(() => refetch(), 3000);
    } catch (err) {
      toast.error("Failed to start sync");
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <ScanText className="text-primary" /> Log Analyzer
        </h2>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings2 size={16} />
            {showSettings ? "Close Settings" : "Automation"}
          </Button>
          <Button 
            variant="primary" 
            size="sm" 
            className="gap-2"
            onClick={handleManualSync}
            disabled={isSyncing}
          >
            <RefreshCw size={16} className={isSyncing ? "animate-spin" : ""} />
            Sync Now
          </Button>
        </div>
      </div>

      {showSettings && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-sm">Remote Log Automation</CardTitle>
            <CardDescription className="text-xs">
              Automatically fetch and analyze your server logs daily.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="remote-url" className="text-xs">Remote Access Log URL</Label>
              <Input 
                id="remote-url"
                placeholder="https://yourserver.com/logs/access.log"
                value={remoteUrl}
                onChange={(e) => setRemoteUrl(e.target.value)}
                className="bg-background"
              />
              <p className="text-[10px] text-text-muted">
                Tip: Ensure this URL is accessible or use a secret token in the URL.
              </p>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-xs">Enable Daily Sync</Label>
                <p className="text-[10px] text-text-muted">Runs every 24 hours automatically.</p>
              </div>
              <Switch 
                checked={syncEnabled}
                onCheckedChange={setSyncEnabled}
              />
            </div>
            <Button size="sm" className="w-full" onClick={handleSaveSettings}>
              Save Automation Settings
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-md">
            <Activity size={18} className="text-primary"/> Recent Bot Activity
          </CardTitle>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <span className="text-xs text-text-muted">Filter Bot:</span>
               <select 
                 className="bg-background border rounded px-2 py-1 text-xs"
                 value={bot}
                 onChange={(e) => setBot(e.target.value)}
               >
                 <option value="">All Bots</option>
                 <option value="Googlebot">Googlebot</option>
                 <option value="Bingbot">Bingbot</option>
                 <option value="GPTBot">GPTBot</option>
                 <option value="ClaudeBot">ClaudeBot</option>
               </select>
            </div>
            <div>
              <input
                ref={inputRef}
                type="file"
                accept=".log,.txt,.gz"
                onChange={onChange}
                className="hidden"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => inputRef.current?.click()}
                disabled={upload.isPending}
                className="gap-2"
              >
                {upload.isPending ? <RefreshCw size={16} className="animate-spin"/> : <FileUp size={16}/>}
                Manual Upload
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2 py-8 text-center">
              <RefreshCw size={24} className="animate-spin mx-auto text-primary opacity-50" />
              <p className="text-sm text-text-muted">Loading crawl events...</p>
            </div>
          ) : events && events.length > 0 ? (
            <div className="overflow-hidden border rounded-lg">
              <table className="w-full text-sm text-left">
                <thead className="bg-muted text-text-muted text-[10px] uppercase tracking-wider">
                  <tr>
                    <th className="p-3">Bot / User Agent</th>
                    <th className="p-3">Requested URL</th>
                    <th className="p-3 text-center">Status</th>
                    <th className="p-3 text-right">Hits</th>
                    <th className="p-3 text-right">Last Crawled</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {events.map((ev: any, idx: number) => (
                    <tr key={idx} className="hover:bg-muted/50 transition-colors">
                      <td className="p-3">
                        <div className="flex flex-col">
                          <span className="font-medium">{ev.bot}</span>
                        </div>
                      </td>
                      <td className="p-3 max-w-xs truncate">
                        <code className="text-[10px] bg-muted px-1 py-0.5 rounded">{ev.url}</code>
                      </td>
                      <td className="p-3 text-center">
                        <Badge variant={ev.status_code < 400 ? "success" : "destructive"} className="text-[10px]">
                          {ev.status_code}
                        </Badge>
                      </td>
                      <td className="p-3 text-right font-mono">{ev.hits}</td>
                      <td className="p-3 text-right text-text-muted text-[11px]">
                        {new Date(ev.last_crawled).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center border-2 border-dashed rounded-lg bg-muted/20">
              <Terminal size={40} className="mx-auto text-text-muted mb-4 opacity-20" />
              <h3 className="text-lg font-medium text-text-muted">No crawl data found</h3>
              <p className="text-sm text-text-muted max-w-sm mx-auto mt-2">
                Configure a remote log URL or upload an access log file to see how search engines and AI bots are crawling your site.
              </p>
            </div>
          )}
          
          <div className="mt-4 p-3 bg-muted/30 rounded border border-dashed text-[11px] text-text-muted flex items-start gap-2">
             <Globe size={14} className="mt-0.5 text-primary" />
             <div>
                <p className="font-medium text-text-1 mb-1">Supported Formats</p>
                <p>Nginx/Apache Combined Log Format is supported. The analyzer tracks crawl budget, orphan pages, and status code distributions.</p>
             </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ label, value, bad = false }: { label: string; value: string | number; bad?: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-text-muted">{label}</p>
        <p className={`text-2xl font-bold mt-1 ${bad ? "text-red-600" : ""}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
