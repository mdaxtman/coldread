import type { FitLevel } from '../../types'
import styles from './Badge.module.css'

export type BadgeLevel = FitLevel | 'machine'

interface BadgeProps {
  level: BadgeLevel
  label?: string
}

export const Badge = ({ level, label }: BadgeProps) => {
  return <span className={`${styles.badge} ${styles[level]}`}>{label ?? `${level} fit`}</span>
}
