'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, Check, AlertCircle, Zap, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import { useScanProgress } from '@/hooks/useScanProgress'
import { useBackgroundScans, type BackgroundScan } from '@/hooks/useBackgroundScans'
import { useToast } from '@/components/ui/use-toast'

interface ScanModalProps {
  isOpen: boolean
  onClose: () => void
  projectId?: string
  featureType?: 'seo' | 'ai' | 'geo' | 'gsc' | 'ads' | 'keywords_gsc' | 'on_page' | 'technical' | 'gaps'
  url?: string
}

type ScanStatus = 'starting' | 'scanning' | 'cached' | 'completed' | 'error' | 'background'

export function ScanModal({ isOpen, onClose, projectId, featureType = 'ai', url = '' }: ScanModalProps) {
  const [status, setStatus] = useState<ScanStatus>('starting')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fromCache, setFromCache] = useState(false)
  const [pollProgress, setPollProgress] = useState(0)
  const { addScan, updateScan, scans } = useBackgroundScans()
  const { toast } = useToast()
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  
  // Get auth token (adjust based on your auth system)
  const authToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  
  // Use WebSocket + HTTP polling for real-time progress
  const {
    progress: wsProgress,
    stage,
    message,
    elapsedSeconds,
    estimatedCompletionAt,
    isConnected: wsConnected,
  } = useScanProgress(taskId, authToken)

  // Sync WebSocket progress with the background scan store
  useEffect(() => {
    if (taskId && wsProgress > 0) {
      // Find the active scan that matches this task
      const activeScan = scans.find(s => s.id.startsWith(projectId || '') && s.status === 'scanning');
      if (activeScan) {
        updateScan(activeScan.id, {
          progress: wsProgress,
          stage: stage || 'Scanning...',
          message: message || '',
        });
      }
    }
  }, [wsProgress, stage, message, taskId, projectId, updateScan, scans]);

  const featureLabels = {
    seo: 'SEO Scan',
    ai: 'AI Visibility Scan',
    geo: 'Location Sync',
    gsc: 'GSC Sync',
    ads: 'Ads Sync',
    keywords_gsc: 'GSC Keyword Import',
    on_page: 'On-Page Audit',
    technical: 'Technical SEO Audit',
    gaps: 'Content Gap Analysis',
  }

  useEffect(() => {
    if (!isOpen || !projectId) return

    const startScan = async () => {
      try {
        setStatus('starting')
        setError(null)
        setPollProgress(0)

        // Start the appropriate scan based on featureType
        let response;
        switch (featureType) {
          case 'seo':
            response = await api.seo.runAudit(projectId, '');
            break;
          case 'on_page':
            response = await api.seo.runOnPageAudit(projectId, url);
            break;
          case 'keywords_gsc':
            response = await api.seo.runGscKeywordSync(projectId);
            break;
          case 'technical':
            response = await api.seo.runTechnicalAudit(projectId);
            break;
          case 'gaps':
            response = await api.seo.runGapSync(projectId);
            break;
          case 'gsc':
            response = await api.gsc.sync(projectId);
            break;
          case 'ads':
            response = await api.ads.sync(projectId);
            break;
          case 'ai':
          default:
            response = await api.ai.runScan(projectId);
            break;
        }
        
        const newTaskId = response.task_id
        const cached = (response as any).from_cache || false

        if (newTaskId) {
          const scanId = `${projectId}-${featureType}-${Date.now()}`
          const newScan: BackgroundScan = {
            id: scanId,
            projectId,
            featureType,
            status: 'scanning',
            startedAt: Date.now(),
            progress: 0,
            stage: 'Initializing...',
            message: '',
          }

          setTaskId(newTaskId)
          setFromCache(cached)
          addScan(newScan)
          
          // If results are from cache, show them immediately
          if (cached) {
            setStatus('cached')
            setPollProgress(100)
            updateScan(scanId, {
              status: 'completed',
              progress: 100,
            })
            // Auto-close after 3 seconds
            setTimeout(() => {
              setStatus('background')
            }, 3000)
          } else {
            setStatus('scanning')
            pollTaskStatus(newTaskId, scanId)
          }
        } else {
          throw new Error('No task ID received from server')
        }
      } catch (err: any) {
        console.error('[ScanModal] Scan trigger failed:', err)
        setStatus('error')
        const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to start scan. Please try again.';
        setError(errorMsg)
      }
    }

    startScan()

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [isOpen, projectId, featureType, addScan, updateScan, toast])

  const pollTaskStatus = async (taskId: string, scanId: string) => {
    // Allow 60 minutes of polling, but user can close modal before then
    const maxAttempts = 3600 // 60 minutes (3600 seconds / 1 second interval)
    let attempts = 0
    let currentPollProgress = 0 // Track progress locally in the closure

    const interval = setInterval(async () => {
      if (attempts >= maxAttempts) {
        clearInterval(interval)
        setStatus('error')
        setError('Scan took too long. This may indicate a backend issue. Please check backend logs or try again later.')
        updateScan(scanId, {
          status: 'error',
          error: 'Scan took too long',
        })
        toast({
          title: 'Scan Timeout',
          description: 'The scan took too long to complete.',
          variant: 'destructive',
        })
        return
      }

      try {
        const response = await api.ai.getTaskStatus(taskId)
        const taskStatus = response.status.toLowerCase()
        
        // Use backend progress if available, otherwise use creeping progress
        const backendProgress = (response as any).progress;
        
        if (backendProgress && backendProgress.progress > 0) {
           currentPollProgress = backendProgress.progress
           setPollProgress(currentPollProgress)
           updateScan(scanId, {
             progress: backendProgress.progress,
             stage: backendProgress.stage || 'Scanning...',
             message: backendProgress.message || '',
           })
        }

        if (taskStatus === 'completed' || taskStatus === 'success') {
          setPollProgress(100)
          setStatus('completed')
          updateScan(scanId, {
            status: 'completed',
            progress: 100,
            stage: 'Scan Complete',
          })
          toast({
            title: 'Scan Complete',
            description: `Your ${featureType} scan has completed successfully.`,
            variant: 'default',
          })
          clearInterval(interval)
        } else if (taskStatus === 'failed' || taskStatus === 'error' || taskStatus === 'failure') {
          setStatus('error')
          setError(response.error || 'Scan failed. Please try again.')
          updateScan(scanId, {
            status: 'error',
            error: response.error,
            stage: 'Scan Failed',
          })
          toast({
            title: 'Scan Failed',
            description: response.error || 'An error occurred during the scan.',
            variant: 'destructive',
          })
          clearInterval(interval)
        } else if (!backendProgress || backendProgress.progress === 0) {
          // Creeping progress logic ONLY if backend hasn't provided real progress yet
          let next;
          if (currentPollProgress < 70) next = currentPollProgress + (Math.random() * 5 + 2);
          else if (currentPollProgress < 90) next = currentPollProgress + (Math.random() * 1 + 0.5);
          else if (currentPollProgress < 99) next = currentPollProgress + (Math.random() * 0.2 + 0.1);
          else next = 99;
          
          currentPollProgress = next;
          setPollProgress(currentPollProgress);
          
          // Ensure we update the background scan store with the SAME value
          // Also update the stage to indicate analysis has begun
          updateScan(scanId, {
            progress: Math.floor(next),
            stage: 'Analyzing data across multiple sources...'
          })
        }

        attempts++
      } catch (err: any) {
        // Suppress error logging for polling - it's expected until scan completes
        attempts++
      }
    }, 1000)

    pollIntervalRef.current = interval
    return () => clearInterval(interval)
  }

  const handleClose = () => {
    onClose()
  }

  const handleMinimize = () => {
    // User can click "Run in background" to close and let scan continue
    setStatus('background')
    onClose()
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
                {status === 'cached' && (
                  <Check className="h-5 w-5 text-green-500" />
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
                {status === 'background' && (
                  <ArrowRight className="h-5 w-5 text-blue-400" />
                )}
                <h3 className="text-lg font-bold text-[#f1f5f9]">
                  {status === 'scanning' && `Running ${featureLabels[featureType]}...`}
                  {status === 'cached' && `${featureLabels[featureType]} Results (Cached)`}
                  {status === 'completed' && `${featureLabels[featureType]} Completed`}
                  {status === 'error' && `${featureLabels[featureType]} Failed`}
                  {status === 'starting' && `Starting ${featureLabels[featureType]}...`}
                  {status === 'background' && `${featureLabels[featureType]} Running in Background`}
                </h3>
              </div>
              {(status === 'completed' || status === 'error' || status === 'cached' || status === 'background') ? (
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
                  <p className="text-center text-[#f1f5f9] font-medium">Running {featureLabels[featureType]}</p>
                  
                  {/* Show real-time stage if WebSocket connected */}
                  {wsConnected && stage && (
                    <p className="text-center text-primary text-sm font-medium">{stage}</p>
                  )}
                  
                  {/* Show message if available */}
                  {message && (
                    <p className="text-center text-[#94a3b8] text-sm">
                      {message}
                    </p>
                  )}
                  
                  {!message && (
                    <p className="text-center text-[#94a3b8] text-sm">
                      Analyzing data across multiple sources...
                    </p>
                  )}

                  {/* Progress bar */}
                  <div className="mt-6 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-[#94a3b8]">Progress</span>
                      <span className="text-xs text-primary font-semibold">{Math.floor(wsProgress || pollProgress)}%</span>
                    </div>
                    <div className="w-full h-2 bg-[#334155] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${wsProgress || pollProgress}%` }}
                        transition={{ duration: 0.3 }}
                        className="h-full bg-gradient-to-r from-primary to-indigo-400"
                      />
                    </div>
                  </div>

                  {/* Show ETA if available */}
                  {estimatedCompletionAt && (
                    <p className="text-center text-[#64748b] text-xs mt-2">
                      Estimated completion: {new Date(estimatedCompletionAt).toLocaleTimeString()}
                    </p>
                  )}

                  <p className="text-center text-[#64748b] text-xs mt-4">
                    This may take several minutes. You can close this dialog to continue working.
                  </p>
                </div>
              )}

              {status === 'cached' && (
                <div className="text-center space-y-3">
                  <div className="flex justify-center">
                    <div className="relative">
                      <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <Check className="h-6 w-6 text-blue-500" />
                      </div>
                      <motion.div
                        initial={{ scale: 0, opacity: 1 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{ duration: 0.5 }}
                        className="absolute inset-0 rounded-full border-2 border-blue-500"
                      />
                    </div>
                  </div>
                  <p className="text-[#f1f5f9] font-semibold">Results from Cache</p>
                  <p className="text-[#94a3b8] text-sm">
                    Using recent scan results (nothing changed in your project).
                  </p>
                </div>
              )}

              {status === 'background' && (
                <div className="text-center space-y-3">
                  <div className="flex justify-center">
                    <ArrowRight className="h-12 w-12 text-blue-400" />
                  </div>
                  <p className="text-[#f1f5f9] font-semibold">Scan Running in Background</p>
                  <p className="text-[#94a3b8] text-sm">
                    Your scan is now running in the background. You'll receive an email when it completes.
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
                    Your scan is complete. Check the results below for updated data.
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
            {status === 'scanning' && (
              <div className="px-6 py-4 border-t border-[#334155]">
                <button
                  onClick={handleMinimize}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <ArrowRight className="h-4 w-4" />
                  Run in Background
                </button>
              </div>
            )}
            {(status === 'completed' || status === 'error' || status === 'cached' || status === 'background') && (
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
