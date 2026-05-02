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

const getBaseUrls = () => {
  if (typeof window === 'undefined') return { ws: '', http: '' }
  
  const isHttps = window.location.protocol === 'https:'
  const wsProtocol = isHttps ? 'wss:' : 'ws:'
  const httpProtocol = isHttps ? 'https:' : 'http:'
  
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || window.location.origin
  
  try {
    const url = new URL(apiUrl)
    const host = url.host
    // API URL usually includes /api suffix, we want to preserve it if present
    const path = url.pathname.replace(/\/$/, '')
    
    return {
      ws: `${wsProtocol}//${host}${path}`,
      http: `${httpProtocol}//${host}${path}`
    }
  } catch {
    return {
      ws: `${wsProtocol}//${window.location.host}/api`,
      http: `${httpProtocol}//${window.location.host}/api`
    }
  }
}

/**
 * Hook to connect to real-time scan progress via WebSocket.
 * Falls back to polling via HTTP if WebSocket fails.
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
  const { ws: baseWS, http: baseHTTP } = getBaseUrls()

  useEffect(() => {
    if (!taskId) {
      setProgress(0)
      setStage('')
      setMessage('')
      return
    }

    let pollFallbackActive = false

    const connectWebSocket = () => {
      try {
        const wsUrl = `${baseWS}/ws/scan/progress/${taskId}`
        console.log('Connecting to WebSocket:', wsUrl)
        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          setIsConnected(true)
          setError(null)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            // Backend sends 'connected' and 'progress' types
            if (data.progress !== undefined) {
              setProgress(data.progress)
              setStage(data.stage || '')
              setMessage(data.message || '')
              setElapsedSeconds(data.elapsed_seconds || 0)
              setEstimatedCompletionAt(data.estimated_completion_at || null)
            }
          } catch (e) {
            console.error('Error parsing progress message:', e)
          }
        }

        ws.onerror = (event) => {
          console.warn('WebSocket error, switching to polling')
          if (!pollFallbackActive) {
            pollFallbackActive = true
            startPolling()
          }
        }

        ws.onclose = () => {
          setIsConnected(false)
          if (!pollFallbackActive) {
            pollFallbackActive = true
            startPolling()
          }
        }

        wsRef.current = ws
      } catch (e) {
        console.error('WS setup error:', e)
        if (!pollFallbackActive) {
          pollFallbackActive = true
          startPolling()
        }
      }
    }

    const startPolling = () => {
      const headers: HeadersInit = { 'Accept': 'application/json' }
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`

      const poll = async () => {
        try {
          const res = await fetch(`${baseHTTP}/ws/scan/progress/${taskId}`, { headers })
          if (res.ok) {
            const data = await res.json()
            setProgress(data.progress ?? 0)
            setStage(data.stage || '')
            setMessage(data.message || '')
            setElapsedSeconds(data.elapsed_seconds || 0)
            setEstimatedCompletionAt(data.estimated_completion_at || null)
            setIsConnected(true)
            
            // If completed, stop polling
            if (data.progress === 100 || data.status === 'completed') {
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
            }
          }
        } catch (e) {
          setError('Polling failed')
        }
      }

      poll()
      pollIntervalRef.current = setInterval(poll, 2500)
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) wsRef.current.close()
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [taskId, authToken, baseWS, baseHTTP])

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
