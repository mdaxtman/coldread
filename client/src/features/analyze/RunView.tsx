import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'
import {
  getFitReport,
  getJobDescription,
  getLatestResume,
  updateJobDescription,
} from '../../api/client'
import { estimateFitCostUsd, formatRunError } from '../../lib/format'
import { useRunStream } from '../../hooks/useRunStream'
import { Button } from '../../components/ui/Button'
import { StageCards } from './StageCards'
import { TracePanel } from './TracePanel'
import { FitReportView } from './FitReportView'
import { ResumeView } from './ResumeView'
import styles from './RunView.module.css'

const EditableTitle = ({ jdId, title }: { jdId: string; title: string }) => {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<string | null>(null)
  const rename = useMutation({
    mutationFn: (t: string) => updateJobDescription(jdId, t),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['jd', jdId] })
      void queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })

  const commit = () => {
    const next = draft?.trim()
    if (next && next !== title) rename.mutate(next)
    setDraft(null)
  }

  if (draft === null) {
    return (
      <h1 className={styles.title}>
        <button
          type="button"
          className={styles.titleButton}
          onClick={() => setDraft(title)}
          title="Rename this JD"
        >
          {title}
          <span className={styles.titleEditHint} aria-hidden>
            edit
          </span>
        </button>
      </h1>
    )
  }
  return (
    <input
      className={styles.titleInput}
      value={draft}
      autoFocus
      maxLength={200}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === 'Enter') commit()
        if (e.key === 'Escape') setDraft(null)
      }}
      aria-label="Job description title"
    />
  )
}

export const RunView = () => {
  const { jdId } = useParams({ from: '/analyze/$jdId' })
  const queryClient = useQueryClient()
  const { state, start, reset } = useRunStream()

  const jd = useQuery({ queryKey: ['jd', jdId], queryFn: () => getJobDescription(jdId) })
  const fit = useQuery({ queryKey: ['fit', jdId], queryFn: () => getFitReport(jdId), retry: false })
  const resume = useQuery({
    queryKey: ['resume', jdId],
    queryFn: () => getLatestResume(jdId),
    retry: false,
  })

  useEffect(() => {
    if (state.status === 'complete') {
      void queryClient.invalidateQueries({ queryKey: ['fit', jdId] })
      void queryClient.invalidateQueries({ queryKey: ['resume', jdId] })
      void queryClient.invalidateQueries({ queryKey: ['runs'] })
    }
  }, [state.status, jdId, queryClient])

  const streaming = state.status === 'streaming'
  const failed = state.status === 'failed'
  const loading = jd.isLoading || fit.isLoading

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>
          Fit assessment {jd.data?.company ? `· ${jd.data.company}` : ''}
        </p>
        {jd.data && <EditableTitle jdId={jdId} title={jd.data.title ?? 'Untitled JD'} />}
      </header>

      {streaming && (
        <div className={styles.streamLayout}>
          <StageCards stages={state.stages} />
          <TracePanel trace={state.trace} live startedAt={state.startedAt} />
        </div>
      )}

      {failed && (
        <div className={styles.failed}>
          <p className={styles.error}>{formatRunError(state.error)}</p>
          <p className={styles.errorHint}>
            The partial trace below survived — closing this tab mid-run cancels it (see{' '}
            <a href="/runs">runs</a> for history).
          </p>
          <TracePanel trace={state.trace} live={false} />
          <Button
            onClick={() => {
              reset()
              void start(`/jds/${jdId}/fit/stream`)
            }}
          >
            Retry
          </Button>
        </div>
      )}

      {state.status === 'complete' && state.trace.length > 0 && (
        <details className={styles.traceKeep}>
          <summary className={styles.traceSummary}>
            Run trace
            {state.totals
              ? ` · ${((state.totals.durationMs ?? 0) / 1000).toFixed(1)}s · $${state.totals.estCostUsd.toFixed(3)}`
              : ''}
          </summary>
          <TracePanel trace={state.trace} live={false} />
        </details>
      )}

      {!streaming && !failed && fit.data && (
        <FitReportView
          jdId={jdId}
          fitReport={fit.data}
          resume={resume.data ?? null}
          onGenerate={() => void start(`/jds/${jdId}/resume/stream`, { fitReportId: fit.data.id })}
          jobDescription={jd.data ?? null}
        />
      )}

      {!streaming && !failed && fit.data && resume.data && (
        <ResumeView
          jdId={jdId}
          variant={resume.data}
          fitReportId={fit.data.id}
          onRefine={(variantId) =>
            void start(`/jds/${jdId}/resume/refine/${variantId}/stream`, {
              fitReportId: fit.data.id,
            })
          }
        />
      )}

      {!streaming && !failed && loading && (
        <div className={styles.loading}>Fetching workspace…</div>
      )}

      {!streaming && !failed && !loading && !fit.data && jd.data && (
        <div className={styles.launch}>
          <div className={styles.launchIntro}>
            <p className={styles.launchTitle}>Ready for a cold read.</p>
            <p className={styles.launchHint}>
              One model call reads this JD against your career narratives and returns an honest fit
              report — matches, gaps, terminology drift.
            </p>
            <Button onClick={() => void start(`/jds/${jdId}/fit/stream`)}>
              Run fit assessment · ≈ ${estimateFitCostUsd(jd.data.content.length).toFixed(2)}
            </Button>
          </div>
          <pre className={styles.jdPreview}>{jd.data.content}</pre>
        </div>
      )}
    </div>
  )
}
