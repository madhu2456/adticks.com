/**
 * AdTicks — SEO Audit Trigger Component
 */

"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface SEOAuditTriggerProps {
  projectId: string;
  domain: string;
}

export function SEOAuditTrigger({ projectId, domain }: SEOAuditTriggerProps) {
  const [urls, setUrls] = useState<string[]>([domain]);
  const [customUrl, setCustomUrl] = useState("");

  // Meta Tags Audit
  const metaTagsMutation = useMutation({
    mutationFn: async (urlsList: string[]) => {
      const params = new URLSearchParams();
      urlsList.forEach((url) => params.append("urls", url));
      const response = await fetch(`/api/seo/audit/meta-tags?project_id=${projectId}&${params}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to trigger meta tags audit");
      return response.json();
    },
    onSuccess: () => {
      toast.success("Meta tags audit queued successfully");
    },
    onError: () => {
      toast.error("Failed to queue meta tags audit");
    },
  });

  // Structured Data Audit
  const structuredDataMutation = useMutation({
    mutationFn: async (urlsList: string[]) => {
      const params = new URLSearchParams();
      urlsList.forEach((url) => params.append("urls", url));
      const response = await fetch(`/api/seo/audit/structured-data?project_id=${projectId}&${params}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to trigger structured data audit");
      return response.json();
    },
    onSuccess: () => {
      toast.success("Structured data audit queued successfully");
    },
    onError: () => {
      toast.error("Failed to queue structured data audit");
    },
  });

  // Crawlability Audit
  const crawlabilityMutation = useMutation({
    mutationFn: async (urlsList: string[]) => {
      const params = new URLSearchParams();
      urlsList.forEach((url) => params.append("urls", url));
      const response = await fetch(`/api/seo/audit/crawlability?project_id=${projectId}&${params}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to trigger crawlability audit");
      return response.json();
    },
    onSuccess: () => {
      toast.success("Crawlability audit queued successfully");
    },
    onError: () => {
      toast.error("Failed to queue crawlability audit");
    },
  });

  // Page Speed Audit
  const pageSpeedMutation = useMutation({
    mutationFn: async (urlsList: string[]) => {
      const params = new URLSearchParams();
      urlsList.forEach((url) => params.append("urls", url));
      const response = await fetch(
        `/api/seo/metrics/page-speed?project_id=${projectId}&device=desktop&${params}`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Failed to trigger page speed audit");
      return response.json();
    },
    onSuccess: () => {
      toast.success("Page speed audit queued successfully");
    },
    onError: () => {
      toast.error("Failed to queue page speed audit");
    },
  });

  // Content Analysis
  const contentAnalysisMutation = useMutation({
    mutationFn: async (urlsList: string[]) => {
      const params = new URLSearchParams();
      urlsList.forEach((url) => params.append("urls", url));
      const response = await fetch(`/api/seo/analyze/content?project_id=${projectId}&${params}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to trigger content analysis");
      return response.json();
    },
    onSuccess: () => {
      toast.success("Content analysis queued successfully");
    },
    onError: () => {
      toast.error("Failed to queue content analysis");
    },
  });

  // Broken Links Detection
  const brokenLinksMutation = useMutation({
    mutationFn: async (urlsList: string[]) => {
      const params = new URLSearchParams();
      urlsList.forEach((url) => params.append("urls", url));
      const response = await fetch(
        `/api/seo/broken-links/detect?project_id=${projectId}&check_external=true&${params}`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Failed to trigger broken links detection");
      return response.json();
    },
    onSuccess: () => {
      toast.success("Broken links detection queued successfully");
    },
    onError: () => {
      toast.error("Failed to queue broken links detection");
    },
  });

  const handleAddUrl = () => {
    if (customUrl && !urls.includes(customUrl)) {
      setUrls([...urls, customUrl]);
      setCustomUrl("");
    }
  };

  const handleRemoveUrl = (url: string) => {
    setUrls(urls.filter((u) => u !== url));
  };

  const isLoading =
    metaTagsMutation.isPending ||
    structuredDataMutation.isPending ||
    crawlabilityMutation.isPending ||
    pageSpeedMutation.isPending ||
    contentAnalysisMutation.isPending ||
    brokenLinksMutation.isPending;

  return (
    <div className="space-y-6">
      {/* URL Selection */}
      <Card>
        <CardHeader>
          <CardTitle>URLs to Audit</CardTitle>
          <CardDescription>Select or enter URLs for SEO analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter URL to audit..."
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleAddUrl()}
            />
            <Button onClick={handleAddUrl} variant="outline">
              Add URL
            </Button>
          </div>

          <div className="space-y-2">
            {urls.map((url) => (
              <div key={url} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm">{url}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveUrl(url)}
                  disabled={urls.length === 1}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Audit Options */}
      <Tabs defaultValue="technical" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="technical">Technical</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="links">Links</TabsTrigger>
        </TabsList>

        {/* Technical SEO */}
        <TabsContent value="technical" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Technical SEO Audits</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Meta Tags */}
                <Card className="border-2">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-blue-600" />
                      Meta Tags Audit
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Title, description, OG tags, Twitter cards
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={() => metaTagsMutation.mutate(urls)}
                      disabled={isLoading}
                      className="w-full"
                    >
                      {metaTagsMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      Audit Meta Tags
                    </Button>
                  </CardContent>
                </Card>

                {/* Structured Data */}
                <Card className="border-2">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-purple-600" />
                      Structured Data
                    </CardTitle>
                    <CardDescription className="text-xs">
                      JSON-LD schemas, breadcrumbs, rich snippets
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={() => structuredDataMutation.mutate(urls)}
                      disabled={isLoading}
                      className="w-full"
                    >
                      {structuredDataMutation.isPending && (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      )}
                      Audit Schemas
                    </Button>
                  </CardContent>
                </Card>

                {/* Crawlability */}
                <Card className="border-2">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-600" />
                      Crawlability
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Redirects, noindex, canonical, links, images
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={() => crawlabilityMutation.mutate(urls)}
                      disabled={isLoading}
                      className="w-full"
                    >
                      {crawlabilityMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      Audit Crawlability
                    </Button>
                  </CardContent>
                </Card>

                {/* Page Speed */}
                <Card className="border-2">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      Page Speed
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Core Web Vitals, Lighthouse scores
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={() => pageSpeedMutation.mutate(urls)}
                      disabled={isLoading}
                      className="w-full"
                    >
                      {pageSpeedMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      Audit Speed
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Content SEO */}
        <TabsContent value="content" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Content SEO Audits</CardTitle>
            </CardHeader>
            <CardContent>
              <Card className="border-2">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                    Content Analysis
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Readability, keyword density, heading structure, word count
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => contentAnalysisMutation.mutate(urls)}
                    disabled={isLoading}
                    className="w-full"
                  >
                    {contentAnalysisMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Analyze Content
                  </Button>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Links */}
        <TabsContent value="links" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Link Audits</CardTitle>
            </CardHeader>
            <CardContent>
              <Card className="border-2">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    Broken Links Detection
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Find broken internal and external links
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => brokenLinksMutation.mutate(urls)}
                    disabled={isLoading}
                    className="w-full"
                  >
                    {brokenLinksMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Detect Broken Links
                  </Button>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Alert>
        <CheckCircle2 className="h-4 w-4" />
        <AlertDescription>
          Audits run in the background. Results will be available shortly. Check back for updates!
        </AlertDescription>
      </Alert>
    </div>
  );
}
