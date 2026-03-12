import type { ReactNode } from 'react'
import styles from './AnnotatedJd.module.css'

interface AnnotatedJdProps {
  content: string
  keywordCoverage: Record<string, boolean>
}

/**
 * Renders JD text with keyword highlights — green for covered, red for uncovered.
 * Uses word-boundary regex for case-insensitive matching.
 */
export const AnnotatedJd = ({ content, keywordCoverage }: AnnotatedJdProps) => {
  const keywords = Object.keys(keywordCoverage)
  if (keywords.length === 0) {
    return <pre className={styles.jd}>{content}</pre>
  }

  // Build a single regex matching all keywords, longest first to avoid partial matches
  const sorted = [...keywords].sort((a, b) => b.length - a.length)
  const escaped = sorted.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const pattern = new RegExp(`\\b(${escaped.join('|')})\\b`, 'gi')

  // Split content into text and keyword segments
  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index))
    }

    const word = match[0]
    // Find the keyword key (case-insensitive lookup)
    const key = keywords.find((k) => k.toLowerCase() === word.toLowerCase()) ?? word
    const covered = keywordCoverage[key] ?? false

    parts.push(
      <mark key={match.index} className={covered ? styles.covered : styles.uncovered}>
        {word}
      </mark>,
    )
    lastIndex = pattern.lastIndex
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex))
  }

  return <pre className={styles.jd}>{parts}</pre>
}
