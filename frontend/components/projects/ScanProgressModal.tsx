"use client";

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { useScanProgress } from "@/hooks/useScanProgress";
import { Loader2, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { getAccessToken } from "@/lib/auth";

interface ScanProgressModalProps {
  taskId: string | null;
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

export function ScanProgressModal({
  taskId,
  projectId,
  isOpen,
  onClose,
  onComplete,
}: ScanProgressModalProps) {
  const [authToken, setAuthToken] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setAuthToken(getAccessToken());
    }
  }, []);

  const {
    progress,
    stage,
    message,
    elapsedSeconds,
    estimatedCompletionAt,
    isConnected,
    error,
  } = useScanProgress(taskId, authToken);

  const isCompleted = progress === 100 || stage === "completed";
  const isFailed = error !== null;

  useEffect(() => {
    if (isCompleted && onComplete) {
      const timer = setTimeout(() => {
        onComplete();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isCompleted, onComplete]);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isCompleted && !isFailed ? null : onClose()}>
      <DialogContent className="sm:max-w-[425px] bg-[#0e0e10] border-white/10 text-white">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
            {isCompleted ? (
              <CheckCircle2 className="text-success h-5 w-5" />
            ) : isFailed ? (
              <AlertCircle className="text-danger h-5 w-5" />
            ) : (
              <Loader2 className="text-primary h-5 w-5 animate-spin" />
            )}
            {isCompleted ? "Scan Complete" : isFailed ? "Scan Failed" : "Comprehensive Scan"}
          </DialogTitle>
          <DialogDescription className="text-text-3">
            {isCompleted
              ? "Your project data has been updated successfully."
              : isFailed
              ? "Something went wrong during the scan."
              : "We're analyzing SEO, AI visibility, and performance data."}
          </DialogDescription>
        </DialogHeader>

        <div className="py-6 space-y-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text-2 font-medium capitalize">
                {(stage || "").replace(/_/g, " ") || "Initializing..."}
              </span>
              <span className="text-primary font-bold">{progress}%</span>
            </div>
            <Progress 
              value={progress} 
              className="h-2 bg-white/5" 
              indicatorClassName="bg-[#6366f1]" 
            />
            <p className="text-xs text-text-3 italic">{message || "Waiting for updates..."}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5">
              <p className="text-[10px] text-text-3 uppercase tracking-wider mb-1">Elapsed Time</p>
              <div className="flex items-center gap-1.5 text-text-1 font-medium">
                <Clock size={12} className="text-text-3" />
                <span>{Math.floor(elapsedSeconds / 60)}m {elapsedSeconds % 60}s</span>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5">
              <p className="text-[10px] text-text-3 uppercase tracking-wider mb-1">Estimated Completion</p>
              <div className="flex items-center gap-1.5 text-text-1 font-medium">
                <Clock size={12} className="text-text-3" />
                <span>
                  {estimatedCompletionAt 
                    ? new Date(estimatedCompletionAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    : "--:--"}
                </span>
              </div>
            </div>
          </div>

          {isFailed && (
            <div className="p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-xs">
              <strong>Error:</strong> {error}
            </div>
          )}

          {!isConnected && !isCompleted && !isFailed && (
            <p className="text-[10px] text-text-3 text-center animate-pulse">
              Connecting to real-time stream...
            </p>
          )}
        </div>

        {(isCompleted || isFailed) && (
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-sm transition-colors border border-white/10"
            >
              Close
            </button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
