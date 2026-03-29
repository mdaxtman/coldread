/**
 * Resume Generation Pipeline Types
 *
 * Types for the three-step resume generation pipeline:
 * Generator → Screener → Refinement
 *
 * All types match the API response schema and support
 * both full regenerate and refine-existing modes.
 */

/**
 * Keyword coverage analysis from screener
 * Maps JD keywords to whether they appear in the resume
 */
export type KeywordCoverage = Record<string, boolean>

/**
 * Coverage gap identified by screener
 * Represents a requirement from JD that's missing/insufficient in resume
 */
export interface CoverageGap {
  requirement: string
  /** 'hard': explicitly required, likely dealbreaker; 'soft': preferred or partially covered */
  gapType: 'hard' | 'soft'
  /** Why this gap impacts the fit */
  impact: string
}

/**
 * Terminology mismatch between candidate's language and JD's language
 * Fixable gap where experience exists but vocabulary doesn't match
 */
export interface TerminologyMismatch {
  myTerm: string
  jdTerm: string
}

/**
 * ATS screener analysis
 * Evaluates the generated resume against job description from keyword/coverage perspective
 */
export interface ScreenerAnalysisData {
  keywordCoverage: KeywordCoverage
  semanticScore: number // 0-1 overall semantic match
  coverageGaps: CoverageGap[]
  terminologyMismatches: TerminologyMismatch[]
  overallScore: number // 0-1 combined score
}

/**
 * Change made during refinement step
 * Documents what was modified to improve coverage
 */
export interface RefinementChange {
  section: string // e.g., "experience", "skills"
  changeDescription: string
}

/**
 * Gap that couldn't be closed during refinement
 * Preserved gaps due to authentic voice preservation (no fabrication)
 */
export interface RemainingGap {
  requirement: string
  whyUnfixable: string
}

/**
 * Refinement changes from step 3
 * Documents improvements made to resume based on screener feedback
 */
export interface RefinementChangeData {
  sectionsModified: string[] // which sections were updated
  changes: RefinementChange[]
  remainingGaps: RemainingGap[]
  /** Estimated improvement in coverage score (0-1 delta) */
  coverageImprovement: number
}

/**
 * Complete screener report
 * Contains both initial analysis and refinement changes
 */
export interface ScreenerReportData {
  screenerAnalysis: ScreenerAnalysisData
  refinementChanges: RefinementChangeData
}

/**
 * Resume variant response from API
 * Single row in resume_variants table with all pipeline output
 */
export interface ResumeVariantResponse {
  id: string
  userId: string
  jobDescriptionId: string
  /** Final refined resume content (from refinement step) */
  content: string
  /** Auto-incremented; new version per regenerate/refine operation */
  version: number
  /** NULL for full regenerate; points to input variant for refine-existing mode */
  parentVariantId: string | null
  /** Complete screener report with analysis + refinement changes */
  screenerReport: ScreenerReportData
  createdAt: string
}

/**
 * Match between resume and job description
 * Used in fit reports for highlighting aligned requirements
 */
export interface MatchModel {
  requirement: string
  priority: 'required' | 'preferred' | 'implied'
  notes: string
}

/**
 * Gap in coverage
 * Represents unmet requirements from job description
 */
export interface GapModel {
  requirement: string
  type: 'hard' | 'soft'
  notes: string
}

/**
 * Terminology alignment model
 * Represents terminology mismatches that can be addressed
 */
export interface TerminologyAlignmentModel {
  myTerm: string
  jdTerm: string
}
