import { useState, useCallback } from "react";

/**
 * Minimal useToast implementation to satisfy build requirements.
 * In a full Shadcn UI setup, this would be more complex.
 */

interface ToastProps {
  title?: string;
  description?: string;
  variant?: "default" | "destructive" | "success";
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const toast = useCallback(({ title, description, variant }: ToastProps) => {
    console.log(`Toast: ${title} - ${description} (${variant})`);
    // Logic to show toast would go here
  }, []);

  return {
    toast,
    toasts,
  };
}
