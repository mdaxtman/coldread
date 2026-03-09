import type {
  CanonicalNarrative,
  FitReport,
  JobDescription,
  ResumeVariant,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

// Narratives
export const getNarratives = () =>
  request<CanonicalNarrative[]>('/narratives')

export const createNarrative = (data: Pick<CanonicalNarrative, 'title' | 'content'>) =>
  request<CanonicalNarrative>('/narratives', { method: 'POST', body: JSON.stringify(data) })

export const updateNarrative = (id: string, data: Pick<CanonicalNarrative, 'title' | 'content'>) =>
  request<CanonicalNarrative>(`/narratives/${id}`, { method: 'PUT', body: JSON.stringify(data) })

export const deleteNarrative = (id: string) =>
  request<void>(`/narratives/${id}`, { method: 'DELETE' })

// Job Descriptions
export const getJobDescriptions = () =>
  request<JobDescription[]>('/jds')

export const createJobDescription = (data: Pick<JobDescription, 'title' | 'company' | 'content'>) =>
  request<JobDescription>('/jds', { method: 'POST', body: JSON.stringify(data) })

// Pipeline
export const runFitAssessment = (jdId: string) =>
  request<FitReport>(`/jds/${jdId}/fit`)

export const generateResume = (jdId: string) =>
  request<ResumeVariant>(`/jds/${jdId}/resume`)

// Resume Variants
export const getResumeVariants = (jdId: string) =>
  request<ResumeVariant[]>(`/jds/${jdId}/resume/variants`)
