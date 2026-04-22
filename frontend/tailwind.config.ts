import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      colors: {
        bg:       "#09090b",
        background: "#09090b",
        surface: {
          1: "#111113",
          2: "#18181b",
          3: "#1f1f23",
          4: "#27272a",
          DEFAULT: "#18181b",
        },
        border: {
          DEFAULT: "rgba(255,255,255,0.06)",
          hover:   "rgba(255,255,255,0.10)",
          strong:  "rgba(255,255,255,0.14)",
        },
        primary: {
          DEFAULT: "#6366f1",
          dim:     "rgba(99,102,241,0.12)",
          hover:   "#4f46e5",
          glow:    "rgba(99,102,241,0.25)",
        },
        violet:  "#8b5cf6",
        pink:    "#ec4899",
        sky:     "#38bdf8",
        emerald: "#34d399",
        amber:   "#fbbf24",
        success: {
          DEFAULT: "#22c55e",
          dim:     "rgba(34,197,94,0.12)",
        },
        warning: {
          DEFAULT: "#eab308",
          dim:     "rgba(234,179,8,0.12)",
        },
        danger: {
          DEFAULT: "#ef4444",
          dim:     "rgba(239,68,68,0.12)",
        },
        // legacy flat aliases (keep for backward compat with existing pages)
        surface1: "#111113",
        surface2: "#18181b",
        surface3: "#1f1f23",
        zinc: { 950: "#09090b" },
        text: {
          1: "#fafafa",
          2: "#a1a1aa",
          3: "#52525b",
          primary: "#fafafa",
          muted:   "#a1a1aa",
        },
      },
      backgroundImage: {
        "gradient-brand":     "linear-gradient(135deg, #6366f1, #8b5cf6)",
        "gradient-brand-r":   "linear-gradient(135deg, #8b5cf6, #ec4899)",
        "gradient-brand-fade":"linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08))",
        "gradient-radial":    "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":     "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      boxShadow: {
        card:         "0 0 0 1px rgba(255,255,255,0.06), 0 4px 24px rgba(0,0,0,0.4)",
        "card-hover": "0 0 0 1px rgba(255,255,255,0.10), 0 8px 32px rgba(0,0,0,0.5)",
        popup:        "0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.08)",
        glow:         "0 0 20px rgba(99,102,241,0.25)",
        "glow-sm":    "0 0 10px rgba(99,102,241,0.15)",
        "glow-md":    "0 0 30px rgba(99,102,241,0.3)",
        "glow-success":"0 0 16px rgba(34,197,94,0.2)",
        "glow-danger": "0 0 16px rgba(239,68,68,0.2)",
        "glow-violet": "0 0 20px rgba(139,92,246,0.25)",
        "glow-amber":  "0 0 16px rgba(251,191,36,0.2)",
      },
      animation: {
        "fade-in":    "fadeIn 0.2s ease-out",
        "slide-up":   "slideUp 0.25s cubic-bezier(0.4,0,0.2,1)",
        "slide-down": "slideDown 0.2s cubic-bezier(0.4,0,0.2,1)",
        "slide-in":   "slideIn 0.2s ease-out",
        "scale-in":   "scaleIn 0.15s ease-out",
        "shimmer":    "shimmer 1.8s ease-in-out infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "spin-slow":  "spin 4s linear infinite",
        "bounce-dot": "bounceDot 1.2s ease-in-out infinite",
        "orb-float":  "orbFloat 12s ease-in-out infinite",
        "live-ping":  "livePing 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:    { "0%":  { opacity: "0" },                                   "100%": { opacity: "1" } },
        slideUp:   { "0%":  { transform: "translateY(10px)", opacity: "0" },     "100%": { transform: "translateY(0)", opacity: "1" } },
        slideDown: { "0%":  { transform: "translateY(-6px)", opacity: "0" },     "100%": { transform: "translateY(0)", opacity: "1" } },
        slideIn:   { "0%":  { transform: "translateX(-8px)", opacity: "0" },     "100%": { transform: "translateX(0)", opacity: "1" } },
        scaleIn:   { "0%":  { transform: "scale(0.95)", opacity: "0" },          "100%": { transform: "scale(1)", opacity: "1" } },
        shimmer:   { "0%":  { backgroundPosition: "-200% 0" },                   "100%": { backgroundPosition: "200% 0" } },
        bounceDot: { "0%,80%,100%": { transform: "scale(0)" },                   "40%":  { transform: "scale(1)" } },
        orbFloat:  { "0%,100%": { transform: "translateY(0) scale(1)" },         "50%":  { transform: "translateY(-20px) scale(1.05)" } },
        livePing:  { "0%":  { transform: "scale(1)", opacity: "0.8" },           "70%":  { transform: "scale(2.2)", opacity: "0" },     "100%": { transform: "scale(1)", opacity: "0" } },
      },
      borderRadius: {
        xl:   "12px",
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
