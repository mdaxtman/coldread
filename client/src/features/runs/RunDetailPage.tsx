import { Link, useParams } from '@tanstack/react-router'
import { useRunDetail } from '../../hooks/useRuns'
import { formatRunError } from '../../lib/format'
import { CodeBlock } from '../../components/terminal/CodeBlock'
import type { ContentBlockView, RequestView as RequestViewType } from '../../types'
import styles from './RunDetailPage.module.css'

/**
 * The server sends views, not the raw Anthropic payload (see RequestView in
 * types.ts). Message bodies and the system prompt arrive as size markers, so
 * this renders shape and scale — which is what the inspector is for — without
 * the runtime type guards the old untyped passthrough required.
 */
const RequestView = ({ request }: { request: RequestViewType }) => (
  <div className={styles.sections}>
    {request.system && (
      <details>
        <summary>system prompt</summary>
        <CodeBlock copyable>{request.system}</CodeBlock>
      </details>
    )}
    {request.messages.length > 0 && (
      <details open>
        <summary>messages ({request.messages.length})</summary>
        {request.messages.map((m, i) => (
          <div key={i} className={styles.message}>
            <span className={styles.role}>{m.role ?? 'message'}</span>
            <CodeBlock copyable>{m.content}</CodeBlock>
          </div>
        ))}
      </details>
    )}
    {request.toolNames.length > 0 && (
      <details>
        <summary>tools ({request.toolNames.length})</summary>
        <CodeBlock copyable>{request.toolNames.join('\n')}</CodeBlock>
      </details>
    )}
    <details>
      <summary>raw request</summary>
      <CodeBlock copyable>{JSON.stringify(request, null, 2)}</CodeBlock>
    </details>
  </div>
)

const ResponseView = ({ response }: { response: ContentBlockView[] }) => (
  <div className={styles.sections}>
    {response.map((b, i) => {
      if (b.type === 'text' && b.text) {
        return (
          <div key={i} className={styles.message}>
            <span className={styles.role}>text</span>
            <CodeBlock copyable>{b.text}</CodeBlock>
          </div>
        )
      }
      if (b.type === 'tool_use') {
        return (
          <div key={i} className={styles.message}>
            <span className={styles.role}>tool_use{b.name ? ` · ${b.name}` : ''}</span>
            <CodeBlock copyable>{JSON.stringify(b.input ?? b, null, 2)}</CodeBlock>
          </div>
        )
      }
      return (
        <div key={i} className={styles.message}>
          <span className={styles.role}>{b.type || 'block'}</span>
          <CodeBlock copyable>{JSON.stringify(b, null, 2)}</CodeBlock>
        </div>
      )
    })}
  </div>
)

export const RunDetailPage = () => {
  const { runId } = useParams({ from: '/runs/$runId' })
  const detail = useRunDetail(runId)
  if (detail.isLoading) return <div className={styles.loading}>Fetching run…</div>
  if (!detail.data) return <div className={styles.loading}>Run not found</div>
  const { run, calls } = detail.data
  return (
    <div className={styles.page}>
      <Link to="/runs" className={styles.back}>
        ← All runs
      </Link>
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
        {run.error && <p className={styles.error}>{formatRunError(run.error)}</p>}
      </header>
      {calls.map((c) => (
        <section key={c.id} className={styles.call}>
          <div className={styles.callHeader}>
            <span className={styles.seq}>{String(c.seq).padStart(2, '0')}</span>
            <span className={styles.stage}>{c.stage}</span>
            <span className={styles.callMeta}>
              {c.model} · {c.latencyMs}ms · {c.tokensIn}/{c.tokensOut} tok · {c.stopReason ?? '—'} ·
              ${c.estCostUsd.toFixed(3)}
            </span>
          </div>
          <details>
            <summary>request</summary>
            <RequestView request={c.request} />
          </details>
          <details>
            <summary>response</summary>
            <ResponseView response={c.response} />
          </details>
        </section>
      ))}
    </div>
  )
}
