import { Badge } from '../../components/ui/Badge'
import { ProgressBar } from '../../components/ui/ProgressBar'
import { Card } from '../../components/ui/Card'
import type { FitReport } from '../../types'
import styles from './FitSummary.module.css'

const fitScores: Record<string, number> = {
  strong: 90,
  moderate: 65,
  borderline: 40,
  poor: 20,
}

interface FitSummaryProps {
  report: FitReport
}

export function FitSummary({ report }: FitSummaryProps) {
  const score = fitScores[report.fitLevel] ?? 50

  return (
    <Card>
      <div className={styles.summary}>
        <div className={styles.scoreBlock}>
          <span className={styles.scoreLabel}>Fit Level</span>
          <Badge level={report.fitLevel} />
          <ProgressBar value={score} level={report.fitLevel} />
        </div>
        <p className={styles.reasoning}>{report.reasoning}</p>
      </div>
    </Card>
  )
}
