// Core domain types for ColdRead.
// All records include user_id — populated with DEFAULT_USER_ID server-side.

export interface JobDescription {
  id: string
  userId: string
  title: string
  company: string
  content: string // raw JD text
  createdAt: string
}

export type FitLevel = 'strong' | 'moderate' | 'borderline' | 'poor'
export type GapType = 'hard' | 'soft'

export interface Gap {
  requirement: string
  type: GapType
  notes: string
}

export interface TerminologyAlignment {
  myTerm: string
  jdTerm: string
}

export interface FitReport {
  id: string
  userId: string
  jobDescriptionId: string
  fitLevel: FitLevel
  matches: string[]
  gaps: Gap[]
  terminology: TerminologyAlignment[]
  reasoning: string
  createdAt: string
}

export interface ScreenerReport {
  keywordCoverage: Record<string, boolean>
  semanticScore: number
  terminologyMismatches: TerminologyAlignment[]
  overallScore: number
}

export interface ResumeVariant {
  id: string
  userId: string
  jobDescriptionId: string
  content: string
  version: number
  parentVariantId: string | null
  screenerReport: ScreenerReport
  createdAt: string
}
