import type { StageInfo } from '../../hooks/useRunStream'
import styles from './StageCards.module.css'

export const StageCards = ({ stages }: { stages: StageInfo[] }) => (
  <div className={styles.list}>
    {stages.map((s) => (
      <div key={s.seq} className={s.status === 'running' ? styles.cardRunning : styles.card}>
        <span className={styles.seq}>{String(s.seq).padStart(2, '0')}</span>
        <span className={styles.name}>{s.stage}</span>
        {s.status === 'running' ? (
          <span className={styles.spinner} aria-label="running" />
        ) : (
          <span className={styles.meta}>
            {s.model} · {s.latencyMs}ms · {s.tokensOut} tok
          </span>
        )}
      </div>
    ))}
  </div>
)
