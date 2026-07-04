import { Link, useParams } from '@tanstack/react-router'
import { useRunDetail } from '../../hooks/useRuns'
import { formatRunError } from '../../lib/format'
import { CodeBlock } from '../../components/terminal/CodeBlock'
import styles from './RunDetailPage.module.css'

interface ContentBlock {
  type?: string
  text?: string
  name?: string
  input?: unknown
}

interface RequestMessage {
  role?: string
  content?: string | ContentBlock[]
}

const textOfContent = (content: RequestMessage['content']): string => {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content
      .map((b) => (typeof b.text === 'string' ? b.text : JSON.stringify(b, null, 2)))
      .join('\n\n')
  }
  return JSON.stringify(content, null, 2)
}

/**
 * The stored request is the raw Anthropic payload. Rendering its parts
 * separately (with real newlines) is the whole point — a JSON.stringify of
 * the payload shows prompts as one line of `\n` escapes.
 */
const RequestView = ({ request }: { request: Record<string, unknown> }) => {
  const system = typeof request.system === 'string' ? request.system : null
  const messages = Array.isArray(request.messages) ? (request.messages as RequestMessage[]) : []
  const tools = Array.isArray(request.tools) ? (request.tools as unknown[]) : []

  return (
    <div className={styles.sections}>
      {system && (
        <details>
          <summary>system prompt</summary>
          <CodeBlock copyable>{system}</CodeBlock>
        </details>
      )}
      {messages.length > 0 && (
        <details open>
          <summary>messages ({messages.length})</summary>
          {messages.map((m, i) => (
            <div key={i} className={styles.message}>
              <span className={styles.role}>{m.role ?? 'message'}</span>
              <CodeBlock copyable>{textOfContent(m.content)}</CodeBlock>
            </div>
          ))}
        </details>
      )}
      {tools.length > 0 && (
        <details>
          <summary>tool schema ({tools.length})</summary>
          <CodeBlock copyable>{JSON.stringify(tools, null, 2)}</CodeBlock>
        </details>
      )}
      <details>
        <summary>raw request</summary>
        <CodeBlock copyable>{JSON.stringify(request, null, 2)}</CodeBlock>
      </details>
    </div>
  )
}

const ResponseView = ({ response }: { response: unknown[] }) => (
  <div className={styles.sections}>
    {response.map((block, i) => {
      const b = (block ?? {}) as ContentBlock
      if (b.type === 'text' && typeof b.text === 'string') {
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
            <CodeBlock copyable>{JSON.stringify(b.input ?? block, null, 2)}</CodeBlock>
          </div>
        )
      }
      return (
        <div key={i} className={styles.message}>
          <span className={styles.role}>{b.type ?? 'block'}</span>
          <CodeBlock copyable>{JSON.stringify(block, null, 2)}</CodeBlock>
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
