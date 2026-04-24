// hooks/useScanProgress.ts
import { useEffect, useState, useCallback, useRef } from 'react'

export interface ScanProgressData {
  type: string
  task_id: string
  project_id: string
  stage: string
  progress: number
  message: string
  elapsed_seconds?: number
  estimated_completion_at?: string
}

export interface UseScanProgressReturn {
  progress: number
  stage: string
  message: string
  elapsedSeconds: number
  estimatedCompletionAt: string | null
  isConnected: boolean
  error: string | null
}

const getBaseWSUrl = () => {
  if (typeof window === 'undefined') return ''
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || window.location.origin
  
  // Parse API URL to get host
  try {
    const url = new URL(apiUrl)
    return `${protocol}//${url.host}/api`
  } catch {
    return `${protocol}//${window.location.host}/api`
  }
}

/**
 * Hook to connect to real-time scan progress via WebSocket.
 * Falls back to polling via HTTP if WebSocket fails.
 * 
 * Usage:
 *   const { progress, stage, message, isConnected } = useScanProgress(taskId, token)
 */
export function useScanProgress(
  taskId: string | null,
  authToken: string | null
): UseScanProgressReturn {
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [message, setMessage] = useState('')
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [estimatedCompletionAt, setEstimatedCompletionAt] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Try WebSocket first, fallback to polling
  useEffect(() => {
    if (!taskId || !authToken) return

    let wsAttempted = false
    let pollFallback = false

    // Try WebSocket connection
    const connectWebSocket = () => {
      try {
        const wsUrl = `${getBaseWSUrl()}/ws/scan/progress/${taskId}`
        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          console.log('WebSocket connected for progress updates')
          setIsConnected(true)
          setError(null)
          wsAttempted = true
        }

        ws.onmessage = (event) => {
          try {
            const data: ScanProgressData = JSON.parse(event.data)
            
            if (data.type === 'progress') {
              setProgress(data.progress)
              setStage(data.stage)
              setMessage(data.message)
              setElapsedSeconds(data.elapsed_seconds || 0)
              setEstimatedCompletionAt(data.estimated_completion_at || null)
            }
          } catch (e) {
            console.error('Error parsing progress message:', e)
          }
        }

        ws.onerror = (event) => {
          console.warn('WebSocket error, falling back to polling:', event)
          ws.close()
          wsRef.current = null
          
          // Fallback to HTTP polling
          if (!pollFallback) {
            pollFallback = true
            pollHTTP()
          }
        }

        ws.onclose = () => {
          console.log('WebSocket closed')
          setIsConnected(false)
          wsRef.current = null
        }

        wsRef.current = ws
      } catch (e) {
        console.error('WebSocket connection error:', e)
        setError('Failed to connect to progress stream')
        
        // Fallback to HTTP polling
        if (!pollFallback) {
          pollFallback = true
          pollHTTP()
        }
      }
    }

    // Fallback: HTTP polling every 2 seconds
    const pollHTTP = () => {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`
      }

      const poll = async () => {
        try {
          const response = await fetch(
            `${getBaseWSUrl()}/ws/scan/progress/${taskId}`,
            { headers }
          )
          
          if (response.ok) {
            const data = await response.json()
            setProgress(data.progress || 0)
            setStage(data.stage || '')
            setMessage(data.message || '')
            setElapsedSeconds(data.elapsed_seconds || 0)
            setEstimatedCompletionAt(data.estimated_completion_at || null)
            setIsConnected(true)
            setError(null)
          }
        } catch (e) {
          console.warn('HTTP polling error:', e)
          setError('Unable to fetch progress updates')
        }
      }

      poll() // Poll immediately
      pollIntervalRef.current = setInterval(poll, 2000)
    }

    connectWebSocket()

    return () => {
      // Cleanup
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [taskId, authToken])

  return {
    progress,
    stage,
    message,
    elapsedSeconds,
    estimatedCompletionAt,
    isConnected,
    error,
  }
}
