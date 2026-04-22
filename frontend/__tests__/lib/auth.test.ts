import {
  setTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  setUser,
  getUser,
  isAuthenticated,
  getTrialDaysLeft,
} from '@/lib/auth'

// localStorage is mocked globally in jest.setup.ts
const mockLocalStorage = window.localStorage as jest.Mocked<typeof window.localStorage>

describe('auth utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('setTokens / getAccessToken / getRefreshToken', () => {
    it('stores access and refresh tokens in localStorage', () => {
      setTokens({ access_token: 'acc_123', refresh_token: 'ref_456', token_type: 'bearer' })
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('adticks_access_token', 'acc_123')
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('adticks_refresh_token', 'ref_456')
    })

    it('getAccessToken retrieves the access token', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'adticks_access_token') return 'acc_123'
        return null
      })
      expect(getAccessToken()).toBe('acc_123')
    })

    it('getRefreshToken retrieves the refresh token', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'adticks_refresh_token') return 'ref_456'
        return null
      })
      expect(getRefreshToken()).toBe('ref_456')
    })

    it('getAccessToken returns null when no token stored', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      expect(getAccessToken()).toBeNull()
    })
  })

  describe('clearTokens', () => {
    it('removes access token, refresh token, and user from localStorage', () => {
      clearTokens()
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('adticks_access_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('adticks_refresh_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('adticks_user')
    })
  })

  describe('setUser / getUser', () => {
    const mockUser = {
      id: 'user-1',
      email: 'test@example.com',
      name: 'Test User',
      plan: 'pro' as const,
      created_at: new Date().toISOString(),
    }

    it('stores user as JSON in localStorage', () => {
      setUser(mockUser)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'adticks_user',
        JSON.stringify(mockUser)
      )
    })

    it('retrieves and parses the stored user', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'adticks_user') return JSON.stringify(mockUser)
        return null
      })
      const user = getUser()
      expect(user).toEqual(mockUser)
      expect(user?.email).toBe('test@example.com')
    })

    it('returns null when no user is stored', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      expect(getUser()).toBeNull()
    })

    it('returns null when stored user is invalid JSON', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'adticks_user') return 'not-valid-json{'
        return null
      })
      expect(getUser()).toBeNull()
    })
  })

  describe('isAuthenticated', () => {
    it('returns false when no access token stored', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      expect(isAuthenticated()).toBe(false)
    })

    it('returns true when an access token exists', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'adticks_access_token') return 'some_token'
        return null
      })
      expect(isAuthenticated()).toBe(true)
    })
  })

  describe('getTrialDaysLeft', () => {
    it('returns 0 when no trialEndsAt is provided', () => {
      expect(getTrialDaysLeft(undefined)).toBe(0)
    })

    it('returns 0 when trial has already ended', () => {
      const pastDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
      expect(getTrialDaysLeft(pastDate)).toBe(0)
    })

    it('returns correct days remaining for future trial end', () => {
      const futureDateMs = Date.now() + 5 * 24 * 60 * 60 * 1000
      // Add a small buffer to account for ceiling math
      const futureDate = new Date(futureDateMs).toISOString()
      const days = getTrialDaysLeft(futureDate)
      expect(days).toBeGreaterThanOrEqual(4)
      expect(days).toBeLessThanOrEqual(6)
    })
  })
})
