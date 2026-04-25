'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Loader2,
  Check,
  AlertCircle,
  ChevronRight,
  Clock,
  Trash2,
} from 'lucide-react'
import { useBackgroundScans } from '@/hooks/useBackgroundScans'
import { useAlertModal } from '@/hooks/useAlertModal'

const featureLabels: Record<string, string> = {
  seo: 'SEO Scan',
  ai: 'AI Visibility Scan',
  geo: 'Location Sync',
  gsc: 'GSC Sync',
  ads: 'Ads Sync',
  full: 'Full Scan',
  keywords_gsc: 'GSC Keyword Sync',
  on_page: 'On-Page Audit',
  technical: 'Technical Audit',
  gaps: 'Content Gap Discovery',
}

export function BackgroundTasksDrawer() {
  const { scans, removeScan, clearOldScans, clearScans } = useBackgroundScans()
  const { showAlert, AlertModal } = useAlertModal()
  const [isOpen, setIsOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    clearOldScans()
  }, [clearOldScans])

  if (!mounted) return null

  const runningScans = scans.filter((s) => s.status === 'scanning')
  const completedScans = scans.filter((s) => s.status !== 'scanning')

  const formatTime = (timestamp: number) => {
    const now = Date.now()
    const diff = now - timestamp
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)

    if (minutes < 1) return 'just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return new Date(timestamp).toLocaleDateString()
  }

  const handleClearAll = () => {
    if (scans.length === 0) return

    const runningCount = scans.filter((s) => s.status === 'scanning').length
    
    showAlert({
      title: 'Clear All Tasks?',
      message: runningCount > 0 
        ? `You have ${runningCount} tasks currently running. Clearing all will remove them from the tracking list. Continue?`
        : 'This will remove all completed and failed tasks from the list.',
      type: 'warning',
      confirmText: 'Clear All',
      onConfirm: () => {
        clearScans()
      },
    })
  }

  return (
    <>
      {/* Badge Button */}
      {scans.length > 0 && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="fixed bottom-6 right-6 z-40 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
        >
          {runningScans.length > 0 ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>{runningScans.length} Running</span>
            </>
          ) : (
            <>
              <Check className="h-4 w-4" />
              <span>{scans.length} Tasks</span>
            </>
          )}
          <ChevronRight className="h-4 w-4" />
        </button>
      )}

      {/* Drawer */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 z-40 bg-black/30"
            />

            {/* Drawer Panel */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-[#1e293b] border-l border-[#334155] shadow-2xl overflow-y-auto"
            >
              {/* Header */}
              <div className="sticky top-0 px-6 py-4 border-b border-[#334155] bg-[#1e293b]/95 backdrop-blur-sm flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-bold text-[#f1f5f9]">Background Tasks</h2>
                  {scans.length > 0 && (
                    <button
                      onClick={handleClearAll}
                      className="text-xs text-[#94a3b8] hover:text-danger flex items-center gap-1 transition-colors px-2 py-1 rounded-md hover:bg-danger/10 border border-transparent hover:border-danger/20"
                    >
                      <Trash2 size={12} />
                      Clear All
                    </button>
                  )}
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-[#94a3b8] hover:text-[#f1f5f9] transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-4">
                {scans.length === 0 ? (
                  <div className="text-center py-8">
                    <Check className="h-12 w-12 text-green-500/50 mx-auto mb-3" />
                    <p className="text-[#94a3b8]">No background tasks</p>
                  </div>
                ) : (
                  <>
                    {/* Running Scans */}
                    {runningScans.length > 0 && (
                      <div className="space-y-3">
                        <h3 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wide">
                          Running ({runningScans.length})
                        </h3>
                        <div className="space-y-3">
                          {runningScans.map((scan) => (
                            <div
                              key={scan.id}
                              className="p-4 bg-[#0f172a]/50 border border-[#334155] rounded-lg space-y-2"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-start gap-3 flex-1 min-w-0">
                                  <div className="mt-1">
                                    <Loader2 className="h-4 w-4 text-primary animate-spin flex-shrink-0" />
                                  </div>
                                  <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium text-[#f1f5f9] truncate">
                                      {featureLabels[scan.featureType] || scan.featureType}
                                    </p>
                                    <p className="text-xs text-[#64748b] flex items-center gap-1 mt-1">
                                      <Clock className="h-3 w-3" />
                                      {formatTime(scan.startedAt)}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex flex-col items-end gap-2">
                                  <span className="text-xs font-semibold text-primary flex-shrink-0">
                                    {Math.floor(scan.progress)}%
                                  </span>
                                  <button
                                    onClick={() => removeScan(scan.id)}
                                    className="text-[10px] text-[#94a3b8] hover:text-danger hover:bg-danger/10 px-1.5 py-0.5 rounded transition-all flex items-center gap-1 border border-[#334155] hover:border-danger/30"
                                    title="Stop tracking this scan"
                                  >
                                    <X size={10} />
                                    Stop
                                  </button>
                                </div>
                              </div>

                              {/* Progress bar */}
                              <div className="w-full h-1.5 bg-[#334155] rounded-full overflow-hidden">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${scan.progress}%` }}
                                  transition={{ duration: 0.3 }}
                                  className="h-full bg-gradient-to-r from-primary to-indigo-400"
                                />
                              </div>

                              {scan.stage && (
                                <p className="text-xs text-[#94a3b8] truncate">{scan.stage}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Completed Scans */}
                    {completedScans.length > 0 && (
                      <div className="space-y-3 border-t border-[#334155] pt-4">
                        <h3 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wide">
                          Completed ({completedScans.length})
                        </h3>
                        <div className="space-y-2">
                          {completedScans.map((scan) => (
                            <div
                              key={scan.id}
                              className="p-3 bg-[#0f172a]/50 border border-[#334155] rounded-lg flex items-start justify-between gap-3 group hover:border-[#475569] transition-colors"
                            >
                              <div className="flex items-start gap-3 flex-1 min-w-0">
                                <div className="mt-0.5">
                                  {scan.status === 'completed' ? (
                                    <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                                  ) : (
                                    <AlertCircle className="h-4 w-4 text-danger flex-shrink-0" />
                                  )}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-medium text-[#f1f5f9] truncate">
                                    {featureLabels[scan.featureType] || scan.featureType}
                                  </p>
                                  <p className="text-xs text-[#64748b] mt-0.5">
                                    {scan.status === 'completed' ? 'Completed' : 'Failed'} {formatTime(scan.startedAt)}
                                  </p>
                                  {scan.error && (
                                    <p className="text-xs text-danger mt-1 truncate">{scan.error}</p>
                                  )}
                                </div>
                              </div>
                              <button
                                onClick={() => removeScan(scan.id)}
                                className="text-[#64748b] hover:text-[#f1f5f9] transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0"
                                title="Remove from list"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
      {AlertModal}
    </>
  )
}
