import { Card } from '../../components/ui'
import type { Gap } from '../../types'
import styles from './GapsList.module.css'

interface GapsListProps {
  gaps: Gap[]
}

export function GapsList({ gaps }: GapsListProps) {
  if (gaps.length === 0) return null

  return (
    <Card>
      <h3 style={{ marginBottom: 'var(--space-4)' }}>Gaps</h3>
      <div className={styles.list}>
        {gaps.map((gap, i) => (
          <div key={i} className={styles.gap}>
            <span className={`${styles.type} ${styles[gap.type]}`}>{gap.type}</span>
            <div className={styles.details}>
              <span className={styles.requirement}>{gap.requirement}</span>
              {gap.notes && <span className={styles.notes}>{gap.notes}</span>}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
