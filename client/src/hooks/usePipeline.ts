import { useCallback, useState } from 'react'
import { runFitAssessment, generateResume } from '../api/client'
import type { FitReport, ResumeVariant } from '../types'
import type { PipelineStep, StepStatus } from '../components/terminal/PipelineLog'
import { PIPELINE_STEPS } from '../constants'

export interface PipelineState {
  status: 'idle' | 'running' | 'done' | 'error'
  steps: PipelineStep[]
  fitReport: FitReport | null
  resumeVariant: ResumeVariant | null
  error: string | null
}

function makeSteps(overrides: Partial<Record<string, StepStatus>> = {}): PipelineStep[] {
  return PIPELINE_STEPS.map((s) => ({
    id: s.id,
    label: s.label,
    status: overrides[s.id] ?? ('pending' as StepStatus),
  }))
}

export function usePipeline() {
  const [state, setState] = useState<PipelineState>({
    status: 'idle',
    steps: makeSteps(),
    fitReport: null,
    resumeVariant: null,
    error: null,
  })

  const run = useCallback(async (jdId: string) => {
    setState({
      status: 'running',
      steps: makeSteps({ screener: 'running' }),
      fitReport: null,
      resumeVariant: null,
      error: null,
    })

    try {
      const fitReport = await runFitAssessment(jdId)

      setState((prev) => ({
        ...prev,
        fitReport,
        steps: makeSteps({ screener: 'done', generator: 'running' }),
      }))

      const resumeVariant = await generateResume(jdId)

      setState({
        status: 'done',
        steps: makeSteps({ screener: 'done', generator: 'done' }),
        fitReport,
        resumeVariant,
        error: null,
      })

      return { fitReport, resumeVariant }
    } catch (err) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Pipeline failed',
        steps: prev.steps.map((s) =>
          s.status === 'running' ? { ...s, status: 'error' as const } : s,
        ),
      }))
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      steps: makeSteps(),
      fitReport: null,
      resumeVariant: null,
      error: null,
    })
  }, [])

  return { ...state, run, reset }
}
