import { useQuery } from '@tanstack/react-query'
import { getJobDescription, getFitReport, getLatestResume } from '../api/client'
import type { FitReport, JobDescription, ResumeVariant } from '../types'

export interface ResultsData {
  jobDescription: JobDescription
  fitReport: FitReport
  resumeVariant: ResumeVariant
}

export const useResultsData = (jdId: string) => {
  const jdQuery = useQuery({ queryKey: ['jd', jdId], queryFn: () => getJobDescription(jdId) })
  const fitQuery = useQuery({ queryKey: ['fit', jdId], queryFn: () => getFitReport(jdId) })
  const resumeQuery = useQuery({
    queryKey: ['resume', jdId],
    queryFn: () => getLatestResume(jdId),
  })

  const isLoading = jdQuery.isLoading || fitQuery.isLoading || resumeQuery.isLoading
  const error = jdQuery.error ?? fitQuery.error ?? resumeQuery.error

  const data: ResultsData | null =
    jdQuery.data && fitQuery.data && resumeQuery.data
      ? { jobDescription: jdQuery.data, fitReport: fitQuery.data, resumeVariant: resumeQuery.data }
      : null

  return { data, isLoading, error }
}
