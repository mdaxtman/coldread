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

export interface CulturalSignal {
  quality: string
  jdSignal: string
  evidenceHint: string
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
  overallScore: number | null
  semanticScore: number | null
  culturalSignals: CulturalSignal[]
  productConnection: string | null
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
  name?: string
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

export type RunKind = 'fit' | 'generate' | 'refine'
export type RunStatus = 'running' | 'completed' | 'failed'

export interface PipelineRun {
  id: string
  jobDescriptionId: string
  kind: RunKind
  status: RunStatus
  error: string | null
  startedAt: string
  finishedAt: string | null
  durationMs: number | null
  tokensIn: number
  tokensOut: number
  estCostUsd: number
  jdTitle: string | null
  jdCompany: string | null
}

/**
 * Wire contract for a stored model call, mirroring server/models.py.
 *
 * These are views, not the raw Anthropic payload. Message bodies and the system
 * prompt arrive as size markers — the server never sends the narratives or the
 * prompt template (#40, #59) — so nothing here needs a runtime shape guard.
 */
export interface MessageView {
  role: string | null
  content: string
}

export interface ContentBlockView {
  type: string
  text: string | null
  name: string | null
  input: Record<string, unknown> | null
}

export interface RequestView {
  model: string | null
  system: string | null
  messages: MessageView[]
  toolNames: string[]
}

export interface ModelCall {
  id: string
  stage: string
  seq: number
  model: string
  latencyMs: number
  tokensIn: number
  tokensOut: number
  stopReason: string | null
  estCostUsd: number
  request: RequestView
  response: ContentBlockView[]
  createdAt: string
}

export interface RunDetail {
  run: PipelineRun
  calls: ModelCall[]
}

export interface Prompt {
  id: string
  stage: string
  name: string
  version: number
  active: boolean
  template: string
}

export interface UsageSummary {
  tokensIn: number
  tokensOut: number
  estCostUsd: number
  runCount: number
}
