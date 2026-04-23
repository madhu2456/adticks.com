"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, BarChart2, Sparkles, MapPin, 
  Activity, Megaphone, Zap, Settings, 
  User, LogOut, Moon, Sun, Laptop,
  ChevronRight, Command
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useProjects, useActiveProject } from "@/hooks/useProject";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setSearchQuery] = useState("");
  const { data: projects = [] } = useProjects();
  const { setActiveId } = useActiveProject();
  const { theme, setTheme } = useTheme();

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const navActions = [
    { id: "nav-ov", label: "Go to Overview", icon: BarChart2, action: () => router.push("/") },
    { id: "nav-seo", label: "SEO Hub", icon: Search, action: () => router.push("/seo") },
    { id: "nav-aeo", label: "AEO Hub", icon: Sparkles, action: () => router.push("/aeo") },
    { id: "nav-geo", label: "Local SEO", icon: MapPin, action: () => router.push("/geo") },
    { id: "nav-gsc", label: "Search Console", icon: Activity, action: () => router.push("/gsc") },
    { id: "nav-ads", label: "Google Ads", icon: Megaphone, action: () => router.push("/ads") },
    { id: "nav-set", label: "Settings", icon: Settings, action: () => router.push("/settings") },
  ];

  const themeActions = [
    { id: "th-dark", label: "Switch to Dark Mode", icon: Moon, action: () => setTheme("dark") },
    { id: "th-light", label: "Switch to Light Mode", icon: Sun, action: () => setTheme("light") },
    { id: "th-sys", label: "Use System Theme", icon: Laptop, action: () => setTheme("system") },
  ];

  const filteredNav = navActions.filter(a => a.label.toLowerCase().includes(query.toLowerCase()));
  const filteredProjects = projects.filter(p => p.brand_name?.toLowerCase().includes(query.toLowerCase()) || p.domain.toLowerCase().includes(query.toLowerCase()));

  const handleAction = (cb: () => void) => {
    cb();
    onClose();
    setSearchQuery("");
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-start justify-center pt-[15vh] px-4 sm:px-6">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/40 backdrop-blur-md"
          />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -10 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="relative w-full max-w-2xl bg-[#1e293b]/95 border border-[#334155] rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl"
          >
            {/* Search Input */}
            <div className="relative border-b border-[#334155] p-4">
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-[#94a3b8]" />
              <input
                autoFocus
                placeholder="Search tools, projects, or settings..."
                value={query}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent pl-10 pr-4 py-2 text-lg text-[#f1f5f9] focus:outline-none placeholder-[#475569]"
              />
              <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center gap-1.5 px-2 py-1 rounded bg-[#0f172a] border border-[#334155] text-[10px] font-bold text-[#94a3b8] uppercase">
                ESC to close
              </div>
            </div>

            {/* Results Area */}
            <div className="max-h-[60vh] overflow-y-auto custom-scroll p-2">
              
              {/* Tools & Navigation */}
              {filteredNav.length > 0 && (
                <div className="mb-4">
                  <p className="px-3 py-2 text-[10px] font-bold text-[#475569] uppercase tracking-widest">Tools & Navigation</p>
                  <div className="space-y-0.5">
                    {filteredNav.map((action) => (
                      <button
                        key={action.id}
                        onClick={() => handleAction(action.action)}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.05] transition-colors group text-left"
                      >
                        <div className="w-8 h-8 rounded-lg bg-[#0f172a] border border-[#334155] flex items-center justify-center group-hover:border-primary/50 transition-colors">
                          <action.icon className="h-4 w-4 text-[#94a3b8] group-hover:text-primary" />
                        </div>
                        <span className="flex-1 text-sm font-medium text-[#cbd5e1] group-hover:text-[#f1f5f9]">{action.label}</span>
                        <ChevronRight className="h-4 w-4 text-[#475569] opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects */}
              {filteredProjects.length > 0 && (
                <div className="mb-4">
                  <p className="px-3 py-2 text-[10px] font-bold text-[#475569] uppercase tracking-widest">Switch Project</p>
                  <div className="space-y-0.5">
                    {filteredProjects.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => handleAction(() => setActiveId(p.id))}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.05] transition-colors group text-left"
                      >
                        <div 
                          className="w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold text-white shrink-0"
                          style={{ background: `linear-gradient(135deg, ${p.color || '#6366f1'}, ${p.color || '#6366f1'}cc)` }}
                        >
                          {p.initials || (p.brand_name || p.name || "?")[0].toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#cbd5e1] group-hover:text-[#f1f5f9] truncate">{p.brand_name || p.name}</p>
                          <p className="text-[11px] text-[#475569] truncate">{p.domain}</p>
                        </div>
                        <span className="text-[10px] font-bold text-[#475569] mr-2">SWITCH</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Appearance */}
              {query === "" && (
                <div>
                  <p className="px-3 py-2 text-[10px] font-bold text-[#475569] uppercase tracking-widest">Appearance</p>
                  <div className="grid grid-cols-3 gap-1 px-1">
                    {themeActions.map((action) => (
                      <button
                        key={action.id}
                        onClick={() => handleAction(action.action)}
                        className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-white/[0.05] transition-colors group"
                      >
                        <div className="w-10 h-10 rounded-full bg-[#0f172a] border border-[#334155] flex items-center justify-center group-hover:border-primary/50 transition-colors">
                          <action.icon className="h-5 w-5 text-[#94a3b8] group-hover:text-primary" />
                        </div>
                        <span className="text-[10px] font-medium text-[#94a3b8] text-center">{action.label.replace("Switch to ", "")}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {filteredNav.length === 0 && filteredProjects.length === 0 && (
                <div className="py-12 text-center">
                  <div className="w-12 h-12 rounded-full bg-[#0f172a] border border-[#334155] flex items-center justify-center mx-auto mb-4">
                    <Search className="h-5 w-5 text-[#475569]" />
                  </div>
                  <p className="text-[#f1f5f9] font-medium">No results found for &ldquo;{query}&rdquo;</p>
                  <p className="text-sm text-[#475569] mt-1">Try searching for a tool or a project name.</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-[#0f172a]/50 px-4 py-3 border-t border-[#334155] flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5 text-[11px] text-[#475569]">
                  <kbd className="px-1.5 py-0.5 rounded bg-[#1e293b] border border-[#334155]">↵</kbd>
                  <span>to select</span>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-[#475569]">
                  <kbd className="px-1.5 py-0.5 rounded bg-[#1e293b] border border-[#334155]">↑↓</kbd>
                  <span>to navigate</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-[11px] text-[#475569]">
                <Zap className="h-3 w-3 text-warning" />
                <span>Powered by AdTicks AI</span>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
