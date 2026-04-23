"use client";
import React from "react";
import Link from "next/link";
import { BarChart2, ArrowRight, Menu, X } from "lucide-react";
import { useState, useEffect } from "react";

export function MarketingLayout({ children }: { children: React.ReactNode }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090b] text-white selection:bg-[#6366f1]/30">
      {/* Navbar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-300 ${
          isScrolled
            ? "bg-[#09090b]/80 backdrop-blur-md border-b border-white/10 py-3"
            : "bg-transparent py-5"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center shadow-lg shadow-[#6366f1]/20 group-hover:scale-105 transition-transform">
              <BarChart2 className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-bold text-xl tracking-tight">AdTicks</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {["Features", "Integrations", "Pricing", "Enterprise"].map((item) => (
              <Link
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-sm font-medium text-white/60 hover:text-white transition-colors"
              >
                {item}
              </Link>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-white/80 hover:text-white transition-colors px-4 py-2"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="bg-white text-black hover:bg-white/90 text-sm font-bold px-5 py-2.5 rounded-full transition-all shadow-xl shadow-white/5 active:scale-95"
            >
              Start Free Trial
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2 text-white/80"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden absolute top-full left-0 right-0 bg-[#0e0e10] border-b border-white/10 p-6 flex flex-col gap-6 animate-in slide-in-from-top-4 duration-200">
            {["Features", "Integrations", "Pricing", "Enterprise"].map((item) => (
              <Link
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-lg font-medium text-white/70"
                onClick={() => setMobileMenuOpen(false)}
              >
                {item}
              </Link>
            ))}
            <hr className="border-white/5" />
            <Link href="/login" className="text-lg font-medium">
              Sign in
            </Link>
            <Link
              href="/register"
              className="bg-[#6366f1] text-white text-center font-bold py-4 rounded-xl"
            >
              Get Started
            </Link>
          </div>
        )}
      </nav>

      <main>{children}</main>

      {/* Footer */}
      <footer className="bg-[#0e0e10] border-t border-white/5 pt-20 pb-10">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2.5 mb-6">
              <div className="w-8 h-8 rounded-lg bg-[#6366f1] flex items-center justify-center">
                <BarChart2 className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-lg">AdTicks</span>
            </div>
            <p className="text-sm text-white/40 leading-relaxed">
              Unified visibility intelligence for modern growth teams. Track SEO, AI, and Ads in one place.
            </p>
          </div>
          <div>
            <h4 className="font-bold text-sm mb-6 uppercase tracking-wider text-white/30">Platform</h4>
            <ul className="space-y-4 text-sm text-white/50">
              <li><Link href="#features">SEO Hub</Link></li>
              <li><Link href="#features">AI Visibility</Link></li>
              <li><Link href="#features">Ads Tracking</Link></li>
              <li><Link href="/register">API Access</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-sm mb-6 uppercase tracking-wider text-white/30">Company</h4>
            <ul className="space-y-4 text-sm text-white/50">
              <li><Link href="#">About</Link></li>
              <li><Link href="#">Customers</Link></li>
              <li><Link href="#">Security</Link></li>
              <li><Link href="#">Contact</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-sm mb-6 uppercase tracking-wider text-white/30">Support</h4>
            <ul className="space-y-4 text-sm text-white/50">
              <li><Link href="/help">Documentation</Link></li>
              <li><Link href="#">Changelog</Link></li>
              <li><Link href="#">Status</Link></li>
              <li><Link href="#">Privacy</Link></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6 border-t border-white/5 pt-10">
          <p className="text-xs text-white/30">© 2026 AdTicks Intelligence Inc. All rights reserved.</p>
          <div className="flex gap-8 text-xs text-white/30">
            <Link href="#">Terms</Link>
            <Link href="#">Privacy</Link>
            <Link href="#">Cookies</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
