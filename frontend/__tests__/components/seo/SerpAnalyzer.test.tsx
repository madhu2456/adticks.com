import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SerpAnalyzer } from "@/components/seo/SerpAnalyzer";

jest.mock("@/hooks/useSEO", () => ({
  useAnalyzeSerp: jest.fn(),
}));

import { useAnalyzeSerp } from "@/hooks/useSEO";

const mAnalyze = useAnalyzeSerp as jest.Mock;

beforeEach(() => {
  mAnalyze.mockReturnValue({ isPending: false, mutate: jest.fn(), data: null });
});

describe("SerpAnalyzer", () => {
  it("renders inputs for keyword, location, device", () => {
    render(<SerpAnalyzer projectId="p1"/>);
    expect(screen.getByPlaceholderText(/keyword/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeInTheDocument();
  });

  it("disables Analyze when no keyword", () => {
    render(<SerpAnalyzer projectId="p1"/>);
    expect(screen.getByRole("button", { name: /analyze/i })).toBeDisabled();
  });

  it("triggers mutation with keyword/location/device", () => {
    const mutate = jest.fn();
    mAnalyze.mockReturnValue({ isPending: false, mutate, data: null });
    render(<SerpAnalyzer projectId="p1"/>);
    fireEvent.change(screen.getByPlaceholderText(/keyword/i), { target: { value: "running shoes" } });
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));
    expect(mutate).toHaveBeenCalledWith({
      projectId: "p1", keyword: "running shoes", location: "us", device: "desktop",
    });
  });

  it("renders SERP feature badges", () => {
    mAnalyze.mockReturnValue({
      isPending: false, mutate: jest.fn(),
      data: {
        keyword_text: "x", location: "us", device: "desktop",
        features_present: ["featured_snippet", "local_pack"],
        results: [],
      },
    });
    render(<SerpAnalyzer projectId="p1"/>);
    expect(screen.getByText("featured_snippet")).toBeInTheDocument();
    expect(screen.getByText("local_pack")).toBeInTheDocument();
  });

  it("renders top organic results", () => {
    mAnalyze.mockReturnValue({
      isPending: false, mutate: jest.fn(),
      data: {
        keyword_text: "x", location: "us", device: "desktop",
        features_present: [],
        results: [
          { position: 1, url: "https://example.com/", title: "Example Page",
            snippet: "An example", domain: "example.com", domain_authority: 70 },
        ],
      },
    });
    render(<SerpAnalyzer projectId="p1"/>);
    expect(screen.getByText("Top 10 Organic Results")).toBeInTheDocument();
    expect(screen.getByText("Example Page")).toBeInTheDocument();
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getByText("DA 70")).toBeInTheDocument();
  });
});
