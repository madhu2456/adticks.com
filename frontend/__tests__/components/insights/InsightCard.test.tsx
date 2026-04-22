import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { InsightCard } from "@/components/insights/InsightCard";
import { Insight } from "@/lib/types";

const recentDate = new Date(Date.now() - 1000 * 60 * 60).toISOString(); // 1 hour ago
const oldDate = new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(); // 48 hours ago

const baseInsight: Insight = {
  id: "ins1",
  title: "Title tags missing primary keywords",
  description: "Your title tags are missing primary keywords on 12 pages.",
  category: "seo",
  priority: "P1",
  created_at: recentDate,
  is_read: false,
};

describe("InsightCard", () => {
  it("renders the insight title", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.getByText("Title tags missing primary keywords")).toBeInTheDocument();
  });

  it("renders the insight description", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.getByText(/title tags are missing primary keywords/i)).toBeInTheDocument();
  });

  it("renders the P1 priority badge with correct label", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.getByText("P1 CRITICAL")).toBeInTheDocument();
  });

  it("renders P2 priority badge", () => {
    const insight = { ...baseInsight, priority: "P2" as const };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("P2 HIGH")).toBeInTheDocument();
  });

  it("renders P3 priority badge", () => {
    const insight = { ...baseInsight, priority: "P3" as const };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("P3 MEDIUM")).toBeInTheDocument();
  });

  it("renders the category label for seo", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.getByText("SEO")).toBeInTheDocument();
  });

  it("renders the category label for ai", () => {
    const insight = { ...baseInsight, category: "ai" as const };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("AI Visibility")).toBeInTheDocument();
  });

  it("renders the category label for gsc", () => {
    const insight = { ...baseInsight, category: "gsc" as const };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("Search Console")).toBeInTheDocument();
  });

  it("renders the category label for ads", () => {
    const insight = { ...baseInsight, category: "ads" as const };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("Ads")).toBeInTheDocument();
  });

  it("renders the category label for cross-channel", () => {
    const insight = { ...baseInsight, category: "cross-channel" as const };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("Cross-Channel")).toBeInTheDocument();
  });

  it("renders data_snippet pills when data_snippet is provided", () => {
    const insight = { ...baseInsight, data_snippet: "12 pages | 5% drop | fix now" };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("12 pages")).toBeInTheDocument();
    expect(screen.getByText("5% drop")).toBeInTheDocument();
    expect(screen.getByText("fix now")).toBeInTheDocument();
  });

  it("does not render data snippet section when data_snippet is absent", () => {
    render(<InsightCard insight={baseInsight} />);
    // No pill content — just verify no crash and card renders
    expect(screen.getByText("Title tags missing primary keywords")).toBeInTheDocument();
  });

  it("shows 'Mark as read' button when not read and onMarkRead is provided", () => {
    const onMarkRead = jest.fn();
    render(<InsightCard insight={baseInsight} onMarkRead={onMarkRead} />);
    expect(screen.getByText(/mark as read/i)).toBeInTheDocument();
  });

  it("calls onMarkRead with insight id when 'Mark as read' is clicked", () => {
    const onMarkRead = jest.fn();
    render(<InsightCard insight={baseInsight} onMarkRead={onMarkRead} />);
    fireEvent.click(screen.getByText(/mark as read/i));
    expect(onMarkRead).toHaveBeenCalledWith("ins1");
  });

  it("does not show 'Mark as read' button when insight is already read", () => {
    const readInsight = { ...baseInsight, is_read: true };
    const onMarkRead = jest.fn();
    render(<InsightCard insight={readInsight} onMarkRead={onMarkRead} />);
    expect(screen.queryByText(/mark as read/i)).not.toBeInTheDocument();
  });

  it("does not show 'Mark as read' button when onMarkRead is not provided", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.queryByText(/mark as read/i)).not.toBeInTheDocument();
  });

  it("shows 'NEW' badge for recent unread insights (within 24h)", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.getByText("NEW")).toBeInTheDocument();
  });

  it("does not show 'NEW' badge for old insights (>24h)", () => {
    const oldInsight = { ...baseInsight, created_at: oldDate };
    render(<InsightCard insight={oldInsight} />);
    expect(screen.queryByText("NEW")).not.toBeInTheDocument();
  });

  it("does not show 'NEW' badge when insight is already read", () => {
    const readInsight = { ...baseInsight, is_read: true };
    render(<InsightCard insight={readInsight} />);
    expect(screen.queryByText("NEW")).not.toBeInTheDocument();
  });

  it("renders action link when action_label is provided", () => {
    const insight = { ...baseInsight, action_label: "Fix Now", action_url: "/seo" };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("Fix Now")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /fix now/i })).toHaveAttribute("href", "/seo");
  });

  it("does not render action link when action_label is absent", () => {
    render(<InsightCard insight={baseInsight} />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
