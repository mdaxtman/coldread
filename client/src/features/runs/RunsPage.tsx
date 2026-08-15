import { Link, useNavigate } from '@tanstack/react-router'
import { useRuns } from '../../hooks/useRuns'
import { Badge, type BadgeLevel } from '../../components/ui/Badge'
import { formatRelativeTime } from '../../lib/format'
import type { PipelineRun, RunStatus } from '../../types'
import styles from './RunsPage.module.css'

const STATUS_BADGE: Record<RunStatus, BadgeLevel> = {
  completed: 'strong',
  failed: 'poor',
  running: 'machine',
}

const RunRow = ({ run }: { run: PipelineRun }) => {
  const navigate = useNavigate()
  return (
    <tr
      className={styles.row}
      onClick={(e) => {
        // The title is a real <Link> (a11y / open-in-new-tab); don't double-navigate.
        if ((e.target as HTMLElement).closest('a')) return
        void navigate({ to: '/runs/$runId', params: { runId: run.id } })
      }}
    >
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
}

export const RunsPage = () => {
  const runs = useRuns()

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Observability</p>
        <h1>Runs</h1>
      </header>

      {runs.isLoading && <div className={styles.loading}>Fetching runs…</div>}
      {!runs.isLoading && runs.data?.length === 0 && (
        <div className={styles.empty}>No runs yet.</div>
      )}
      {!runs.isLoading && runs.data && runs.data.length > 0 && (
        <div className={styles.tableScroll}>
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
        </div>
      )}
    </div>
  )
}
