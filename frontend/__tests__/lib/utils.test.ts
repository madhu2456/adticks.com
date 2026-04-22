import {
  cn,
  formatNumber,
  formatCurrency,
  formatPercent,
  formatDate,
  formatRelativeTime,
  getTrendColor,
  getTrendSymbol,
  getScoreColor,
  getDifficultyColor,
  truncate,
} from '@/lib/utils'

describe('cn utility', () => {
  it('merges class names correctly', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes (false is excluded)', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible')
  })

  it('handles undefined values', () => {
    expect(cn('base', undefined, 'end')).toBe('base end')
  })

  it('resolves Tailwind conflicts — last one wins', () => {
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
  })

  it('returns empty string for no arguments', () => {
    expect(cn()).toBe('')
  })
})

describe('formatNumber', () => {
  it('formats a number with commas', () => {
    expect(formatNumber(1000)).toBe('1,000')
    expect(formatNumber(1234567)).toBe('1,234,567')
  })

  it('formats compact K', () => {
    expect(formatNumber(2400, true)).toBe('2.4K')
  })

  it('formats compact M', () => {
    expect(formatNumber(1500000, true)).toBe('1.5M')
  })

  it('returns plain number when compact and < 1000', () => {
    expect(formatNumber(500, true)).toBe('500')
  })
})

describe('formatCurrency', () => {
  it('formats USD correctly', () => {
    expect(formatCurrency(1000)).toBe('$1,000')
  })

  it('formats with decimals when present', () => {
    const result = formatCurrency(99.99)
    expect(result).toContain('99.99')
  })
})

describe('formatPercent', () => {
  it('formats to 1 decimal by default', () => {
    expect(formatPercent(3.567)).toBe('3.6%')
  })

  it('respects custom decimal count', () => {
    expect(formatPercent(3.567, 2)).toBe('3.57%')
  })
})

describe('formatDate', () => {
  it('formats a date string', () => {
    const result = formatDate('2024-01-15')
    expect(result).toMatch(/Jan/)
    expect(result).toMatch(/15/)
    expect(result).toMatch(/2024/)
  })

  it('formats a Date object', () => {
    const result = formatDate(new Date('2024-06-01'))
    expect(result).toMatch(/Jun/)
  })
})

describe('formatRelativeTime', () => {
  it('returns "just now" for very recent times', () => {
    expect(formatRelativeTime(new Date().toISOString())).toBe('just now')
  })

  it('returns minutes ago', () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
    expect(formatRelativeTime(fiveMinutesAgo)).toBe('5m ago')
  })

  it('returns hours ago', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
    expect(formatRelativeTime(twoHoursAgo)).toBe('2h ago')
  })

  it('returns days ago for less than a week', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
    expect(formatRelativeTime(threeDaysAgo)).toBe('3d ago')
  })
})

describe('getTrendColor', () => {
  it('returns success color for positive change', () => {
    expect(getTrendColor(5)).toBe('text-success')
  })

  it('returns danger color for negative change', () => {
    expect(getTrendColor(-3)).toBe('text-danger')
  })

  it('returns muted color for zero change', () => {
    expect(getTrendColor(0)).toBe('text-text-muted')
  })
})

describe('getTrendSymbol', () => {
  it('returns up arrow for positive change', () => {
    expect(getTrendSymbol(1)).toBe('↑')
  })

  it('returns down arrow for negative change', () => {
    expect(getTrendSymbol(-1)).toBe('↓')
  })

  it('returns dash for zero change', () => {
    expect(getTrendSymbol(0)).toBe('—')
  })
})

describe('getScoreColor', () => {
  it('returns green for score >= 80', () => {
    expect(getScoreColor(80)).toBe('#10b981')
    expect(getScoreColor(95)).toBe('#10b981')
  })

  it('returns amber for score 60–79', () => {
    expect(getScoreColor(60)).toBe('#f59e0b')
    expect(getScoreColor(75)).toBe('#f59e0b')
  })

  it('returns orange for score 40–59', () => {
    expect(getScoreColor(40)).toBe('#f97316')
  })

  it('returns red for score < 40', () => {
    expect(getScoreColor(20)).toBe('#ef4444')
  })
})

describe('getDifficultyColor', () => {
  it('returns green for easy difficulty (<= 30)', () => {
    expect(getDifficultyColor(20)).toBe('#10b981')
  })

  it('returns amber for medium difficulty (31–60)', () => {
    expect(getDifficultyColor(50)).toBe('#f59e0b')
  })

  it('returns red for hard difficulty (> 60)', () => {
    expect(getDifficultyColor(80)).toBe('#ef4444')
  })
})

describe('truncate', () => {
  it('truncates long strings with ellipsis', () => {
    expect(truncate('Hello World', 5)).toBe('Hello...')
  })

  it('returns original string when within length', () => {
    expect(truncate('Hi', 10)).toBe('Hi')
  })

  it('returns original string when exactly at length', () => {
    expect(truncate('Hello', 5)).toBe('Hello')
  })
})
