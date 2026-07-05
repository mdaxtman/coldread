import { describe, expect, it } from 'vitest'
import { formatRunError } from '../format'

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
