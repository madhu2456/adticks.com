"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2, Globe, Building2, Briefcase, Key } from "lucide-react";
import { useCreateProject } from "@/hooks/useProject";

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (projectId: string) => void;
}

const INDUSTRIES = [
  "SaaS / Software", "E-commerce", "Finance", "Healthcare",
  "Education", "Real Estate", "Travel", "Agency / Marketing", "Other",
];

export function ProjectModal({ isOpen, onClose, onSuccess }: ProjectModalProps) {
  const [form, setForm] = useState({ 
    brand_name: "", 
    domain: "", 
    industry: INDUSTRIES[0],
    seed_keywords: ""
  });
  const [error, setError] = useState<string | null>(null);
  const createProject = useCreateProject();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.brand_name || !form.domain) {
      setError("Please fill in all required fields.");
      return;
    }

    const payload = {
      brand_name: form.brand_name,
      domain: form.domain,
      industry: form.industry,
      seed_keywords: form.seed_keywords 
        ? form.seed_keywords.split(',').map(k => k.trim()).filter(Boolean)
        : []
    };

    try {
      const project = await createProject.mutateAsync(payload as any);
      setForm({ brand_name: "", domain: "", industry: INDUSTRIES[0], seed_keywords: "" });
      onSuccess?.(project.id);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to create project. Please try again.");
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="relative w-full max-w-md bg-[#1e293b] border border-[#334155] rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#334155]">
              <h3 className="text-lg font-bold text-[#f1f5f9]">Create New Project</h3>
              <button
                onClick={onClose}
                className="text-[#94a3b8] hover:text-[#f1f5f9] transition-colors p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <div className="bg-danger/10 border border-danger/20 text-danger text-xs px-3 py-2 rounded-lg">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Brand Name</label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#475569]">
                    <Building2 className="h-4 w-4" />
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Acme Corp"
                    value={form.brand_name}
                    onChange={(e) => setForm({ ...form, brand_name: e.target.value })}
                    className="w-full bg-[#0f172a] border border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#f1f5f9] focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Primary Domain</label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#475569]">
                    <Globe className="h-4 w-4" />
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="e.g. acme.com"
                    value={form.domain}
                    onChange={(e) => setForm({ ...form, domain: e.target.value })}
                    className="w-full bg-[#0f172a] border border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#f1f5f9] focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Industry</label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#475569]">
                    <Briefcase className="h-4 w-4" />
                  </div>
                  <select
                    value={form.industry}
                    onChange={(e) => setForm({ ...form, industry: e.target.value })}
                    className="w-full bg-[#0f172a] border border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#f1f5f9] focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 transition-all appearance-none"
                  >
                    {INDUSTRIES.map((ind) => (
                      <option key={ind} value={ind}>{ind}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Seed Keywords (Optional)</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-[#475569]">
                    <Key className="h-4 w-4" />
                  </div>
                  <textarea
                    placeholder="e.g. coffee beans, organic tea (comma separated)"
                    value={form.seed_keywords}
                    onChange={(e) => setForm({ ...form, seed_keywords: e.target.value })}
                    rows={2}
                    className="w-full bg-[#0f172a] border border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#f1f5f9] focus:outline-none focus:ring-2 focus:ring-[#6366f1]/40 transition-all resize-none"
                  />
                </div>
                <p className="text-[10px] text-[#64748b]">Helps AI find the most relevant rankings and opportunities.</p>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={createProject.isPending}
                  className="w-full bg-[#6366f1] hover:bg-[#4f46e5] text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-[#6366f1]/25 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createProject.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Create Project"
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
