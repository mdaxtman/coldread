import { useMutation, useQuery } from '@tanstack/react-query'
import { ResumeVariantResponse } from '../types/resume'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function apiFetch<T>(url: string, method: 'GET' | 'POST' = 'GET'): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
    credentials: 'include',
  })

  if (!response.ok) {
    if (response.status === 404) return null as T
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Request failed: ${response.statusText}`)
  }

  return response.json() as Promise<T>
}

export function useGenerateResume(jdId: string) {
  return useMutation({
    mutationFn: async () =>
      apiFetch<ResumeVariantResponse>(`${API_BASE}/jds/${jdId}/resume`, 'POST'),
  })
}

export function useRefineResume(jdId: string, variantId: string) {
  return useMutation({
    mutationFn: async () =>
      apiFetch<ResumeVariantResponse>(`${API_BASE}/jds/${jdId}/resume/refine/${variantId}`, 'POST'),
  })
}

export function useGetLatestResume(jdId: string) {
  return useQuery({
    queryKey: ['resume', jdId],
    queryFn: async () => apiFetch<ResumeVariantResponse>(`${API_BASE}/jds/${jdId}/resume`),
  })
}

export function useListResumeVariants(jdId: string) {
  return useQuery({
    queryKey: ['resume-variants', jdId],
    queryFn: async () =>
      apiFetch<ResumeVariantResponse[]>(`${API_BASE}/jds/${jdId}/resume/variants`),
  })
}
