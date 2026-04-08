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

  const parts = []
  if (contact.email) parts.push(contact.email)
  if (contact.phone) parts.push(contact.phone)
  if (contact.location) parts.push(contact.location)
  if (contact.linkedin) parts.push(contact.linkedin)
  if (contact.github) parts.push(contact.github)
  if (contact.website) parts.push(contact.website)

  return parts.filter((p) => p).join(' | ')
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

  return (
    <div className={styles.panel}>
      {/* Contact info section */}
      {contactLine && (
        <div style={{ marginBottom: '1rem', fontFamily: 'monospace', fontSize: '0.95rem' }}>
          {contactLine}
        </div>
      )}

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

      {/* Resume content */}
      <div className={styles.resumeContent}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>

      {/* Export button */}
      <button type="button" className={styles.exportBtn} onClick={() => downloadResume(content)}>
        Download .txt
      </button>
    </div>
  )
}
