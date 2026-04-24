'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, Check, AlertCircle, Zap } from 'lucide-react'
import { api } from '@/lib/api'

interface ScanModalProps {
  isOpen: boolean
  onClose: () => void
  projectId?: string
}

type ScanStatus = 'starting' | 'scanning' | 'completed' | 'error'

export function ScanModal({ isOpen, onClose, projectId }: ScanModalProps) {
  const [status, setStatus] = useState<ScanStatus>('starting')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isOpen || !projectId) return

    const startScan = async () => {
      try {
        setStatus('starting')
        setError(null)
        setProgress(0)

        const response = await api.ai.runScan(projectId)
        const newTaskId = response.task_id

        setTaskId(newTaskId)
        setStatus('scanning')

        pollTaskStatus(newTaskId)
      } catch (err: any) {
        console.error('Scan failed:', err)
        setStatus('error')
        setError(err.response?.data?.message || 'Failed to start scan. Please try again.')
      }
    }

    startScan()
  }, [isOpen, projectId])

  const pollTaskStatus = async (taskId: string) => {
    const maxAttempts = 300 // 5 minutes instead of 1 minute
    let attempts = 0

    const interval = setInterval(async () => {
      if (attempts >= maxAttempts) {
        clearInterval(interval)
        setStatus('error')
        setError('Scan took too long. This may indicate a backend issue. Please check backend logs or try again later.')
        return
      }

      try {
        const response = await api.ai.getTaskStatus(taskId)
        const taskStatus = response.status.toLowerCase()

        if (taskStatus === 'completed' || taskStatus === 'success') {
          setProgress(100)
          setStatus('completed')
          clearInterval(interval)
        } else if (taskStatus === 'failed' || taskStatus === 'error') {
          setStatus('error')
          setError(response.error || 'Scan failed. Please try again.')
          clearInterval(interval)
        } else if (taskStatus === 'running' || taskStatus === 'pending' || taskStatus === 'started') {
          // Slow progress increase to show activity during long scans
          setProgress(prev => Math.min(95, prev + (Math.random() * 5 + 2)))
        }

        attempts++
      } catch (err: any) {
        // Suppress error logging for polling - it's expected until scan completes
        attempts++
      }
    }, 1000)

    return () => clearInterval(interval)
  }

  const handleClose = () => {
    if (status === 'completed' || status === 'error') {
      onClose()
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md bg-[#1e293b] border border-[#334155] rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#334155]">
              <div className="flex items-center gap-2">
                {status === 'scanning' && (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                )}
                {status === 'completed' && (
                  <Check className="h-5 w-5 text-green-500" />
                )}
                {status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-danger" />
                )}
                {status === 'starting' && (
                  <Zap className="h-5 w-5 text-primary" />
                )}
                <h3 className="text-lg font-bold text-[#f1f5f9]">
                  {status === 'scanning' && 'Running Scan...'}
                  {status === 'completed' && 'Scan Completed'}
                  {status === 'error' && 'Scan Failed'}
                  {status === 'starting' && 'Starting Scan...'}
                </h3>
              </div>
              {status === 'completed' || status === 'error' ? (
                <button
                  onClick={handleClose}
                  className="text-[#94a3b8] hover:text-[#f1f5f9] transition-colors p-1"
                >
                  <X className="h-5 w-5" />
                </button>
              ) : null}
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              {/* Status Messages */}
              {status === 'starting' && (
                <div className="text-center space-y-3">
                  <div className="flex justify-center">
                    <Zap className="h-12 w-12 text-primary animate-pulse" />
                  </div>
                  <p className="text-[#94a3b8] text-sm">Initializing scan...</p>
                </div>
              )}

              {status === 'scanning' && (
                <div className="space-y-3">
                  <div className="flex justify-center">
                    <Loader2 className="h-12 w-12 text-primary animate-spin" />
                  </div>
                  <p className="text-center text-[#f1f5f9] font-medium">Scanning your website</p>
                  <p className="text-center text-[#94a3b8] text-sm">
                    Analyzing content, rankings, and AI visibility...
                  </p>

                  {/* Progress bar */}
                  <div className="mt-6 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-[#94a3b8]">Progress</span>
                      <span className="text-xs text-primary font-semibold">{Math.floor(progress)}%</span>
                    </div>
                    <div className="w-full h-2 bg-[#334155] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.3 }}
                        className="h-full bg-gradient-to-r from-primary to-indigo-400"
                      />
                    </div>
                  </div>

                  <p className="text-center text-[#64748b] text-xs mt-4">
                    This may take a few moments. Please don't close this dialog.
                  </p>
                </div>
              )}

              {status === 'completed' && (
                <div className="text-center space-y-3">
                  <div className="flex justify-center">
                    <div className="relative">
                      <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center">
                        <Check className="h-6 w-6 text-green-500" />
                      </div>
                      <motion.div
                        initial={{ scale: 0, opacity: 1 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{ duration: 0.5 }}
                        className="absolute inset-0 rounded-full border-2 border-green-500"
                      />
                    </div>
                  </div>
                  <p className="text-[#f1f5f9] font-semibold">Scan Completed Successfully!</p>
                  <p className="text-[#94a3b8] text-sm">
                    Your website scan is now complete. Check your dashboard for updated results.
                  </p>
                </div>
              )}

              {status === 'error' && (
                <div className="text-center space-y-3">
                  <div className="flex justify-center">
                    <div className="h-12 w-12 rounded-full bg-danger/20 flex items-center justify-center">
                      <AlertCircle className="h-6 w-6 text-danger" />
                    </div>
                  </div>
                  <p className="text-[#f1f5f9] font-semibold">Scan Failed</p>
                  <p className="text-[#94a3b8] text-sm">{error || 'An error occurred during the scan.'}</p>
                </div>
              )}
            </div>

            {/* Footer */}
            {(status === 'completed' || status === 'error') && (
              <div className="px-6 py-4 border-t border-[#334155]">
                <button
                  onClick={handleClose}
                  className="w-full px-4 py-2 bg-primary hover:bg-primary/90 text-white font-medium rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
