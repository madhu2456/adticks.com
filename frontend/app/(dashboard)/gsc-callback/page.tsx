"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Loader2 } from "lucide-react";

export default function GSCCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    const code = searchParams.get("code");
    
    if (completedRef.current) return;

    if (!code) {
      setError("No authorization code found in the URL.");
      return;
    }

    const completeAuth = async () => {
      try {
        completedRef.current = true;
        // Retrieve pkce_state from sessionStorage
        const pkce_state = sessionStorage.getItem("gsc_pkce_state");
        if (pkce_state) {
          sessionStorage.removeItem("gsc_pkce_state"); // Clear it after use
        }
        await api.gsc.completeAuth(code, pkce_state || undefined);
        router.push("/gsc?success=true");
      } catch (err: any) {
        console.error("GSC Auth completion failed:", err);
        setError(err.response?.data?.message || err.message || "Failed to connect Google Search Console.");
      }
    };

    completeAuth();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-4">Connection Error</h1>
        <p className="text-slate-600 mb-6 max-w-md">{error}</p>
        <button 
          onClick={() => router.push("/gsc")}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Back to GSC
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 text-center">
      <Loader2 className="h-12 w-12 text-blue-600 animate-spin mb-4" />
      <h1 className="text-2xl font-bold text-slate-800 mb-2">Connecting to Google...</h1>
      <p className="text-slate-600">Please wait while we finalize the connection with Search Console.</p>
    </div>
  );
}
