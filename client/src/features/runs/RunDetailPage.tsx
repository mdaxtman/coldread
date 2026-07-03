import { useParams } from '@tanstack/react-router'
import { useRunDetail } from '../../hooks/useRuns'
import { CodeBlock } from '../../components/terminal/CodeBlock'
import styles from './RunDetailPage.module.css'

export const RunDetailPage = () => {
  const { runId } = useParams({ from: '/runs/$runId' })
  const detail = useRunDetail(runId)
  if (detail.isLoading) return <div className={styles.loading}>loading…</div>
  if (!detail.data) return <div className={styles.loading}>run not found</div>
  const { run, calls } = detail.data
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>
          {run.kind} run · {run.status}
        </p>
        <h1>
          {run.jdTitle ?? 'Untitled JD'} {run.jdCompany ? `· ${run.jdCompany}` : ''}
        </h1>
        <p className={styles.totals}>
          {run.durationMs != null ? `${(run.durationMs / 1000).toFixed(1)}s` : '—'} ·{' '}
          {run.tokensIn.toLocaleString()} in / {run.tokensOut.toLocaleString()} out · $
          {run.estCostUsd.toFixed(3)}
        </p>
        {run.error && <p className={styles.error}>{run.error}</p>}
      </header>
      {calls.map((c) => (
        <section key={c.id} className={styles.call}>
          <div className={styles.callHeader}>
            <span className={styles.seq}>{String(c.seq).padStart(2, '0')}</span>
            <span className={styles.stage}>{c.stage}</span>
            <span className={styles.callMeta}>
              {c.model} · {c.latencyMs}ms · {c.tokensIn}/{c.tokensOut} tok · {c.stopReason ?? '—'} ·
              ${c.estCostUsd.toFixed(4)}
            </span>
          </div>
          <details>
            <summary>request</summary>
            <CodeBlock>{JSON.stringify(c.request, null, 2)}</CodeBlock>
          </details>
          <details>
            <summary>response</summary>
            <CodeBlock>{JSON.stringify(c.response, null, 2)}</CodeBlock>
          </details>
        </section>
      ))}
    </div>
  )
}
