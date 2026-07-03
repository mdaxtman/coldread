import { Link } from '@tanstack/react-router'
import { useRuns } from '../../hooks/useRuns'
import { Badge, type BadgeLevel } from '../../components/ui/Badge'
import type { PipelineRun, RunStatus } from '../../types'
import styles from './RunsPage.module.css'

const STATUS_BADGE: Record<RunStatus, BadgeLevel> = {
  completed: 'strong',
  failed: 'poor',
  running: 'machine',
}

const formatRelativeTime = (iso: string): string => {
  const deltaMs = Date.now() - new Date(iso).getTime()
  const deltaSec = Math.round(deltaMs / 1000)
  const units: Array<[string, number]> = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [unit, secs] of units) {
    const value = Math.floor(Math.abs(deltaSec) / secs)
    if (value >= 1) return `${value}${unit[0]} ago`
  }
  return 'just now'
}

const RunRow = ({ run }: { run: PipelineRun }) => (
  <tr>
    <td>{formatRelativeTime(run.startedAt)}</td>
    <td className={styles.kind}>{run.kind}</td>
    <td>
      <Link to="/runs/$runId" params={{ runId: run.id }} className={styles.jdLink}>
        {run.jdTitle ?? 'Untitled JD'}
        {run.jdCompany ? <span className={styles.jdCompany}> · {run.jdCompany}</span> : null}
      </Link>
    </td>
    <td>
      <Badge level={STATUS_BADGE[run.status]} label={run.status} />
    </td>
    <td className={styles.numeric}>
      {run.durationMs != null ? `${(run.durationMs / 1000).toFixed(1)}s` : '—'}
    </td>
    <td className={styles.numeric}>
      {run.tokensIn.toLocaleString()} / {run.tokensOut.toLocaleString()}
    </td>
    <td className={styles.numeric}>${run.estCostUsd.toFixed(3)}</td>
  </tr>
)

export const RunsPage = () => {
  const runs = useRuns()

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Observability</p>
        <h1>Runs</h1>
      </header>

      {runs.isLoading && <div className={styles.loading}>loading…</div>}
      {!runs.isLoading && runs.data?.length === 0 && (
        <div className={styles.empty}>No runs yet.</div>
      )}
      {!runs.isLoading && runs.data && runs.data.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>started</th>
              <th>kind</th>
              <th>job description</th>
              <th>status</th>
              <th>duration</th>
              <th>tokens in / out</th>
              <th>cost</th>
            </tr>
          </thead>
          <tbody>
            {runs.data.map((run) => (
              <RunRow key={run.id} run={run} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
