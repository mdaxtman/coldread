import ReactMarkdown from 'react-markdown'
import { Badge } from '../../components/ui/Badge'
import { ProgressBar } from '../../components/ui/ProgressBar'
import { Card } from '../../components/ui/Card'
import type { ResumeVariant, ResumeContact, FitLevel } from '../../types'
import styles from './ResumePanel.module.css'

interface ResumePanelProps {
  resumeVariant: ResumeVariant
  fitLevel: FitLevel
}

function formatContactInfo(contact?: ResumeContact): string {
  if (!contact) return ''

  const lines = []

  // Name as centered header (markdown center syntax with special formatting)
  if (contact.name) {
    lines.push(`# ${contact.name}`)
    lines.push('') // blank line after name
  }

  // Contact details on separate line
  const contactParts = []
  if (contact.email) contactParts.push(contact.email)
  if (contact.phone) contactParts.push(contact.phone)
  if (contact.location) contactParts.push(contact.location)
  if (contact.linkedin) contactParts.push(contact.linkedin)
  if (contact.github) contactParts.push(contact.github)
  if (contact.website) contactParts.push(contact.website)

  if (contactParts.length > 0) {
    lines.push(contactParts.join(' | '))
  }

  return lines.join('\n')
}

function scoreToBucket(score: number): FitLevel {
  if (score >= 0.8) return 'strong'
  if (score >= 0.6) return 'moderate'
  if (score >= 0.4) return 'borderline'
  return 'poor'
}

function downloadResume(content: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'resume.txt'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

export const ResumePanel = ({ resumeVariant, fitLevel }: ResumePanelProps) => {
  const { screenerReport, content, contactInfo } = resumeVariant
  const contactLine = formatContactInfo(contactInfo)
  const { keywordCoverage, semanticScore, overallScore } = screenerReport.screenerAnalysis

  const coveredCount = Object.values(keywordCoverage).filter(Boolean).length
  const totalCount = Object.keys(keywordCoverage).length

  // Prepend contact info to resume content if present
  const resumeWithContact = contactLine ? `${contactLine}\n\n${content}` : content

  return (
    <div className={styles.panel}>
      {/* Screener stats bar */}
      <Card className={styles.statsBar}>
        <div className={styles.stats}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Overall</span>
            <span className={styles.statValue}>{Math.round(overallScore * 100)}%</span>
            <ProgressBar value={overallScore * 100} level={scoreToBucket(overallScore)} />
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Semantic</span>
            <span className={styles.statValue}>{Math.round(semanticScore * 100)}%</span>
            <ProgressBar value={semanticScore * 100} level={scoreToBucket(semanticScore)} />
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Keywords</span>
            <span className={styles.statValue}>
              {coveredCount}/{totalCount}
            </span>
            <Badge level={fitLevel} label={`${coveredCount} of ${totalCount}`} />
          </div>
        </div>
      </Card>

      {/* Resume content with contact info */}
      <div className={styles.resumeContent}>
        <ReactMarkdown>{resumeWithContact}</ReactMarkdown>
      </div>

      {/* Export button */}
      <button
        type="button"
        className={styles.exportBtn}
        onClick={() => downloadResume(resumeWithContact)}
      >
        Download .txt
      </button>
    </div>
  )
}
