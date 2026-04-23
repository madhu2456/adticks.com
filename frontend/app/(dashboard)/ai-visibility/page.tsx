"use client";
import React, { useState } from "react";
import { Bot, Scan, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SOVChart } from "@/components/ai/SOVChart";
import { PromptResults } from "@/components/ai/PromptResults";
import { CompetitorComparison } from "@/components/ai/CompetitorComparison";
export default function AIVisibilityPage() {
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleScan = async () => {
    setScanning(true);
    setProgress(0);
    for (let i = 0; i <= 100; i += 10) {
      await new Promise((r) => setTimeout(r, 300));
      setProgress(i);
    }
    setScanning(false);
    setProgress(0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">AI Visibility</h1>
          <p className="text-text-muted text-sm mt-1">Track how often your brand appears in AI-generated responses</p>
        </div>
        <Button onClick={handleScan} loading={scanning} className="gap-2">
          <Scan className="h-4 w-4" />
          {scanning ? `Scanning... ${progress}%` : "Run New Scan"}
        </Button>
      </div>

      {scanning && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Bot className="h-5 w-5 text-primary animate-pulse" />
              <span className="text-sm font-medium text-primary">Scanning AI responses...</span>
              <span className="text-xs text-text-muted ml-auto">{progress}%</span>
            </div>
            <div className="h-2 bg-surface2 rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-xs text-text-muted mt-2">Testing 48 prompts across ChatGPT, Gemini, Claude, and Perplexity</p>
          </CardContent>
        </Card>
      )}

      {/* Hero metric */}
      <Card className="border-primary/20 bg-gradient-to-br from-primary/10 via-accent/5 to-transparent">
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 rounded-full bg-primary/20 border-2 border-primary/40 flex items-center justify-center shrink-0">
              <Bot className="h-8 w-8 text-primary" />
            </div>
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-text-primary">{mockAIScore.score}%</span>
                <span className="text-xl text-text-muted">AI Visibility</span>
              </div>
              <p className="text-text-muted mt-1">
                You appear in <span className="text-primary font-semibold">{mockAIScore.prompts_appeared_in}</span> of{" "}
                <span className="font-semibold text-text-primary">{mockAIScore.total_prompts}</span> AI responses tested
              </p>
              <div className="flex items-center gap-4 mt-3 text-sm">
                <div>
                  <span className="text-text-muted">Avg Position: </span>
                  <span className="font-semibold text-text-primary">#{mockAIScore.avg_position}</span>
                </div>
                <div className="flex items-center gap-1 text-warning">
                  <TrendingUp className="h-4 w-4" />
                  <span>Industry avg: 61%</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SOV + Category */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SOVChart data={mockSOV} />
        <CompetitorComparison data={mockCategoryBreakdown} />
      </div>

      {/* Prompt results */}
      <PromptResults results={mockAIResults} />
    </div>
  );
}

