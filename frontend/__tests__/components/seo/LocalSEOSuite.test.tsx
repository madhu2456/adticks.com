import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { LocalSEOSuite } from "@/components/seo/LocalSEOSuite";

jest.mock("@/hooks/useSEO", () => ({
  useCitations: jest.fn(),
  useConsistency: jest.fn(),
  useLocalGrid: jest.fn(),
  useRunLocalGrid: jest.fn(),
}));

import {
  useCitations, useConsistency, useLocalGrid, useRunLocalGrid,
} from "@/hooks/useSEO";

const mCitations = useCitations as jest.Mock;
const mConsistency = useConsistency as jest.Mock;
const mGrid = useLocalGrid as jest.Mock;
const mRunGrid = useRunLocalGrid as jest.Mock;

beforeEach(() => {
  mCitations.mockReturnValue({ isLoading: false, data: [] });
  mConsistency.mockReturnValue({ isLoading: false, data: null });
  mGrid.mockReturnValue({ data: [] });
  mRunGrid.mockReturnValue({ isPending: false, mutate: jest.fn() });
});

describe("LocalSEOSuite", () => {
  it("renders both tabs", () => {
    render(<LocalSEOSuite projectId="p1"/>);
    expect(screen.getByRole("tab", { name: /nap consistency/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /local rank grid/i })).toBeInTheDocument();
  });

  it("shows empty state when no citations exist", () => {
    render(<LocalSEOSuite projectId="p1"/>);
    expect(screen.getByText(/no citations tracked yet/i)).toBeInTheDocument();
  });

  it("renders consistency stats", () => {
    mConsistency.mockReturnValue({
      isLoading: false,
      data: { score: 85, directories_listed: 7, directories_total: 20,
              issues_count: 2, directories_missing: ["Yelp", "TripAdvisor"] },
    });
    render(<LocalSEOSuite projectId="p1"/>);
    expect(screen.getByText("Consistency Score")).toBeInTheDocument();
    expect(screen.getByText("85/100")).toBeInTheDocument();
    expect(screen.getByText("7/20")).toBeInTheDocument();
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1);
    // Missing directories list
    expect(screen.getByText("Yelp")).toBeInTheDocument();
  });

  it("renders citation rows", () => {
    mCitations.mockReturnValue({
      isLoading: false,
      data: [{
        id: "c1", directory: "Yelp", consistency_score: 70, issues: ["Phone differs"],
        business_name: "Acme", address: "123 Main St", phone: "555-1234",
      }],
    });
    render(<LocalSEOSuite projectId="p1"/>);
    expect(screen.getByText("Yelp")).toBeInTheDocument();
    expect(screen.getByText(/Acme/)).toBeInTheDocument();
    expect(screen.getByText("70/100")).toBeInTheDocument();
    expect(screen.getByText(/Phone differs/)).toBeInTheDocument();
  });

  it("runs local grid with provided params", () => {
    const mutate = jest.fn();
    mRunGrid.mockReturnValue({ isPending: false, mutate });
    render(<LocalSEOSuite projectId="p1"/>);
    fireEvent.click(screen.getByRole("tab", { name: /local rank grid/i }));
    fireEvent.change(screen.getByPlaceholderText("Keyword"), { target: { value: "plumber" } });
    fireEvent.click(screen.getByRole("button", { name: /run grid/i }));
    expect(mutate).toHaveBeenCalled();
    const args = mutate.mock.calls[0][0];
    expect(args.projectId).toBe("p1");
    expect(args.params.keyword).toBe("plumber");
  });

  it("renders heatmap cells when grid data is present", () => {
    mGrid.mockReturnValue({
      data: Array.from({ length: 9 }, (_, i) => ({
        id: `g${i}`, keyword: "x", grid_lat: 0, grid_lng: 0,
        rank: i < 3 ? 1 : i < 6 ? 5 : null, radius_km: 5,
      })),
    });
    render(<LocalSEOSuite projectId="p1"/>);
    fireEvent.click(screen.getByRole("tab", { name: /local rank grid/i }));
    expect(screen.getByText("Heatmap")).toBeInTheDocument();
  });
});
