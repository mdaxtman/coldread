import { useEffect, useRef, useState } from 'react'
import type { TraceLine } from '../../hooks/useRunStream'
import styles from './TracePanel.module.css'

const TONE_CLASS: Record<TraceLine['tone'], string> = {
  info: styles.info,
  machine: styles.machine,
  success: styles.success,
  error: styles.error,
}

/** Ticking elapsed clock — proof of life while the model call gives us no events. */
const Heartbeat = ({ since }: { since: number }) => {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 100)
    return () => clearInterval(id)
  }, [])
  return (
    <div className={styles.line}>
      <span className={styles.at}>+{((now - since) / 1000).toFixed(1)}s</span>
      <span className={styles.label} />
      <span className={styles.heartbeat}>
        <span className={styles.cursor} aria-hidden /> working…
      </span>
    </div>
  )
}

export const TracePanel = ({
  trace,
  live,
  startedAt,
}: {
  trace: TraceLine[]
  live: boolean
  startedAt?: number
}) => {
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (live) bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [trace.length, live])

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={live ? styles.liveDot : styles.idleDot} aria-hidden />
        <span>{live ? 'Live trace' : 'Trace'}</span>
      </div>
      <div className={styles.log}>
        {trace.map((line, i) => (
          <div key={i} className={styles.line}>
            <span className={styles.at}>+{(line.at / 1000).toFixed(2)}s</span>
            <span className={styles.label}>{line.label}</span>
            <span className={TONE_CLASS[line.tone]}>{line.message}</span>
          </div>
        ))}
        {live && startedAt != null && <Heartbeat since={startedAt} />}
        {live && startedAt == null && <span className={styles.cursor} aria-hidden />}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
