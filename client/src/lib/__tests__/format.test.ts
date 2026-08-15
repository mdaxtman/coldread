import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { formatRelativeTime, formatRunError } from '../format'

describe('formatRunError', () => {
  it('translates a bare Python KeyError repr from historical runs', () => {
    expect(formatRunError("'refined_content'")).toBe(
      "The model's response was missing the expected field 'refined_content'.",
    )
  })

  it('passes through already-humanized messages', () => {
    const msg = 'The refine run failed — the model timed out.'
    expect(formatRunError(msg)).toBe(msg)
  })

  it('returns null for empty errors', () => {
    expect(formatRunError(null)).toBeNull()
    expect(formatRunError('')).toBeNull()
  })
})

describe('formatRelativeTime', () => {
  const NOW = new Date('2026-08-15T12:00:00.000Z')
  const ago = (ms: number) => new Date(NOW.getTime() - ms).toISOString()

  const MINUTE = 60_000
  const HOUR = 60 * MINUTE
  const DAY = 24 * HOUR
  const MONTH = 30 * DAY
  const YEAR = 365 * DAY

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(NOW)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // The bug: abbreviations were taken as unit[0], so 'month' and 'minute'
  // both rendered as 'm' and a run from last month read as one minute old.
  it('does not render months and minutes with the same abbreviation', () => {
    expect(formatRelativeTime(ago(MONTH))).not.toBe(formatRelativeTime(ago(MINUTE)))
  })

  it('renders months as mo', () => {
    expect(formatRelativeTime(ago(MONTH))).toBe('1mo ago')
    expect(formatRelativeTime(ago(3 * MONTH))).toBe('3mo ago')
  })

  it('renders minutes as m', () => {
    expect(formatRelativeTime(ago(MINUTE))).toBe('1m ago')
    expect(formatRelativeTime(ago(45 * MINUTE))).toBe('45m ago')
  })

  it('renders years, days and hours', () => {
    expect(formatRelativeTime(ago(YEAR))).toBe('1y ago')
    expect(formatRelativeTime(ago(2 * DAY))).toBe('2d ago')
    expect(formatRelativeTime(ago(5 * HOUR))).toBe('5h ago')
  })

  it('renders anything under a minute as just now', () => {
    expect(formatRelativeTime(ago(30_000))).toBe('just now')
    expect(formatRelativeTime(ago(0))).toBe('just now')
  })
})
