import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'
import { getFitReport, getJobDescription, getLatestResume } from '../../api/client'
import { useRunStream } from '../../hooks/useRunStream'
import { Button } from '../../components/ui/Button'
import { StageCards } from './StageCards'
import { TracePanel } from './TracePanel'
import { FitReportView } from './FitReportView'
import { ResumeView } from './ResumeView'
import styles from './RunView.module.css'

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

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>
          {jd.data?.title ?? 'Job description'} {jd.data?.company ? `· ${jd.data.company}` : ''}
        </p>
      </header>

      {streaming && (
        <div className={styles.streamLayout}>
          <StageCards stages={state.stages} />
          <TracePanel trace={state.trace} live />
        </div>
      )}

      {failed && (
        <div className={styles.failed}>
          <p className={styles.error}>{state.error}</p>
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

      {!streaming && !failed && fit.data && (
        <FitReportView
          jdId={jdId}
          fitReport={fit.data}
          resume={resume.data ?? null}
          onGenerate={() => void start(`/jds/${jdId}/resume/stream`, { fitReportId: fit.data.id })}
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

      {!streaming && !failed && !fit.data && !fit.isLoading && (
        <div className={styles.empty}>
          <p>No fit report yet for this JD.</p>
          <Button onClick={() => void start(`/jds/${jdId}/fit/stream`)}>Run fit assessment</Button>
        </div>
      )}
    </div>
  )
}
