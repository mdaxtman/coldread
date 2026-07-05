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
 * Rough fit-run cost label: prompt + narratives dominate input (~21k tokens),
 * the report runs ~3k out, at claude-sonnet-5 list pricing ($3/M in, $15/M out).
 * An order-of-magnitude label for the run button — not billing.
 */
export function estimateFitCostUsd(jdChars: number): number {
  return ((21_000 + jdChars / 4) * 3 + 3_000 * 15) / 1_000_000
}
