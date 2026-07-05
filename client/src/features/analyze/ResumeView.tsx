import ReactMarkdown from 'react-markdown'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import type { FitLevel, ResumeVariant } from '../../types'
import styles from './ResumeView.module.css'

interface ResumeViewProps {
  jdId: string
  variant: ResumeVariant
  fitReportId: string
  onRefine: (variantId: string) => void
}

function scoreToBucket(score: number): FitLevel {
  if (score >= 0.8) return 'strong'
  if (score >= 0.6) return 'moderate'
  if (score >= 0.4) return 'borderline'
  return 'poor'
}

export const ResumeView = ({ jdId, variant, fitReportId, onRefine }: ResumeViewProps) => {
  const { overallScore, semanticScore } = variant.screenerReport.screenerAnalysis
  const { changes } = variant.screenerReport.refinementChanges

  return (
    <div className={styles.view} data-jd-id={jdId} data-fit-report-id={fitReportId}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Resume
          <Badge level={scoreToBucket(overallScore)} label={`v${variant.version}`} />
        </h2>
        <Button onClick={() => onRefine(variant.id)}>Refine again</Button>
      </div>

      <Card className={styles.scores}>
        <div className={styles.score}>
          <span className={styles.scoreLabel}>Overall</span>
          <span className={styles.scoreValue}>{Math.round(overallScore * 100)}%</span>
        </div>
        <div className={styles.score}>
          <span className={styles.scoreLabel}>Semantic</span>
          <span className={styles.scoreValue}>{Math.round(semanticScore * 100)}%</span>
        </div>
      </Card>

      <Card className={styles.content}>
        <ReactMarkdown>{variant.content}</ReactMarkdown>
      </Card>

      {changes.length > 0 && (
        <Card className={styles.changes}>
          <h3 className={styles.changesTitle}>Refinement changes</h3>
          <ul className={styles.changeList}>
            {changes.map((change, i) => (
              <li key={i} className={styles.change}>
                <span className={styles.changeSection}>{change.section}</span>
                {change.changeDescription}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
