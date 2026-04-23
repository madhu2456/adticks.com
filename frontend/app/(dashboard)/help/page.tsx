"use client";
import React from "react";
import { HelpCircle, Book, MessageSquare, Terminal, Shield, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const HELP_SECTIONS = [
  {
    title: "Getting Started",
    icon: Zap,
    desc: "Learn how to create your first project and connect your search channels.",
    links: ["Project Setup Guide", "Connecting Google Search Console", "Running your first AI Scan"]
  },
  {
    title: "Intelligence Hubs",
    icon: Book,
    desc: "Deep dives into SEO Hub, AEO Hub, and Local SEO modules.",
    links: ["Understanding Visibility Scores", "Tracking AI Brand Mentions", "Local Ranking Factors"]
  },
  {
    title: "API & Enterprise",
    icon: Terminal,
    desc: "Documentation for technical teams and advanced API configurations.",
    links: ["API Authentication", "Webhook Notifications", "Data Export Options"]
  }
];

export default function HelpPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <HelpCircle className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-4xl font-bold text-text-1 mb-4 tracking-tight">How can we help?</h1>
        <p className="text-text-3 text-lg max-w-2xl mx-auto">
          Search our documentation or reach out to our enterprise support team for assistance with your visibility tracking.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {HELP_SECTIONS.map((section, i) => (
          <Card key={i} className="bg-surface-1 border-white/5 hover:border-primary/30 transition-all">
            <CardHeader>
              <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center mb-4">
                <section.icon className="w-5 h-5 text-text-2" />
              </div>
              <CardTitle className="text-xl">{section.title}</CardTitle>
              <CardDescription>{section.desc}</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {section.links.map((link, j) => (
                  <li key={j}>
                    <button className="text-sm text-primary hover:underline text-left">
                      {link}
                    </button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-gradient-to-br from-primary/10 to-transparent border-primary/20">
        <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4 text-left">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center shrink-0 shadow-lg shadow-primary/20">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold">Still need help?</h3>
              <p className="text-sm text-text-3">Our support team typically responds in under 2 hours.</p>
            </div>
          </div>
          <button className="bg-white text-black px-6 py-3 rounded-xl font-bold text-sm hover:bg-white/90 transition-colors shrink-0">
            Contact Support
          </button>
        </CardContent>
      </Card>
    </div>
  );
}
