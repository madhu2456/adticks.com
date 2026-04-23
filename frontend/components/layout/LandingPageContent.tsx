"use client";
import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight, Search, Bot, BarChart2, Zap,
  CheckCircle2, Globe, Shield, Activity, Target
} from "lucide-react";

export function LandingPageContent() {
  return (
    <div className="overflow-x-hidden">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 px-6">
        {/* Glow Effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-[500px] bg-[#6366f1]/20 blur-[120px] rounded-full -z-10 opacity-50" />
        
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#6366f1]/10 border border-[#6366f1]/20 text-[#818cf8] text-xs font-bold uppercase tracking-wider mb-6">
              <Zap className="w-3 h-3" /> Unified Visibility Intelligence
            </span>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
              Own your brand&apos;s <br /> 
              <span className="text-[#6366f1]">Digital Footprint.</span>
            </h1>
            <p className="max-w-2xl mx-auto text-lg md:text-xl text-white/50 mb-10 leading-relaxed">
              The first platform that unifies SEO rank tracking, AI search visibility, and Google Ads performance into a single source of truth.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/register"
                className="w-full sm:w-auto bg-[#6366f1] hover:bg-[#4f46e5] text-white font-bold px-8 py-4 rounded-2xl transition-all shadow-xl shadow-[#6366f1]/20 active:scale-95 flex items-center justify-center gap-2"
              >
                Start 14-Day Free Trial <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="#features"
                className="w-full sm:w-auto bg-white/5 hover:bg-white/10 text-white border border-white/10 font-bold px-8 py-4 rounded-2xl transition-all active:scale-95"
              >
                View Features
              </Link>
            </div>
            
            {/* Social Proof */}
            <div className="mt-16 pt-8 border-t border-white/5 max-w-4xl mx-auto">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/20 mb-8">Trusted by growth teams at</p>
              <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-30 grayscale invert">
                <span className="text-2xl font-bold italic tracking-tighter">Velocity</span>
                <span className="text-2xl font-bold tracking-tight">DATAFLOW</span>
                <span className="text-2xl font-bold">Lumina</span>
                <span className="text-2xl font-bold lowercase tracking-tighter">prism.</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 bg-[#0c0c0e]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Total Visibility Architecture</h2>
            <p className="text-white/40 max-w-xl mx-auto">Stop jumping between tools. AdTicks brings your most critical growth metrics into one unified workspace.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: "SEO Hub",
                desc: "Enterprise-grade keyword tracking, automated content gap analysis, and daily ranking updates.",
                color: "#6366f1"
              },
              {
                icon: Bot,
                title: "AI Visibility",
                desc: "Track how LLMs like ChatGPT, Perplexity, and Claude mention your brand in comparison queries.",
                color: "#8b5cf6"
              },
              {
                icon: BarChart2,
                title: "Ad Intelligence",
                desc: "Monitor Google Ads spend, ROAS, and conversions alongside your organic performance data.",
                color: "#f97316"
              }
            ].map((f, i) => (
              <div key={i} className="group p-8 rounded-3xl bg-[#141416] border border-white/5 hover:border-[#6366f1]/30 transition-all">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110" style={{ backgroundColor: `${f.color}15` }}>
                  <f.icon className="w-6 h-6" style={{ color: f.color }} />
                </div>
                <h3 className="text-xl font-bold mb-3">{f.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Prop Section */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-4xl font-bold mb-8 leading-tight">
              The only platform built for <br />
              <span className="text-[#6366f1]">Search in the AI Era.</span>
            </h2>
            <div className="space-y-6">
              {[
                { title: "Real-time AI Scans", desc: "Understand your share of voice in generative search results." },
                { title: "Google Search Console Sync", desc: "Native integration for accurate clicks and impressions." },
                { title: "Automated Insights", desc: "AI-driven recommendations to improve your visibility scores." },
                { title: "Multi-Project Management", desc: "Track as many brands or domains as your business needs." }
              ].map((item, i) => (
                <div key={i} className="flex gap-4">
                  <div className="mt-1">
                    <CheckCircle2 className="w-5 h-5 text-[#6366f1]" />
                  </div>
                  <div>
                    <h4 className="font-bold text-white/90">{item.title}</h4>
                    <p className="text-sm text-white/40 mt-1">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="relative">
            <div className="aspect-square rounded-3xl bg-gradient-to-br from-[#1e1e22] to-[#0e0e10] border border-white/5 p-8 shadow-2xl overflow-hidden group">
               <div className="absolute inset-0 bg-[#6366f1]/5 opacity-0 group-hover:opacity-100 transition-opacity" />
               <div className="relative h-full flex flex-col justify-center gap-6">
                  {/* Mock UI elements */}
                  <div className="h-12 w-full bg-white/5 rounded-xl border border-white/5 animate-pulse" />
                  <div className="h-40 w-full bg-[#6366f1]/10 rounded-xl border border-[#6366f1]/20 p-4">
                    <div className="h-full w-full bg-[#6366f1]/20 rounded-lg" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="h-24 bg-white/5 rounded-xl border border-white/5" />
                    <div className="h-24 bg-white/5 rounded-xl border border-white/5" />
                  </div>
               </div>
            </div>
            {/* Floating badge */}
            <div className="absolute -bottom-6 -left-6 bg-white text-black p-6 rounded-2xl shadow-2xl max-w-[200px]">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-[#6366f1]" />
                <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">Enterprise Ready</span>
              </div>
              <p className="text-xs font-bold">100% Data Security & SOC2 Compliance.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto rounded-[3rem] bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] p-12 md:p-20 text-center relative overflow-hidden shadow-2xl shadow-[#6366f1]/20">
          <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10 pointer-events-none" />
          <h2 className="text-4xl md:text-5xl font-bold mb-8 relative z-10 text-white">
            Ready to gain <br className="md:hidden" /> total visibility?
          </h2>
          <p className="text-white/80 max-w-xl mx-auto mb-12 text-lg relative z-10">
            Join hundreds of forward-thinking teams using AdTicks to dominate their niche across every search surface.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 relative z-10">
            <Link
              href="/register"
              className="bg-white text-black hover:bg-white/90 font-bold px-10 py-5 rounded-2xl transition-all shadow-xl active:scale-95"
            >
              Get Started Now
            </Link>
            <p className="text-white/60 text-sm">No credit card required.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
