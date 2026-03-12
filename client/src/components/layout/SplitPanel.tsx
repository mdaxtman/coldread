import type { ReactNode } from 'react'
import styles from './SplitPanel.module.css'

interface SplitPanelProps {
  children: ReactNode
}

export const SplitPanel = ({ children }: SplitPanelProps) => {
  return <div className={styles.split}>{children}</div>
}
