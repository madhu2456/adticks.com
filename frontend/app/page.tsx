"use client";
import React, { useState, useEffect } from "react";
import { getUser } from "@/lib/auth";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { DashboardContent } from "@/components/dashboard/DashboardContent";
import { MarketingLayout } from "@/components/layout/MarketingLayout";
import { LandingPageContent } from "@/components/layout/LandingPageContent";
import { Loader2 } from "lucide-react";

export default function RootPage() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is authenticated
    const user = getUser();
    setAuthenticated(!!user);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[#6366f1] animate-spin" />
      </div>
    );
  }

  if (authenticated) {
    return (
      <DashboardLayout>
        <DashboardContent />
      </DashboardLayout>
    );
  }

  return (
    <MarketingLayout>
      <LandingPageContent />
    </MarketingLayout>
  );
}
