import { useEffect, useRef } from 'react'
import type { TraceLine } from '../../hooks/useRunStream'
import styles from './TracePanel.module.css'

const TONE_CLASS: Record<TraceLine['tone'], string> = {
  info: styles.info,
  machine: styles.machine,
  success: styles.success,
  error: styles.error,
}

export const TracePanel = ({ trace, live }: { trace: TraceLine[]; live: boolean }) => {
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [trace.length])

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={live ? styles.liveDot : styles.idleDot} aria-hidden />
        <span>Live trace</span>
      </div>
      <div className={styles.log}>
        {trace.map((line, i) => (
          <div key={i} className={styles.line}>
            <span className={styles.at}>+{(line.at / 1000).toFixed(2)}s</span>
            <span className={styles.label}>{line.label}</span>
            <span className={TONE_CLASS[line.tone]}>{line.message}</span>
          </div>
        ))}
        {live && <span className={styles.cursor} aria-hidden />}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
