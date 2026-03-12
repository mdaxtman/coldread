// React Query-based hook replacing the old ResultsContext.
// The pipeline result is seeded into the cache via queryClient.setQueryData
// rather than fetched — there's no server endpoint that returns a combined result.

import { useQueryClient, useQuery } from '@tanstack/react-query'
import { useCallback } from 'react'
import type { FitReport, JobDescription, ResumeVariant } from '../types'

export interface PipelineResult {
  jobDescription: JobDescription
  fitReport: FitReport
  resumeVariant: ResumeVariant
}

const QUERY_KEY = ['pipelineResult'] as const

export const usePipelineResult = () => {
  const queryClient = useQueryClient()

  const { data: result = null } = useQuery<PipelineResult | null>({
    queryKey: QUERY_KEY,
    // No fetcher — data is seeded manually via setPipelineResult
    queryFn: () => null,
    staleTime: Infinity,
  })

  const setPipelineResult = useCallback(
    (value: PipelineResult) => {
      queryClient.setQueryData<PipelineResult | null>(QUERY_KEY, value)
    },
    [queryClient],
  )

  const clearPipelineResult = useCallback(() => {
    queryClient.setQueryData<PipelineResult | null>(QUERY_KEY, null)
  }, [queryClient])

  return { result, setPipelineResult, clearPipelineResult }
}
