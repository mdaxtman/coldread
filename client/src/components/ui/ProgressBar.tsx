import type { FitLevel } from '../../types'
import styles from './ProgressBar.module.css'

interface ProgressBarProps {
  value: number
  max?: number
  level?: FitLevel
}

const levelColors: Record<FitLevel, string> = {
  strong: 'var(--fit-strong)',
  moderate: 'var(--fit-moderate)',
  borderline: 'var(--fit-borderline)',
  poor: 'var(--fit-poor)',
}

export const ProgressBar = ({ value, max = 100, level = 'moderate' }: ProgressBarProps) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div className={styles.track} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
      <div
        className={styles.fill}
        style={{ width: `${pct}%`, backgroundColor: levelColors[level] }}
      />
    </div>
  )
}
