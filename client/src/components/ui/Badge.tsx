import type { FitLevel } from '../../types'
import styles from './Badge.module.css'

interface BadgeProps {
  level: FitLevel
  label?: string
}

export const Badge = ({ level, label }: BadgeProps) => {
  return (
    <span className={`${styles.badge} ${styles[level]}`}>
      {label ?? `${level} fit`}
    </span>
  )
}
