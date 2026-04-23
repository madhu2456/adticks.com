"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { setTokens, setUser } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await api.auth.login({ email, password });
      setTokens(tokens);

      // Fetch user profile immediately
      const user = await api.auth.me();
      setUser(user);

      router.push("/");
      router.refresh();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr?.response?.data?.detail ||
          "Invalid email or password. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-[#1e293b] rounded-2xl p-8 shadow-2xl border border-[#334155]">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[#f1f5f9]">Welcome back</h2>
        <p className="text-sm text-[#94a3b8] mt-1">Sign in to your AdTicks account</p>
      </div>

      {error && (
        <div className="mb-5 flex items-center gap-2.5 rounded-lg bg-[#ef4444]/10 border border-[#ef4444]/30 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-[#ef4444] shrink-0" />
          <p className="text-sm text-[#ef4444]">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">
            Email address
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">
            Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#475569] hover:text-[#94a3b8] transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <div className="mt-1.5 text-right">
            <button 
              type="button"
              onClick={() => alert('Password recovery is coming soon!')}
              className="text-xs text-[#6366f1] hover:text-[#8b5cf6] transition-colors"
            >
              Forgot password?
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#6366f1] hover:bg-[#4f46e5] disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-2.5 text-sm transition-colors shadow-lg shadow-[#6366f1]/25"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-[#94a3b8]">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="text-[#6366f1] hover:text-[#8b5cf6] font-medium transition-colors"
        >
          Start free trial &rarr;
        </Link>
      </p>
    </div>
  );
}
