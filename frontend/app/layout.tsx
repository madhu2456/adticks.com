import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { PageErrorBoundary } from "@/components/PageErrorBoundary";
import { ThemeProvider } from "next-themes";

export const metadata: Metadata = {
  title: "AdTicks — Visibility Intelligence Platform",
  description: "Monitor your brand's visibility across SEO, AI, Search Console, and Ads in one unified dashboard.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-background text-text-primary antialiased">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <QueryProvider>
            <PageErrorBoundary>{children}</PageErrorBoundary>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
