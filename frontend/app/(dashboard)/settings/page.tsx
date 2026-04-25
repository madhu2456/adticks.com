"use client";
import React, { useState } from "react";
import {
  User, FolderOpen, Link2, CreditCard, Key,
  CheckCircle, XCircle, Copy, RefreshCw, Eye, EyeOff,
  Plus, X, ChevronDown, BarChart2, Megaphone, TrendingUp,
  Zap, Crown, Loader2,
} from "lucide-react";
import { useActiveProject, useUpdateProject } from "@/hooks/useProject";
import { useUsage } from "@/hooks/useUsage";
import { useAlertModal } from "@/hooks/useAlertModal";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

type Tab = "profile" | "project" | "integrations" | "plan" | "api";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "project", label: "Project", icon: FolderOpen },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "plan", label: "Plan", icon: CreditCard },
  { id: "api", label: "API", icon: Key },
];

function SaveButton({ onClick, saved }: { onClick: () => void; saved: boolean }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-xl px-5 py-2.5 text-sm font-semibold transition-colors"
    >
      {saved ? (
        <>
          <CheckCircle className="h-4 w-4 text-[#10b981]" />
          Saved!
        </>
      ) : (
        "Save Changes"
      )}
    </button>
  );
}

function InputField({ label, value, onChange, type = "text", placeholder }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 focus:border-[#6366f1] transition-colors"
      />
    </div>
  );
}

function ProfileTab() {
  const { showAlert, AlertModal } = useAlertModal();
  const [form, setForm] = useState({ name: "", email: "", company: "" });
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    const user = getUser();
    if (user) {
      setForm({
        name: user.full_name || user.name || "",
        email: user.email || "",
        company: user.company_name || "",
      });
      setAvatarUrl(user.avatar_url || null);
    }
  }, []);

  async function handleAvatarClick() {
    fileInputRef.current?.click();
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const updatedUser = await api.auth.uploadAvatar(file);
      setAvatarUrl(updatedUser.avatar_url || null);
      
      const { setUser } = await import("@/lib/auth");
      setUser(updatedUser);
    } catch (err) {
      showAlert({
        title: "Upload Failed",
        message: "Failed to upload avatar. Please try again.",
        type: "error",
        confirmText: "Close",
      });
    } finally {
      setUploading(false);
    }
  }

  async function handleSave() {
    setLoading(true);
    try {
      const updatedUser = await api.auth.updateMe({
        full_name: form.name,
        email: form.email,
        company_name: form.company,
      });
      // Save updated user back to local storage
      const { setUser } = await import("@/lib/auth");
      setUser(updatedUser);
      
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      showAlert({
        title: "Save Failed",
        message: "Failed to save profile changes. Please try again.",
        type: "error",
        confirmText: "Close",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#f1f5f9] mb-1">Profile Settings</h2>
        <p className="text-sm text-[#94a3b8]">Update your personal information</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative group cursor-pointer" onClick={handleAvatarClick}>
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center text-white font-bold text-xl overflow-hidden">
            {avatarUrl ? (
              <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
            ) : (
              form.name.charAt(0) || "U"
            )}
            
            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Plus className="w-5 h-5 text-white" />
            </div>
          </div>
          
          {uploading && (
            <div className="absolute inset-0 bg-black/60 rounded-full flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-white animate-spin" />
            </div>
          )}
        </div>
        
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept="image/*"
          onChange={handleFileChange}
        />
        
        <div>
          <p className="text-sm font-medium text-[#f1f5f9]">{form.name || "Your Name"}</p>
          <p className="text-xs text-[#94a3b8]">{form.email || "user@example.com"}</p>
          <button 
            onClick={handleAvatarClick}
            className="text-xs text-[#6366f1] hover:text-[#8b5cf6] mt-1 transition-colors disabled:opacity-50"
            disabled={uploading}
          >
            {uploading ? "Uploading..." : "Change avatar"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InputField label="Full Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="Your full name" />
        <InputField label="Email Address" value={form.email} onChange={(v) => setForm({ ...form, email: v })} type="email" placeholder="your@email.com" />
        <InputField label="Company Name" value={form.company} onChange={(v) => setForm({ ...form, company: v })} placeholder="Your company" />
      </div>

      <div className="pt-2">
        <SaveButton onClick={handleSave} saved={saved} />
      </div>

      {/* Danger Zone */}
      <div className="pt-6 border-t border-[#334155]">
        <h3 className="text-sm font-semibold text-[#ef4444] mb-1">Danger Zone</h3>
        <p className="text-xs text-[#94a3b8] mb-4">Actions here are permanent and affect the entire system cache.</p>
        
        <button
          onClick={async () => {
            showAlert({
              title: "Purge Everything?",
              message: "This will clear all cached data and background task states across the entire system. This action cannot be undone.",
              type: "warning",
              confirmText: "Purge All",
              cancelText: "Cancel",
              onConfirm: async () => {
                try {
                  await api.cache.purgeAll();
                  showAlert({
                    title: "Success",
                    message: "System-wide cache has been purged successfully.",
                    type: "success",
                  });
                } catch (err: any) {
                  showAlert({
                    title: "Purge Failed",
                    message: err.response?.data?.detail || "You may not have permission to perform this action.",
                    type: "error",
                  });
                }
              }
            });
          }}
          className="flex items-center gap-2 bg-[#ef4444]/10 hover:bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/20 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all active:scale-95"
        >
          <XCircle className="h-4 w-4" />
          Purge Everything
        </button>
      </div>
      {AlertModal}
    </div>
  );
}

function ProjectTab() {
  const { activeProject } = useActiveProject();
  const updateProject = useUpdateProject();
  const { showAlert, AlertModal } = useAlertModal();
  
  const [form, setForm] = useState({ 
    brand_name: "", 
    domain: "", 
    industry: "SaaS / Marketing" 
  });
  
  const [competitors, setCompetitors] = useState(["Competitor A", "Competitor B"]);
  const [newComp, setNewComp] = useState("");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (activeProject) {
      setForm({
        brand_name: activeProject.brand_name || activeProject.name || "",
        domain: activeProject.domain || "",
        industry: activeProject.industry || "SaaS / Marketing",
      });
    }
  }, [activeProject]);

  function addCompetitor() {
    if (newComp.trim() && !competitors.includes(newComp.trim())) {
      setCompetitors([...competitors, newComp.trim()]);
      setNewComp("");
    }
  }

  function removeCompetitor(c: string) {
    setCompetitors(competitors.filter((x) => x !== c));
  }

  async function handleSave() {
    if (!activeProject) return;
    setLoading(true);
    try {
      await updateProject.mutateAsync({
        id: activeProject.id,
        data: form
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      showAlert({
        title: "Update Failed",
        message: "Failed to update project settings. Please try again.",
        type: "error",
        confirmText: "Close",
      });
    } finally {
      setLoading(false);
    }
  }

  const industries = [
    "SaaS / Marketing", "E-commerce", "Finance", "Healthcare",
    "Education", "Real Estate", "Travel", "Media / Publishing", "Other",
  ];

  if (!activeProject) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FolderOpen className="h-12 w-12 text-[#475569] mb-4" />
        <h2 className="text-lg font-semibold text-[#f1f5f9]">No Project Selected</h2>
        <p className="text-sm text-[#94a3b8] max-w-xs mt-1">Select or create a project to manage its settings.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#f1f5f9] mb-1">Project Settings</h2>
        <p className="text-sm text-[#94a3b8]">Configure your tracked domain and competitors</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InputField label="Brand Name" value={form.brand_name} onChange={(v) => setForm({ ...form, brand_name: v })} placeholder="Your Brand" />
        <InputField label="Project Domain" value={form.domain} onChange={(v) => setForm({ ...form, domain: v })} placeholder="example.com" />
      </div>

      <div>
        <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">Industry</label>
        <div className="relative">
          <select
            value={form.industry}
            onChange={(e) => setForm({ ...form, industry: e.target.value })}
            className="w-full appearance-none rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] px-3.5 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 focus:border-[#6366f1] transition-colors cursor-pointer"
          >
            {industries.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#475569] pointer-events-none" />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-[#f1f5f9] mb-2">Competitors</label>
        <div className="flex flex-wrap gap-2 mb-3">
          {competitors.map((c) => (
            <span key={c} className="flex items-center gap-1.5 bg-[#334155] text-[#f1f5f9] rounded-lg px-3 py-1.5 text-sm">
              {c}
              <button onClick={() => removeCompetitor(c)} className="text-[#94a3b8] hover:text-[#ef4444] transition-colors">
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newComp}
            onChange={(e) => setNewComp(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addCompetitor()}
            placeholder="Add competitor..."
            className="flex-1 rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 focus:border-[#6366f1] transition-colors"
          />
          <button
            onClick={addCompetitor}
            className="flex items-center gap-1.5 bg-[#334155] hover:bg-[#475569] text-[#f1f5f9] rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add
          </button>
        </div>
      </div>

      <SaveButton onClick={handleSave} saved={saved} />
      {AlertModal}
    </div>
  );
}

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  connected: boolean;
}

function IntegrationsTab() {
  const { activeProject } = useActiveProject();
  const { showAlert, AlertModal } = useAlertModal();

  const integrations = [
    {
      id: "gsc",
      name: "Google Search Console",
      description: "Track impressions, clicks, CTR and ranking positions",
      icon: BarChart2,
      color: "#6366f1",
      connected: activeProject?.gsc_connected || false,
      available: true,
    },
    {
      id: "ads",
      name: "Google Ads",
      description: "Monitor spend, conversions, ROAS and campaign data",
      icon: Megaphone,
      color: "#f97316",
      connected: activeProject?.ads_connected || false,
      available: false,
    },
    {
      id: "ga4",
      name: "Google Analytics 4",
      description: "Import sessions, goals and user behavior data",
      icon: TrendingUp,
      color: "#10b981",
      connected: false,
      available: false,
    },
  ];

  async function handleConnect(id: string) {
    if (id === "gsc") {
      if (!activeProject) {
        showAlert({
          title: "Project Required",
          message: "Please select a project first.",
          type: "warning",
          confirmText: "OK",
        });
        return;
      }
      try {
        const { url } = await api.gsc.getAuthUrl(activeProject.id);
        window.location.href = url;
      } catch (err) {
        showAlert({
          title: "Connection Failed",
          message: "Failed to initialize connection. Please try again.",
          type: "error",
          confirmText: "Close",
        });
      }
    } else {
      showAlert({
        title: "Coming Soon",
        message: `${integrations.find(i => i.id === id)?.name} integration is coming soon! Contact support to join the beta.`,
        type: "info",
        confirmText: "Got it",
      });
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#f1f5f9] mb-1">Integrations</h2>
        <p className="text-sm text-[#94a3b8]">Connect your external data sources to AdTicks</p>
      </div>

      <div className="space-y-4">
        {integrations.map((i) => (
          <div
            key={i.id}
            className="flex items-center gap-4 bg-[#0f172a]/40 border border-[#334155] rounded-xl p-5"
          >
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: `${i.color}18` }}
            >
              <i.icon className="h-6 w-6" style={{ color: i.color }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-[#f1f5f9]">{i.name}</h3>
                {i.connected && (
                  <span className="flex items-center gap-1 text-[10px] font-semibold text-[#10b981] bg-[#10b981]/10 border border-[#10b981]/20 px-2 py-0.5 rounded-md">
                    <CheckCircle className="h-3 w-3" /> Connected
                  </span>
                )}
                {!i.available && !i.connected && (
                  <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-md uppercase tracking-wider">
                    COMING SOON
                  </span>
                )}
              </div>
              <p className="text-xs text-[#94a3b8]">{i.description}</p>
            </div>
            <button
              onClick={() => handleConnect(i.id)}
              disabled={i.connected}
              className={cn(
                "px-4 py-2 rounded-lg text-xs font-bold transition-all shrink-0",
                i.connected
                  ? "bg-white/[0.05] text-[#475569] cursor-default"
                  : "bg-white text-black hover:bg-white/90 active:scale-95"
              )}
            >
              {i.connected ? "Manage" : "Connect"}
            </button>
          </div>
        ))}
      </div>
      {AlertModal}
    </div>
  );
}

function PlanTab() {
  const { data: usage } = useUsage();
  const queryClient = useQueryClient();
  const { showAlert, AlertModal } = useAlertModal();
  const [upgrading, setUpgrading] = useState(false);

  const features = [
    { name: "AI Visibility Scans", free: "50/mo", pro: "Unlimited" },
    { name: "Keywords Tracked", free: "500", pro: "Unlimited" },
    { name: "Competitors Tracked", free: "3", pro: "10" },
    { name: "GSC Integration", free: true, pro: true },
    { name: "Google Ads Integration", free: false, pro: true },
    { name: "Custom Reports", free: false, pro: true },
    { name: "API Access", free: false, pro: true },
    { name: "Team Members", free: "1", pro: "10" },
    { name: "Priority Support", free: false, pro: true },
  ];

  const planName = usage?.plan === "free" ? "Free Trial" : (usage?.plan ? usage.plan.charAt(0).toUpperCase() + usage.plan.slice(1) : "Free Trial");
  const isPro = usage?.plan === "pro" || usage?.plan === "enterprise";

  async function handleUpgrade() {
    setUpgrading(true);
    try {
      await api.auth.upgrade();
      queryClient.invalidateQueries({ queryKey: ["usage"] });
      showAlert({
        title: "Upgrade Successful",
        message: "Successfully upgraded to Pro plan!",
        type: "success",
        confirmText: "Great",
      });
    } catch (error) {
      console.error("Upgrade failed:", error);
      showAlert({
        title: "Upgrade Failed",
        message: "Failed to upgrade. Please try again later.",
        type: "error",
        confirmText: "Close",
      });
    } finally {
      setUpgrading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#f1f5f9] mb-1">Plan &amp; Billing</h2>
        <p className="text-sm text-[#94a3b8]">Manage your subscription</p>
      </div>

      {/* Trial card */}
      {!isPro && (
        <div className="bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/10 border border-[#6366f1]/30 rounded-xl p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-5 w-5 text-[#6366f1]" />
                <span className="font-semibold text-[#f1f5f9]">{planName}</span>
                <span className="text-xs bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30 px-2 py-0.5 rounded-md font-semibold">
                  {usage?.days_remaining || 0} days remaining
                </span>
              </div>
              <p className="text-sm text-[#94a3b8]">Your trial includes full access to all Pro features.</p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            {[
              { label: "AI Scans Used", value: `${usage?.ai_scans_used || 0}/${usage?.ai_scans_limit || 50}` },
              { label: "Keywords Tracked", value: `${usage?.keywords_used || 0}/${usage?.keywords_limit || 500}` },
              { label: "Competitors", value: `${usage?.competitors_used || 0}/${usage?.competitors_limit || 3}` },
              { label: "Days Remaining", value: `${usage?.days_remaining || 0}` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-[#0f172a]/30 rounded-lg p-3">
                <p className="text-xs text-[#94a3b8]">{label}</p>
                <p className="text-lg font-bold text-[#f1f5f9] mt-0.5">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature comparison */}
      <div className="bg-[#0f172a]/30 border border-[#334155] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#334155]">
              <th className="px-5 py-3 text-left text-xs font-medium text-[#94a3b8] uppercase">Feature</th>
              <th className="px-5 py-3 text-center text-xs font-medium text-[#94a3b8] uppercase">Free</th>
              <th className="px-5 py-3 text-center text-xs font-semibold text-[#6366f1] uppercase">Pro</th>
            </tr>
          </thead>
          <tbody>
            {features.map((f) => (
              <tr key={f.name} className="border-t border-[#334155]/50">
                <td className="px-5 py-3 text-[#f1f5f9] text-sm">{f.name}</td>
                <td className="px-5 py-3 text-center">
                  {typeof f.free === "boolean" ? (
                    f.free ? (
                      <CheckCircle className="h-4 w-4 text-[#10b981] mx-auto" />
                    ) : (
                      <XCircle className="h-4 w-4 text-[#475569] mx-auto" />
                    )
                  ) : (
                    <span className="text-[#94a3b8] text-xs">{f.free}</span>
                  )}
                </td>
                <td className="px-5 py-3 text-center">
                  {typeof f.pro === "boolean" ? (
                    f.pro ? (
                      <CheckCircle className="h-4 w-4 text-[#10b981] mx-auto" />
                    ) : (
                      <XCircle className="h-4 w-4 text-[#475569] mx-auto" />
                    )
                  ) : (
                    <span className="text-[#6366f1] text-xs font-semibold">{f.pro}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!isPro && (
        <button 
          onClick={handleUpgrade}
          disabled={upgrading}
          className="flex items-center gap-2 bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] hover:opacity-90 text-white font-semibold rounded-xl px-6 py-3 text-sm transition-opacity shadow-lg shadow-[#6366f1]/25 disabled:opacity-60"
        >
          {upgrading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Crown className="h-4 w-4" />
          )}
          {upgrading ? "Upgrading..." : "Upgrade to Pro — $49/mo"}
        </button>
      )}
      {AlertModal}
    </div>
  );
}

function APITab() {
  const { data: usage } = useUsage();
  const [apiKey] = useState("No API Key generated yet.");
  const [showKey, setShowKey] = useState(false);
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleRegenerate() {
    setRegenerating(true);
    setTimeout(() => setRegenerating(false), 1500);
  }

  const maskedKey = apiKey.slice(0, 12) + "•".repeat(24) + apiKey.slice(-6);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#f1f5f9] mb-1">API Access</h2>
        <p className="text-sm text-[#94a3b8]">Integrate AdTicks into your own tools</p>
      </div>

      <div className="bg-[#0f172a]/40 border border-[#334155] rounded-xl p-5">
        <label className="block text-sm font-medium text-[#f1f5f9] mb-2">Your API Key</label>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-[#0f172a] border border-[#334155] rounded-lg px-3.5 py-2.5 font-mono text-sm text-[#94a3b8] overflow-hidden text-ellipsis whitespace-nowrap">
            {showKey ? apiKey : maskedKey}
          </div>
          <button
            onClick={() => setShowKey(!showKey)}
            className="p-2.5 rounded-lg bg-[#334155] hover:bg-[#475569] text-[#94a3b8] hover:text-[#f1f5f9] transition-colors"
            title={showKey ? "Hide key" : "Show key"}
          >
            {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-2.5 rounded-lg bg-[#334155] hover:bg-[#475569] text-sm font-medium transition-colors"
          >
            {copied ? (
              <><CheckCircle className="h-4 w-4 text-[#10b981]" /><span className="text-[#10b981]">Copied</span></>
            ) : (
              <><Copy className="h-4 w-4 text-[#94a3b8]" /><span className="text-[#94a3b8]">Copy</span></>
            )}
          </button>
        </div>
        <p className="text-xs text-[#475569] mt-2">Keep this key secret. Do not expose it in client-side code.</p>
      </div>

      {/* Usage stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Requests Today", value: usage?.api_requests_today?.toLocaleString() || 0 },
          { label: "Requests This Month", value: usage?.api_requests_month?.toLocaleString() || 0 },
          { label: "Rate Limit", value: usage?.api_rate_limit || "100/hr" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[#0f172a]/40 border border-[#334155] rounded-xl p-4">
            <p className="text-xs text-[#94a3b8] mb-1">{label}</p>
            <p className="text-xl font-bold text-[#f1f5f9]">{value}</p>
          </div>
        ))}
      </div>

      <button
        onClick={handleRegenerate}
        disabled={regenerating}
        className="flex items-center gap-2 bg-[#334155] hover:bg-[#475569] text-[#f1f5f9] rounded-xl px-5 py-2.5 text-sm font-medium transition-colors disabled:opacity-60"
      >
        <RefreshCw className={`h-4 w-4 ${regenerating ? "animate-spin" : ""}`} />
        {regenerating ? "Regenerating..." : "Regenerate API Key"}
      </button>

      <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/20 rounded-xl p-4">
        <p className="text-xs text-[#f59e0b] font-medium mb-1">Warning</p>
        <p className="text-xs text-[#94a3b8]">
          Regenerating your API key will invalidate the current key immediately. Any apps using the old key will stop working.
        </p>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("profile");

  const tabContent: Record<Tab, React.ReactNode> = {
    profile: <ProfileTab />,
    project: <ProjectTab />,
    integrations: <IntegrationsTab />,
    plan: <PlanTab />,
    api: <APITab />,
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#f1f5f9]">Settings</h1>
        <p className="text-sm text-[#94a3b8] mt-1">Manage your account and preferences</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar nav */}
        <aside className="w-48 shrink-0">
          <nav className="space-y-1 bg-[#1e293b] rounded-xl border border-[#334155] p-2">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === id
                    ? "bg-[#6366f1]/20 text-[#6366f1] border border-[#6366f1]/30"
                    : "text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#334155]"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Content */}
        <div className="flex-1 bg-[#1e293b] rounded-xl border border-[#334155] p-6">
          {tabContent[activeTab]}
        </div>
      </div>
    </div>
  );
}
