/**
 * Presentation boundary for run failures.
 *
 * Runs recorded before the server started humanizing errors have a raw
 * Python KeyError repr stored verbatim — literally `'refined_content'` —
 * so the client keeps a translation for historical rows.
 */
export function formatRunError(error: string | null | undefined): string | null {
  if (!error) return null
  const keyError = /^'([\w.-]+)'$/.exec(error.trim())
  if (keyError) {
    return `The model's response was missing the expected field '${keyError[1]}'.`
  }
  return error
}

/**
 * Compact "3d ago" timestamps for run lists.
 *
 * Abbreviations are explicit rather than derived from the unit name: taking the
 * first letter collapsed 'month' and 'minute' onto the same 'm', so a run from
 * last month was indistinguishable from one a minute old.
 */
const RELATIVE_UNITS: Array<[abbrev: string, seconds: number]> = [
  ['y', 31_536_000],
  ['mo', 2_592_000],
  ['d', 86_400],
  ['h', 3_600],
  ['m', 60],
]

export function formatRelativeTime(iso: string): string {
  const deltaSec = Math.round((Date.now() - new Date(iso).getTime()) / 1000)
  for (const [abbrev, seconds] of RELATIVE_UNITS) {
    const value = Math.floor(Math.abs(deltaSec) / seconds)
    if (value >= 1) return `${value}${abbrev} ago`
  }
  return 'just now'
}

/**
 * Rough fit-run cost label: prompt + narratives dominate input (~21k tokens),
 * the report runs ~3k out, at claude-sonnet-5 list pricing ($3/M in, $15/M out).
 * An order-of-magnitude label for the run button — not billing.
 */
export function estimateFitCostUsd(jdChars: number): number {
  return ((21_000 + jdChars / 4) * 3 + 3_000 * 15) / 1_000_000
}
