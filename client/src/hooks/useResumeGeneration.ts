import { useMutation, useQuery } from '@tanstack/react-query'
import { ResumeVariantResponse } from '../types/resume'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useGenerateResume(jdId: string) {
  return useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE}/jds/${jdId}/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Generation failed')
      }
      return response.json() as Promise<ResumeVariantResponse>
    },
  })
}

export function useRefineResume(jdId: string, variantId: string) {
  return useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE}/jds/${jdId}/resume/refine/${variantId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Refinement failed')
      }
      return response.json() as Promise<ResumeVariantResponse>
    },
  })
}

export function useGetLatestResume(jdId: string) {
  return useQuery({
    queryKey: ['resume', jdId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/jds/${jdId}/resume`, {
        credentials: 'include',
      })
      if (!response.ok) {
        if (response.status === 404) return null
        throw new Error('Failed to fetch resume')
      }
      return response.json() as Promise<ResumeVariantResponse>
    },
  })
}

export function useListResumeVariants(jdId: string) {
  return useQuery({
    queryKey: ['resume-variants', jdId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/jds/${jdId}/resume/variants`, {
        credentials: 'include',
      })
      if (!response.ok) {
        throw new Error('Failed to fetch variants')
      }
      return response.json() as Promise<ResumeVariantResponse[]>
    },
  })
}
