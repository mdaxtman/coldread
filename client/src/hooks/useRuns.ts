import { useQuery } from '@tanstack/react-query'
import { getPrompts, getRunDetail, getRuns, getUsageSummary } from '../api/client'

export const useRuns = () => useQuery({ queryKey: ['runs'], queryFn: getRuns })

export const useRunDetail = (runId: string) =>
  useQuery({ queryKey: ['run', runId], queryFn: () => getRunDetail(runId) })

export const usePrompts = () => useQuery({ queryKey: ['prompts'], queryFn: getPrompts })

export const useUsageSummary = () => useQuery({ queryKey: ['usage'], queryFn: getUsageSummary })
