import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BacklinkIntelligence } from "@/components/seo/BacklinkIntelligence";

jest.mock("@/hooks/useSEO", () => ({
  useAnchors: jest.fn(),
  useRefreshAnchors: jest.fn(),
  useToxic: jest.fn(),
  useScanToxic: jest.fn(),
  useDisavowToxic: jest.fn(),
  useLinkIntersect: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  api: { seoAdvanced: { exportDisavow: jest.fn() } },
}));

import {
  useAnchors, useRefreshAnchors, useToxic, useScanToxic,
  useDisavowToxic, useLinkIntersect,
} from "@/hooks/useSEO";

const mAnchors = useAnchors as jest.Mock;
const mRefresh = useRefreshAnchors as jest.Mock;
const mToxic = useToxic as jest.Mock;
const mScan = useScanToxic as jest.Mock;
const mDisavow = useDisavowToxic as jest.Mock;
const mIntersect = useLinkIntersect as jest.Mock;

beforeEach(() => {
  mAnchors.mockReturnValue({ isLoading: false, data: [] });
  mRefresh.mockReturnValue({ isPending: false, mutate: jest.fn() });
  mToxic.mockReturnValue({ isLoading: false, data: [] });
  mScan.mockReturnValue({ isPending: false, mutate: jest.fn() });
  mDisavow.mockReturnValue({ isPending: false, mutate: jest.fn() });
  mIntersect.mockReturnValue({ isPending: false, mutate: jest.fn(), data: null });
});

describe("BacklinkIntelligence", () => {
  it("renders all three tabs", () => {
    render(<BacklinkIntelligence projectId="p1"/>);
    expect(screen.getByRole("tab", { name: /anchor text distribution/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /toxic backlinks/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /link intersect/i })).toBeInTheDocument();
  });

  it("renders empty state for anchors", () => {
    render(<BacklinkIntelligence projectId="p1"/>);
    expect(screen.getByText(/no anchor data yet/i)).toBeInTheDocument();
  });

  it("renders anchor rows when data is present", () => {
    mAnchors.mockReturnValue({
      isLoading: false,
      data: [
        { id: "a1", anchor: "click here", classification: "generic", count: 5, referring_domains: 3 },
        { id: "a2", anchor: "Adticks", classification: "branded", count: 10, referring_domains: 7 },
      ],
    });
    render(<BacklinkIntelligence projectId="p1"/>);
    expect(screen.getByText("click here")).toBeInTheDocument();
    expect(screen.getByText("Adticks")).toBeInTheDocument();
  });

  it("calls refresh when button clicked", () => {
    const mutate = jest.fn();
    mRefresh.mockReturnValue({ isPending: false, mutate });
    render(<BacklinkIntelligence projectId="p1"/>);
    const buttons = screen.getAllByRole("button", { name: /refresh/i });
    fireEvent.click(buttons[0]);
    expect(mutate).toHaveBeenCalledWith({ projectId: "p1" });
  });

  it("switches to toxic tab and renders rows", () => {
    mToxic.mockReturnValue({
      isLoading: false,
      data: [
        { id: "t1", referring_domain: "spam.xyz", spam_score: 78,
          reasons: ["Spammy TLD"], disavowed: false },
      ],
    });
    render(<BacklinkIntelligence projectId="p1"/>);
    fireEvent.click(screen.getByRole("tab", { name: /toxic backlinks/i }));
    expect(screen.getByText("spam.xyz")).toBeInTheDocument();
    expect(screen.getByText(/Spam 78/i)).toBeInTheDocument();
    expect(screen.getByText(/Spammy TLD/i)).toBeInTheDocument();
  });
});
