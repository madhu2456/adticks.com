import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { RecommendationPanel } from "@/components/insights/RecommendationPanel";
import { Recommendation } from "@/lib/types";

// Mock URL.createObjectURL and related DOM APIs used in export
beforeAll(() => {
  global.URL.createObjectURL = jest.fn(() => "blob:mock-url");
  global.URL.revokeObjectURL = jest.fn();
});

const mockRecommendations: Recommendation[] = [
  {
    id: "rec1",
    title: "Fix missing title tags",
    description: "Add unique title tags to 12 pages missing them.",
    priority: "P1",
    category: "seo",
    effort: "low",
    impact: "high",
  },
  {
    id: "rec2",
    title: "Improve AI brand mentions",
    description: "Optimize content for AI-driven search results.",
    priority: "P2",
    category: "ai",
    effort: "medium",
    impact: "high",
  },
  {
    id: "rec3",
    title: "Review ad spend allocation",
    description: "Reallocate budget to higher performing campaigns.",
    priority: "P3",
    category: "ads",
    effort: "medium",
    impact: "medium",
  },
];

describe("RecommendationPanel", () => {
  it("renders the 'Action Plan' heading", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("Action Plan")).toBeInTheDocument();
  });

  it("renders all recommendation titles", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("Fix missing title tags")).toBeInTheDocument();
    expect(screen.getByText("Improve AI brand mentions")).toBeInTheDocument();
    expect(screen.getByText("Review ad spend allocation")).toBeInTheDocument();
  });

  it("renders recommendation descriptions", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText(/add unique title tags/i)).toBeInTheDocument();
  });

  it("shows initial completion count '0 of N completed'", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("0 of 3 completed")).toBeInTheDocument();
  });

  it("shows '0%' progress initially", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("checking a recommendation increases the completion count", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    // Click the first recommendation button
    fireEvent.click(screen.getByText("Fix missing title tags").closest("button")!);
    expect(screen.getByText("1 of 3 completed")).toBeInTheDocument();
  });

  it("unchecking a recommendation decreases the completion count", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    const firstBtn = screen.getByText("Fix missing title tags").closest("button")!;
    // Check it
    fireEvent.click(firstBtn);
    expect(screen.getByText("1 of 3 completed")).toBeInTheDocument();
    // Uncheck it
    fireEvent.click(firstBtn);
    expect(screen.getByText("0 of 3 completed")).toBeInTheDocument();
  });

  it("hides description when recommendation is checked", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    const firstBtn = screen.getByText("Fix missing title tags").closest("button")!;
    fireEvent.click(firstBtn);
    // Description should be hidden when done
    expect(screen.queryByText(/add unique title tags/i)).not.toBeInTheDocument();
  });

  it("shows correct percentage after completing items", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    fireEvent.click(screen.getByText("Fix missing title tags").closest("button")!);
    expect(screen.getByText("33%")).toBeInTheDocument();
  });

  it("renders priority labels for each recommendation", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("P1")).toBeInTheDocument();
    expect(screen.getByText("P2")).toBeInTheDocument();
    expect(screen.getByText("P3")).toBeInTheDocument();
  });

  it("renders category labels", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("SEO")).toBeInTheDocument();
    expect(screen.getByText("AI")).toBeInTheDocument();
    expect(screen.getByText("Ads")).toBeInTheDocument();
  });

  it("renders numbered list (1., 2., 3.)", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText("1.")).toBeInTheDocument();
    expect(screen.getByText("2.")).toBeInTheDocument();
    expect(screen.getByText("3.")).toBeInTheDocument();
  });

  it("renders the Export Action Plan button", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(screen.getByText(/export action plan/i)).toBeInTheDocument();
  });

  it("clicking export does not throw", () => {
    render(<RecommendationPanel recommendations={mockRecommendations} />);
    expect(() => {
      fireEvent.click(screen.getByText(/export action plan/i));
    }).not.toThrow();
  });
});
