import { useCallback, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { runFitAssessment, generateResume } from '../api/client'
import type { PipelineStep, StepStatus } from '../components/terminal/PipelineLog'
import { PIPELINE_STEPS } from '../constants'

function makeSteps(overrides: Partial<Record<string, StepStatus>> = {}): PipelineStep[] {
  return PIPELINE_STEPS.map((s) => ({
    id: s.id,
    label: s.label,
    status: overrides[s.id] ?? ('pending' as StepStatus),
  }))
}

export const usePipeline = () => {
  const [steps, setSteps] = useState<PipelineStep[]>(makeSteps())

  const mutation = useMutation({
    mutationFn: async (jdId: string) => {
      setSteps(makeSteps({ screener: 'running' }))
      const fitReport = await runFitAssessment(jdId)

      setSteps(makeSteps({ screener: 'done', generator: 'running' }))
      const resumeVariant = await generateResume(jdId)

      setSteps(makeSteps({ screener: 'done', generator: 'done' }))
      return { fitReport, resumeVariant }
    },
    onError: () => {
      setSteps((prev) =>
        prev.map((s) => (s.status === 'running' ? { ...s, status: 'error' as const } : s)),
      )
    },
  })

  const reset = useCallback(() => {
    mutation.reset()
    setSteps(makeSteps())
  }, [mutation])

  return { ...mutation, steps, reset }
}
