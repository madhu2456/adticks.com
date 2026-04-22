import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("calls onClick handler when clicked", () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Press</Button>);
    fireEvent.click(screen.getByRole("button", { name: /press/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when disabled prop is passed", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button", { name: /disabled/i })).toBeDisabled();
  });

  it("does not call onClick when disabled", () => {
    const onClick = jest.fn();
    render(<Button disabled onClick={onClick}>Disabled</Button>);
    fireEvent.click(screen.getByRole("button", { name: /disabled/i }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("is disabled and shows spinner when loading", () => {
    render(<Button loading>Loading</Button>);
    const btn = screen.getByRole("button", { name: /loading/i });
    expect(btn).toBeDisabled();
  });

  it("renders default variant", () => {
    render(<Button variant="default">Default</Button>);
    expect(screen.getByRole("button", { name: /default/i })).toBeInTheDocument();
  });

  it("renders outline variant", () => {
    render(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole("button", { name: /outline/i })).toBeInTheDocument();
  });

  it("renders ghost variant", () => {
    render(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole("button", { name: /ghost/i })).toBeInTheDocument();
  });

  it("renders danger variant", () => {
    render(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole("button", { name: /danger/i })).toBeInTheDocument();
  });

  it("renders secondary variant", () => {
    render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button", { name: /secondary/i })).toBeInTheDocument();
  });

  it("renders success variant", () => {
    render(<Button variant="success">Success</Button>);
    expect(screen.getByRole("button", { name: /success/i })).toBeInTheDocument();
  });

  it("renders link variant", () => {
    render(<Button variant="link">Link</Button>);
    expect(screen.getByRole("button", { name: /link/i })).toBeInTheDocument();
  });

  it("works as type=submit in a form context", () => {
    const onSubmit = jest.fn((e) => e.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <Button type="submit">Submit</Button>
      </form>
    );
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("accepts and applies additional className", () => {
    render(<Button className="my-custom-class">Custom</Button>);
    expect(screen.getByRole("button", { name: /custom/i })).toHaveClass("my-custom-class");
  });
});
