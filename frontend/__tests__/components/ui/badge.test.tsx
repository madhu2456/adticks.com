import React from "react";
import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>Status</Badge>);
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("renders with default variant", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default")).toBeInTheDocument();
  });

  it("renders secondary variant", () => {
    render(<Badge variant="secondary">Secondary</Badge>);
    expect(screen.getByText("Secondary")).toBeInTheDocument();
  });

  it("renders success variant", () => {
    render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success")).toBeInTheDocument();
  });

  it("renders warning variant", () => {
    render(<Badge variant="warning">Warning</Badge>);
    expect(screen.getByText("Warning")).toBeInTheDocument();
  });

  it("renders danger variant", () => {
    render(<Badge variant="danger">Danger</Badge>);
    expect(screen.getByText("Danger")).toBeInTheDocument();
  });

  it("renders outline variant", () => {
    render(<Badge variant="outline">Outline</Badge>);
    expect(screen.getByText("Outline")).toBeInTheDocument();
  });

  it("renders informational variant", () => {
    render(<Badge variant="informational">Informational</Badge>);
    expect(screen.getByText("Informational")).toBeInTheDocument();
  });

  it("renders transactional variant", () => {
    render(<Badge variant="transactional">Transactional</Badge>);
    expect(screen.getByText("Transactional")).toBeInTheDocument();
  });

  it("renders commercial variant", () => {
    render(<Badge variant="commercial">Commercial</Badge>);
    expect(screen.getByText("Commercial")).toBeInTheDocument();
  });

  it("renders navigational variant", () => {
    render(<Badge variant="navigational">Navigational</Badge>);
    expect(screen.getByText("Navigational")).toBeInTheDocument();
  });

  it("renders p1 variant", () => {
    render(<Badge variant="p1">P1</Badge>);
    expect(screen.getByText("P1")).toBeInTheDocument();
  });

  it("renders p2 variant", () => {
    render(<Badge variant="p2">P2</Badge>);
    expect(screen.getByText("P2")).toBeInTheDocument();
  });

  it("renders p3 variant", () => {
    render(<Badge variant="p3">P3</Badge>);
    expect(screen.getByText("P3")).toBeInTheDocument();
  });

  it("accepts additional className", () => {
    render(<Badge className="extra-class">Label</Badge>);
    expect(screen.getByText("Label")).toHaveClass("extra-class");
  });

  it("renders as a span element", () => {
    const { container } = render(<Badge>Content</Badge>);
    expect(container.firstChild?.nodeName).toBe("SPAN");
  });
});
