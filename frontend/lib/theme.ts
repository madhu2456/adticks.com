import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function useClientTheme() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, systemTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return {
      theme: "dark",
      setTheme,
      isDark: true,
      isLoading: true,
    };
  }

  const currentTheme = theme === "system" ? systemTheme : theme;
  const isDark = currentTheme === "dark";

  return {
    theme: currentTheme || "dark",
    setTheme,
    isDark,
    isLoading: false,
  };
}

export function toggleTheme(currentTheme: string | undefined, setTheme: (theme: string) => void) {
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  setTheme(newTheme);
}
