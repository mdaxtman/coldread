// Core domain types for ColdRead.
// All records include user_id — populated with DEFAULT_USER_ID server-side.

export interface JobDescription {
  id: string
  userId: string
  title: string | null
  company: string | null
  content: string // raw JD text
  createdAt: string
}

export type FitLevel = 'strong' | 'moderate' | 'borderline' | 'poor'
export type GapType = 'hard' | 'soft'
export type MatchPriority = 'required' | 'preferred' | 'implied'

export interface Match {
  requirement: string
  priority: MatchPriority
  notes: string
}

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
  matches: Match[]
  gaps: Gap[]
  terminology: TerminologyAlignment[]
  reasoning: string
  createdAt: string
}

export interface ScreenerAnalysisData {
  keywordCoverage: Record<string, boolean>
  semanticScore: number
  coverageGaps: Gap[]
  terminologyMismatches: TerminologyAlignment[]
  overallScore: number
}

export interface RefinementChangeData {
  sectionsModified: string[]
  changes: Array<{ section: string; changeDescription: string }>
  remainingGaps: Array<{ requirement: string; whyUnfixable: string }>
  coverageImprovement: number
}

export interface ScreenerReport {
  screenerAnalysis: ScreenerAnalysisData
  refinementChanges: RefinementChangeData
}

export interface ResumeContact {
  email?: string
  phone?: string
  location?: string
  linkedin?: string
  github?: string
  website?: string
}

export interface ResumeVariant {
  id: string
  userId: string
  jobDescriptionId: string
  content: string
  contactInfo?: ResumeContact
  version: number
  parentVariantId: string | null
  screenerReport: ScreenerReport
  createdAt: string
}
