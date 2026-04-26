/**
 * AdTicks — SEO Health Dashboard Component
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  Zap,
  Search,
  Gauge,
  Link2,
  Image as ImageIcon,
} from "lucide-react";
import { format } from "date-fns";

interface SEOHealthScoreResponse {
  id: string;
  project_id: string;
  overall_score: number;
  technical_score: number;
  content_score: number;
  performance_score: number;
  security_score: number;
  mobile_score: number;
  total_pages_crawled: number;
  pages_with_issues: number;
  critical_issues: number;
  warnings: number;
  top_opportunities: Array<{ title: string; impact: string; effort: string }>;
  quick_wins: Array<{ title: string; description: string }>;
  last_audit_date: string;
  timestamp: string;
}

interface SEOHealthDashboardProps {
  projectId: string;
}

export function SEOHealthDashboard({ projectId }: SEOHealthDashboardProps) {
  const { data: healthScore, isLoading, error } = useQuery<SEOHealthScoreResponse>({
    queryKey: ["seo-health", projectId],
    queryFn: async () => {
      const response = await fetch(`/api/seo/health-score/${projectId}`);
      if (!response.ok) throw new Error("Failed to fetch SEO health score");
      return response.json();
    },
  });

  if (isLoading) {
    return <div className="animate-pulse">Loading SEO health data...</div>;
  }

  if (error || !healthScore) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Unable to load SEO health score. Run an audit first.</AlertDescription>
      </Alert>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return "bg-green-100";
    if (score >= 60) return "bg-yellow-100";
    return "bg-red-100";
  };

  return (
    <div className="space-y-6">
      {/* Overall Score Card */}
      <Card>
        <CardHeader>
          <CardTitle>SEO Health Score</CardTitle>
          <CardDescription>
            Last updated: {healthScore.last_audit_date ? format(new Date(healthScore.last_audit_date), "PPP") : "Never"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-6">
            {/* Overall */}
            <div className="text-center">
              <div className={`text-4xl font-bold ${getScoreColor(healthScore.overall_score)}`}>
                {healthScore.overall_score}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Overall</p>
            </div>

            {/* Technical */}
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(healthScore.technical_score)}`}>
                {healthScore.technical_score}
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Technical</p>
            </div>

            {/* Content */}
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(healthScore.content_score)}`}>
                {healthScore.content_score}
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Content</p>
            </div>

            {/* Performance */}
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(healthScore.performance_score)}`}>
                {healthScore.performance_score}
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Performance</p>
            </div>

            {/* Mobile */}
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(healthScore.mobile_score)}`}>
                {healthScore.mobile_score}
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Mobile</p>
            </div>

            {/* Security */}
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(healthScore.security_score)}`}>
                {healthScore.security_score}
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Security</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Pages Crawled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{healthScore.total_pages_crawled}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Total</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Pages with Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{healthScore.pages_with_issues}</div>
            <Progress
              value={(healthScore.pages_with_issues / Math.max(1, healthScore.total_pages_crawled)) * 100}
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{healthScore.critical_issues}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Needs attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{healthScore.warnings}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">To review</p>
          </CardContent>
        </Card>
      </div>

      {/* Opportunities & Quick Wins */}
      <Tabs defaultValue="opportunities" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="opportunities">
            <TrendingUp className="w-4 h-4 mr-2" />
            Opportunities ({healthScore.top_opportunities.length})
          </TabsTrigger>
          <TabsTrigger value="quick-wins">
            <Zap className="w-4 h-4 mr-2" />
            Quick Wins ({healthScore.quick_wins.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="opportunities">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Top Opportunities</CardTitle>
              <CardDescription>High-impact improvements sorted by effort</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {healthScore.top_opportunities.length > 0 ? (
                  healthScore.top_opportunities.map((opp, idx) => (
                    <div key={idx} className="flex gap-4 p-3 border rounded-lg">
                      <SearchIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-medium">{opp.title}</h4>
                        <div className="flex gap-2 mt-2 text-xs">
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                            {opp.impact} impact
                          </span>
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                            {opp.effort} effort
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">No opportunities identified</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quick-wins">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Wins</CardTitle>
              <CardDescription>Easy improvements with high impact</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {healthScore.quick_wins.length > 0 ? (
                  healthScore.quick_wins.map((win, idx) => (
                    <div key={idx} className="flex gap-4 p-3 border rounded-lg border-green-200 bg-green-50">
                      <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-medium">{win.title}</h4>
                        <p className="text-sm text-gray-700 mt-1">{win.description}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">No quick wins available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Icon placeholder
function SearchIcon(props: any) {
  return <Search {...props} />;
}
