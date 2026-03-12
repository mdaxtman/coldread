import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Button } from '../../components/ui/Button'
import { PipelineLog } from '../../components/terminal/PipelineLog'
import { createJobDescription } from '../../api/client'
import { usePipeline } from '../../hooks/usePipeline'
import { usePipelineResult } from '../../hooks/usePipelineResult'
import { JdInput } from './JdInput'
import styles from './LandingPage.module.css'

export function LandingPage() {
  const [jdText, setJdText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const pipeline = usePipeline()
  const { setPipelineResult } = usePipelineResult()
  const navigate = useNavigate()

  const isRunning = pipeline.status === 'running'
  const canRun = jdText.trim().length > 0 && !isRunning && !submitting

  async function handleRun() {
    if (!canRun) return
    setSubmitting(true)

    try {
      const jd = await createJobDescription({
        title: 'Untitled Position',
        company: 'Unknown',
        content: jdText.trim(),
      })

      const result = await pipeline.run(jd.id)
      if (result) {
        setPipelineResult({ jobDescription: jd, ...result })
        navigate({ to: '/results' })
      }
    } catch {
      // Pipeline hook handles its own errors; this catches JD creation failures
    } finally {
      setSubmitting(false)
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
          {pipeline.error && <span className={styles.error}>{pipeline.error}</span>}
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
