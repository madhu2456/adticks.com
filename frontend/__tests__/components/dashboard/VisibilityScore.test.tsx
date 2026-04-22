import React from "react";
import { render, screen } from "@testing-library/react";
import { VisibilityScore } from "@/components/dashboard/VisibilityScore";
import { VisibilityScore as VisibilityScoreType } from "@/lib/types";

jest.mock("recharts", () => ({
  RadialBarChart: ({ children }: any) => <div data-testid="radial-chart">{children}</div>,
  RadialBar: () => <div data-testid="radial-bar" />,
  PolarAngleAxis: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Tooltip: () => null,
  Cell: () => null,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  RadarChart: ({ children }: any) => <div data-testid="radar-chart">{children}</div>,
  PolarGrid: () => null,
  Radar: () => <div data-testid="radar" />,
}));

const mockScore: VisibilityScoreType = {
  overall: 78,
  seo: 82,
  ai: 65,
  gsc: 90,
  ads: 74,
  computed_at: new Date().toISOString(),
};

describe("VisibilityScore", () => {
  it("renders the card title when score is provided", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByText("Visibility Score")).toBeInTheDocument();
  });

  it("renders the overall score value", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByText("Good")).toBeInTheDocument();
  });

  it("renders score label", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByText("Score")).toBeInTheDocument();
  });

  it("renders channel labels", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByText("SEO Hub")).toBeInTheDocument();
    expect(screen.getByText("AI Visibility")).toBeInTheDocument();
    expect(screen.getByText("Search Console")).toBeInTheDocument();
    expect(screen.getByText("Google Ads")).toBeInTheDocument();
  });

  it("renders channel score values", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("65")).toBeInTheDocument();
    expect(screen.getByText("90")).toBeInTheDocument();
    expect(screen.getByText("74")).toBeInTheDocument();
  });

  it("renders the radial chart", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByTestId("radial-chart")).toBeInTheDocument();
  });

  it("renders loading skeleton when loading is true", () => {
    const { container } = render(<VisibilityScore loading />);
    // In loading state, no score content should appear
    expect(screen.queryByText("Visibility Score")).not.toBeInTheDocument();
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders nothing when no score and not loading", () => {
    const { container } = render(<VisibilityScore />);
    expect(container.firstChild).toBeNull();
  });

  it("renders description text", () => {
    render(<VisibilityScore score={mockScore} />);
    expect(screen.getByText(/unified brand presence index/i)).toBeInTheDocument();
  });
});
