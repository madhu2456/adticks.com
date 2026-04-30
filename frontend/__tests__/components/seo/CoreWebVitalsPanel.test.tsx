import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CoreWebVitalsPanel } from "@/components/seo/CoreWebVitalsPanel";

jest.mock("@/hooks/useSEO", () => ({
  useCWV: jest.fn(),
  useRunCWV: jest.fn(),
}));

import { useCWV, useRunCWV } from "@/hooks/useSEO";

const mCWV = useCWV as jest.Mock;
const mRun = useRunCWV as jest.Mock;
const mutate = jest.fn();

beforeEach(() => {
  mutate.mockClear();
  mCWV.mockReturnValue({ isLoading: false, data: [] });
  mRun.mockReturnValue({ isPending: false, mutate });
});

describe("CoreWebVitalsPanel", () => {
  it("renders the URL input and Analyze button", () => {
    render(<CoreWebVitalsPanel projectId="p1"/>);
    expect(screen.getByPlaceholderText(/https:\/\/example.com\/page/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeInTheDocument();
  });

  it("disables Analyze when no URL is entered", () => {
    render(<CoreWebVitalsPanel projectId="p1"/>);
    expect(screen.getByRole("button", { name: /analyze/i })).toBeDisabled();
  });

  it("toggles strategy between mobile and desktop", () => {
    render(<CoreWebVitalsPanel projectId="p1" defaultUrl="https://x.com"/>);
    const desktop = screen.getByRole("button", { name: /desktop/i });
    fireEvent.click(desktop);
    // After clicking, Analyze fires with desktop strategy
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));
    expect(mutate).toHaveBeenCalledWith({
      projectId: "p1", url: "https://x.com", strategy: "desktop",
    });
  });

  it("renders score cards and vitals when latest data exists", () => {
    mCWV.mockReturnValue({
      isLoading: false,
      data: [{
        id: "c1", url: "https://x.com", strategy: "mobile", timestamp: new Date().toISOString(),
        lcp_ms: 2400, inp_ms: 180, cls: 0.05, fcp_ms: 1700, ttfb_ms: 250,
        performance_score: 85, seo_score: 92, accessibility_score: 80, best_practices_score: 95,
        opportunities: [],
      }],
    });
    render(<CoreWebVitalsPanel projectId="p1"/>);
    expect(screen.getByText("Performance")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText("92")).toBeInTheDocument();
    expect(screen.getByText("LCP")).toBeInTheDocument();
    // LCP value formatted
    expect(screen.getByText("2400ms")).toBeInTheDocument();
  });

  it("renders opportunities panel when present", () => {
    mCWV.mockReturnValue({
      isLoading: false,
      data: [{
        id: "c1", url: "https://x.com", strategy: "mobile", timestamp: new Date().toISOString(),
        lcp_ms: 2400, performance_score: 50, opportunities: [
          { id: "img", title: "Optimize images", description: "Compress images", savings_ms: 1500 },
        ],
      }],
    });
    render(<CoreWebVitalsPanel projectId="p1"/>);
    expect(screen.getByText("Top Performance Opportunities")).toBeInTheDocument();
    expect(screen.getByText("Optimize images")).toBeInTheDocument();
    expect(screen.getByText("Save 1.5s")).toBeInTheDocument();
  });
});
