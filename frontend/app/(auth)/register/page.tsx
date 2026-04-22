"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import { setTokens } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const tokens = await api.auth.register({
        email: form.email,
        password: form.password,
        full_name: form.name,
      });
      setTokens(tokens);
      router.push("/");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr?.response?.data?.detail ||
          "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  const passwordStrong = form.password.length >= 8;

  return (
    <div className="bg-[#1e293b] rounded-2xl p-8 shadow-2xl border border-[#334155]">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[#f1f5f9]">Create your account</h2>
        <p className="text-sm text-[#94a3b8] mt-1">Get full visibility across all your channels</p>
      </div>

      {error && (
        <div className="mb-5 flex items-center gap-2.5 rounded-lg bg-[#ef4444]/10 border border-[#ef4444]/30 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-[#ef4444] shrink-0" />
          <p className="text-sm text-[#ef4444]">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">Full name</label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder="Jane Smith"
              className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">Company name</label>
            <input
              type="text"
              value={form.company}
              onChange={(e) => handleChange("company", e.target.value)}
              placeholder="Optivio"
              className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">Email address</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => handleChange("email", e.target.value)}
            placeholder="you@company.com"
            className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">Password</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              required
              value={form.password}
              onChange={(e) => handleChange("password", e.target.value)}
              placeholder="Min. 8 characters"
              className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#475569] hover:text-[#94a3b8]"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {form.password && (
            <div className="mt-1.5 flex items-center gap-1.5">
              <CheckCircle
                className={`h-3.5 w-3.5 ${passwordStrong ? "text-[#10b981]" : "text-[#475569]"}`}
              />
              <span className={`text-xs ${passwordStrong ? "text-[#10b981]" : "text-[#475569]"}`}>
                {passwordStrong ? "Strong password" : "At least 8 characters required"}
              </span>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-[#f1f5f9] mb-1.5">Confirm password</label>
          <input
            type={showPassword ? "text" : "password"}
            required
            value={form.confirmPassword}
            onChange={(e) => handleChange("confirmPassword", e.target.value)}
            placeholder="Repeat your password"
            className="w-full rounded-lg bg-[#0f172a] border border-[#334155] text-[#f1f5f9] placeholder-[#475569] px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 focus:border-[#6366f1] transition-colors"
          />
          {form.confirmPassword && form.password !== form.confirmPassword && (
            <p className="mt-1 text-xs text-[#ef4444]">Passwords do not match</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#6366f1] hover:bg-[#4f46e5] disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-2.5 text-sm transition-colors shadow-lg shadow-[#6366f1]/25 mt-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating account...
            </>
          ) : (
            "Create Free Account"
          )}
        </button>

        <div className="flex items-center justify-center gap-1.5">
          <CheckCircle className="h-3.5 w-3.5 text-[#10b981]" />
          <span className="text-xs text-[#94a3b8]">1 month free trial &bull; No credit card required</span>
        </div>
      </form>

      <p className="mt-5 text-center text-sm text-[#94a3b8]">
        Already have an account?{" "}
        <Link href="/login" className="text-[#6366f1] hover:text-[#8b5cf6] font-medium transition-colors">
          Sign in &rarr;
        </Link>
      </p>
    </div>
  );
}
