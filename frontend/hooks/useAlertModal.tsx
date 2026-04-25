"use client"

import React, { useState, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { AlertCircle, CheckCircle, Info, AlertTriangle, Loader2 } from "lucide-react"

export type AlertType = "info" | "success" | "warning" | "error" | "loading"

export interface AlertModalConfig {
  title: string
  message: string
  type?: AlertType
  onConfirm?: () => void | Promise<void>
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  onCancel?: () => void
}

const iconMap: Record<AlertType, React.ReactNode> = {
  info: <Info className="h-5 w-5 text-blue-500" />,
  success: <CheckCircle className="h-5 w-5 text-green-500" />,
  warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
  error: <AlertCircle className="h-5 w-5 text-red-500" />,
  loading: <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />,
}

export function useAlertModal() {
  const [open, setOpen] = useState(false)
  const [config, setConfig] = useState<AlertModalConfig>({
    title: "",
    message: "",
    type: "info",
  })
  const [isLoading, setIsLoading] = useState(false)

  const showAlert = useCallback((alertConfig: AlertModalConfig) => {
    setConfig({
      type: "info",
      confirmText: alertConfig.type === "error" ? "Close" : "OK",
      cancelText: "Cancel",
      showCancel: false,
      ...alertConfig,
    })
    setOpen(true)
  }, [])

  const handleConfirm = useCallback(async () => {
    if (config.onConfirm) {
      setIsLoading(true)
      try {
        await Promise.resolve(config.onConfirm())
      } finally {
        setIsLoading(false)
      }
    }
    setOpen(false)
  }, [config])

  const handleCancel = useCallback(() => {
    config.onCancel?.()
    setOpen(false)
  }, [config])

  return {
    showAlert,
    AlertModal: (
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <div className="flex items-center gap-3">
              {iconMap[config.type || "info"]}
              <DialogTitle>{config.title}</DialogTitle>
            </div>
          </DialogHeader>
          <DialogDescription className="text-base text-foreground py-4">
            {config.message}
          </DialogDescription>
          <DialogFooter>
            {config.showCancel && (
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={isLoading}
              >
                {config.cancelText || "Cancel"}
              </Button>
            )}
            <Button
              onClick={handleConfirm}
              disabled={isLoading}
              variant={config.type === "error" ? "danger" : "default"}
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {config.confirmText || "OK"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    ),
  }
}

/**
 * Standalone AlertModal component for use in context-based apps
 * Usage: <AlertModal {...config} />
 */
export function AlertModal({
  isOpen,
  onClose,
  title,
  message,
  type = "info",
  onConfirm,
  confirmText,
  cancelText,
  showCancel = false,
}: AlertModalConfig & {
  isOpen: boolean
  onClose: () => void
}) {
  const [isLoading, setIsLoading] = React.useState(false)

  const handleConfirm = async () => {
    if (onConfirm) {
      setIsLoading(true)
      try {
        await Promise.resolve(onConfirm())
      } finally {
        setIsLoading(false)
      }
    }
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-3">
            {iconMap[type]}
            <DialogTitle>{title}</DialogTitle>
          </div>
        </DialogHeader>
        <DialogDescription className="text-base text-foreground py-4">
          {message}
        </DialogDescription>
        <DialogFooter>
          {showCancel && (
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              {cancelText || "Cancel"}
            </Button>
          )}
          <Button
            onClick={handleConfirm}
            disabled={isLoading}
            variant={type === "error" ? "danger" : "default"}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {confirmText || "OK"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
