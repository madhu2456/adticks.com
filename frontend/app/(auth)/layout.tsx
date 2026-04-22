import React from "react";
import { BarChart2 } from "lucide-react";
import { PageErrorBoundary } from "@/components/PageErrorBoundary";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <PageErrorBoundary>
      <div className="min-h-screen bg-[#0f172a] flex flex-col items-center justify-center relative overflow-hidden">
        {/* Background glow effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-[#6366f1]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[300px] bg-[#8b5cf6]/8 rounded-full blur-3xl pointer-events-none" />

        {/* Logo at top */}
        <div className="mb-8 flex flex-col items-center gap-3 z-10">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center shadow-lg shadow-[#6366f1]/30">
            <BarChart2 className="h-6 w-6 text-white" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
              AdTicks
            </h1>
            <p className="text-sm text-[#94a3b8] mt-1">Visibility Intelligence Platform</p>
          </div>
        </div>

        {/* Main content */}
        <div className="w-full max-w-md px-4 z-10">
          {children}
        </div>

        {/* Footer */}
        <p className="mt-8 text-xs text-[#475569] z-10">
          &copy; {new Date().getFullYear()} AdTicks. All rights reserved.
        </p>
      </div>
    </PageErrorBoundary>
  );
}
