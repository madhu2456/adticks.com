import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { PageErrorBoundary } from "@/components/PageErrorBoundary";
import { ThemeProvider } from "next-themes";
import { generateOrganizationSchema } from "@/lib/seo";

export const metadata: Metadata = {
  title: "AdTicks — Visibility Intelligence Platform",
  description: "Monitor your brand's visibility across SEO, AI, Search Console, and Ads in one unified dashboard.",
  keywords: ["SEO", "visibility", "search console", "ads", "analytics", "marketing intelligence"],
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "AdTicks — Visibility Intelligence Platform",
    description: "Monitor your brand's visibility across SEO, AI, Search Console, and Ads in one unified dashboard.",
    type: "website",
    url: "https://adticks.com",
    images: [
      {
        url: "https://adticks.com/og-image.png",
        width: 1200,
        height: 630,
        alt: "AdTicks Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "AdTicks — Visibility Intelligence Platform",
    description: "Monitor your brand's visibility across SEO, AI, Search Console, and Ads.",
    images: ["https://adticks.com/twitter-image.png"],
  },
  robots: "index, follow",
  alternates: {
    canonical: "https://adticks.com",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const organizationSchema = generateOrganizationSchema({
    name: "AdTicks",
    url: "https://adticks.com",
    description: "Visibility Intelligence Platform",
    sameAs: [
      "https://twitter.com/adticks",
      "https://linkedin.com/company/adticks",
    ],
  });

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />
      </head>
      <body className="bg-background text-text-primary antialiased">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <AuthProvider>
            <QueryProvider>
              <PageErrorBoundary>{children}</PageErrorBoundary>
            </QueryProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
