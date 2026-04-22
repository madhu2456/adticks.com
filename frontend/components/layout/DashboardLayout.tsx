"use client";
import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { cn } from "@/lib/utils";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen" style={{ background: '#09090b' }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <Header sidebarCollapsed={collapsed} />

      <main
        className={cn(
          "pt-14 min-h-screen transition-all duration-[220ms] ease-[cubic-bezier(0.4,0,0.2,1)]",
          collapsed ? "pl-[60px]" : "pl-[224px]",
        )}
      >
        {/* Subtle top gradient bleed */}
        <div
          className="pointer-events-none fixed top-14 left-0 right-0 h-32 z-10"
          style={{
            background: 'linear-gradient(to bottom, rgba(9,9,11,0.4), transparent)',
          }}
        />

        <div className="relative z-0 p-6 max-w-[1440px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
