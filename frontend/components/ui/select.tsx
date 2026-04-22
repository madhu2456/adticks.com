"use client";
import * as React from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  placeholder?: string;
  className?: string;
}

export function Select({ value, onValueChange, children, placeholder, className }: SelectProps) {
  return (
    <div className={cn("relative", className)}>
      <select
        value={value}
        onChange={(e) => onValueChange?.(e.target.value)}
        className="w-full h-9 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary appearance-none focus:outline-none focus:ring-2 focus:ring-primary pr-8"
      >
        {placeholder && <option value="">{placeholder}</option>}
        {children}
      </select>
      <ChevronDown className="absolute right-2.5 top-2.5 h-4 w-4 text-text-muted pointer-events-none" />
    </div>
  );
}

export function SelectItem({ value, children }: { value: string; children: React.ReactNode }) {
  return <option value={value}>{children}</option>;
}

export function SelectTrigger({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

export function SelectContent({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function SelectValue({ placeholder }: { placeholder?: string }) {
  return <span className="text-text-muted">{placeholder}</span>;
}
