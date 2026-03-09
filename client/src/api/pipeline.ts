// Pipeline orchestration — mirrors the server-side screener → generator → re-evaluator flow.
// The actual AI work happens server-side; this module coordinates client state during a run.

import { generateResume, runFitAssessment } from './client'
import type { FitReport, ResumeVariant } from '../types'

export interface PipelineResult {
  fitReport: FitReport
  resumeVariant: ResumeVariant
}

export async function runPipeline(jdId: string): Promise<PipelineResult> {
  const fitReport = await runFitAssessment(jdId)
  const resumeVariant = await generateResume(jdId)
  return { fitReport, resumeVariant }
}
