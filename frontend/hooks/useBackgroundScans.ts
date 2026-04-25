import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface BackgroundScan {
  id: string
  projectId: string
  featureType: 'seo' | 'ai' | 'geo' | 'gsc' | 'ads' | 'full'
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
        set((state) => ({
          scans: state.scans.map((scan) =>
            scan.id === id ? { ...scan, ...updates } : scan
          ),
        })),
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
    }),
    {
      name: 'background-scans',
    }
  )
)
