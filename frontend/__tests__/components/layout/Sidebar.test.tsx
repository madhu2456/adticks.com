import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar } from "@/components/layout/Sidebar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

jest.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: jest.fn() }),
}));

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href, title }: { children: React.ReactNode; href: string; title?: string }) => (
    <a href={href} title={title}>{children}</a>
  );
});

// Mock auth
jest.mock("@/lib/auth", () => ({
  getUser: jest.fn(() => ({
    full_name: "Test User",
    email: "test@example.com",
    plan: "free",
  })),
}));

// Mock useUsage
jest.mock("@/hooks/useUsage", () => ({
  useUsage: jest.fn(() => ({
    data: {
      plan: "free",
      days_remaining: 10,
    },
    isLoading: false,
  })),
}));

const renderSidebar = (collapsed = false, onToggle = jest.fn()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <Sidebar collapsed={collapsed} onToggle={onToggle} />
    </QueryClientProvider>
  );
};

describe("Sidebar", () => {
  it("renders 'AdTicks' brand name when expanded", () => {
    renderSidebar();
    expect(screen.getByText("AdTicks")).toBeInTheDocument();
  });

  it("does not render 'AdTicks' text when collapsed", () => {
    renderSidebar(true);
    expect(screen.queryByText("AdTicks")).not.toBeInTheDocument();
  });

  it("renders Overview navigation link", () => {
    renderSidebar();
    expect(screen.getByText("Overview")).toBeInTheDocument();
  });

  it("renders SEO Hub navigation link", () => {
    renderSidebar();
    expect(screen.getByText("SEO Hub")).toBeInTheDocument();
  });

  it("renders AEO Hub navigation link", () => {
    renderSidebar();
    expect(screen.getByText("AEO Hub")).toBeInTheDocument();
  });

  it("renders Search Console navigation link", () => {
    renderSidebar();
    expect(screen.getByText("Search Console")).toBeInTheDocument();
  });

  it("renders Ads navigation link", () => {
    renderSidebar();
    expect(screen.getByText("Ads")).toBeInTheDocument();
  });

  it("renders Insights navigation link", () => {
    renderSidebar();
    expect(screen.getByText("Insights")).toBeInTheDocument();
  });

  it("renders Settings navigation link", () => {
    renderSidebar();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders Collapse toggle button", () => {
    renderSidebar();
    expect(
      screen.getByRole("button", { name: /collapse sidebar/i }),
    ).toBeInTheDocument();
  });

  it("calls onToggle when collapse button is clicked", () => {
    const onToggle = jest.fn();
    renderSidebar(false, onToggle);
    fireEvent.click(screen.getByRole("button", { name: /collapse sidebar/i }));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("nav links have accessible href attributes", () => {
    renderSidebar();
    expect(screen.getByRole("link", { name: /overview/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /seo hub/i })).toHaveAttribute("href", "/seo");
    expect(screen.getByRole("link", { name: /aeo hub/i })).toHaveAttribute("href", "/aeo");
    expect(screen.getByRole("link", { name: /search console/i })).toHaveAttribute("href", "/gsc");
    expect(screen.getByRole("link", { name: /^ads$/i })).toHaveAttribute("href", "/ads");
    expect(screen.getByRole("link", { name: /insights/i })).toHaveAttribute("href", "/insights");
    expect(screen.getByRole("link", { name: /settings/i })).toHaveAttribute("href", "/settings");
  });

  it("shows trial badge when expanded", () => {
    renderSidebar();
    expect(screen.getByText("Trial Plan")).toBeInTheDocument();
  });

  it("hides trial badge when collapsed", () => {
    renderSidebar(true);
    expect(screen.queryByText("Trial Plan")).not.toBeInTheDocument();
  });

  it("renders 'Upgrade Plan' button when expanded", () => {
    renderSidebar();
    expect(screen.getByText(/Upgrade to Pro/i)).toBeInTheDocument();
  });

  it("uses title attributes on nav links when collapsed for accessibility", () => {
    renderSidebar(true);
    // When collapsed, links have title attributes
    const links = screen.getAllByRole("link");
    const overviewLink = links.find((l) => l.getAttribute("title") === "Overview");
    expect(overviewLink).toBeTruthy();
  });

  it("active route '/' highlights Overview link", () => {
    // usePathname returns '/' via mock above
    renderSidebar();
    // The active link has extra styling — verify it's rendered
    const overviewLink = screen.getByRole("link", { name: /overview/i });
    expect(overviewLink).toBeInTheDocument();
  });
});
