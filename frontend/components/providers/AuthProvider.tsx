"use client";

import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getUser, clearTokens } from "@/lib/auth";
import { api } from "@/lib/api";

// 15 minutes of inactivity (configurable)
const IDLE_TIMEOUT = 15 * 60 * 1000; 

interface AuthContextType {
  user: any;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      clearTokens();
      setUserState(null);
      router.push("/login");
    }
  };

  const resetIdleTimer = () => {
    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current);
    }
    
    // Only set timer if user is logged in
    if (getUser()) {
      idleTimerRef.current = setTimeout(() => {
        console.log("User idle for too long. Logging out...");
        logout();
      }, IDLE_TIMEOUT);
    }
  };

  useEffect(() => {
    // Initial user load
    const currentUser = getUser();
    setUserState(currentUser);
    setLoading(false);

    // Activity listeners
    const activityEvents = [
      "mousedown", "mousemove", "keydown", 
      "scroll", "touchstart", "click"
    ];

    const handleActivity = () => resetIdleTimer();

    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity);
    });

    // Initial timer set
    resetIdleTimer();

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, [pathname]); // Reset listeners/timer on route change

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
