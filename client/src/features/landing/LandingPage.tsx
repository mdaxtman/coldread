import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { PipelineLog } from '../../components/terminal/PipelineLog'
import { createJobDescription } from '../../api/client'
import { usePipeline } from '../../hooks/usePipeline'
import { JdInput } from './JdInput'
import styles from './LandingPage.module.css'

export const LandingPage = () => {
  const [jdText, setJdText] = useState('')
  const createJd = useMutation({ mutationFn: createJobDescription })
  const pipeline = usePipeline()
  const navigate = useNavigate()

  const isRunning = createJd.isPending || pipeline.isPending
  const canRun = jdText.trim().length > 0 && !isRunning
  const error = createJd.error?.message ?? pipeline.error?.message

  async function handleRun() {
    if (!canRun) return

    try {
      const jd = await createJd.mutateAsync({
        title: 'Untitled Position',
        company: 'Unknown',
        content: jdText.trim(),
      })

      await pipeline.mutateAsync(jd.id)
      navigate({ to: '/results/$jdId', params: { jdId: jd.id } })
    } catch {
      // Errors are captured in createJd.error / pipeline.error
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.tagline}>AI-powered resume analysis</h1>
      <p className={styles.subtitle}>
        Paste a job description to get a fit assessment and tailored resume.
      </p>

      <div className={styles.form}>
        <JdInput value={jdText} onChange={setJdText} disabled={isRunning} />

        <div className={styles.actions}>
          <Button size="lg" onClick={handleRun} disabled={!canRun}>
            {isRunning ? 'Running...' : 'Run Analysis'}
          </Button>
          {error && <span className={styles.error}>{error}</span>}
        </div>
      </div>

      {pipeline.status !== 'idle' && (
        <div className={styles.pipelineSection}>
          <PipelineLog steps={pipeline.steps} />
        </div>
      )}
    </div>
  )
}
