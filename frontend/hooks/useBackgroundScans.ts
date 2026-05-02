import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface BackgroundScan {
  id: string
  projectId: string
  featureType: 'seo' | 'ai' | 'geo' | 'gsc' | 'ads' | 'keywords_gsc' | 'on_page' | 'technical' | 'gaps'
  status: 'scanning' | 'completed' | 'error'
  startedAt: number
  progress: number
  stage: string
  message: string
  error?: string
}

interface BackgroundScansStore {
  scans: BackgroundScan[]
  addScan: (scan: BackgroundScan) => void
  updateScan: (id: string, updates: Partial<BackgroundScan>) => void
  removeScan: (id: string) => void
  clearOldScans: () => void
  clearScans: () => void
}

export const useBackgroundScans = create<BackgroundScansStore>()(
  persist(
    (set) => ({
      scans: [],
      addScan: (scan) =>
        set((state) => ({
          scans: [...state.scans, scan],
        })),
      updateScan: (id, updates) =>
        set((state) => {
          const scan = state.scans.find((s) => s.id === id)
          if (!scan) return state

          // Check if any value actually changed to avoid unnecessary re-renders
          const hasChanges = Object.entries(updates).some(
            ([key, value]) => scan[key as keyof BackgroundScan] !== value
          )

          if (!hasChanges) return state

          return {
            scans: state.scans.map((s) =>
              s.id === id ? { ...s, ...updates } : s
            ),
          }
        }),
      removeScan: (id) =>
        set((state) => ({
          scans: state.scans.filter((scan) => scan.id !== id),
        })),
      clearOldScans: () =>
        set((state) => {
          const oneHourAgo = Date.now() - 60 * 60 * 1000
          return {
            scans: state.scans.filter(
              (scan) =>
                scan.status === 'scanning' || scan.startedAt > oneHourAgo
            ),
          }
        }),
      clearScans: () =>
        set({
          scans: [],
        }),
    }),
    {
      name: 'background-scans',
    }
  )
)
