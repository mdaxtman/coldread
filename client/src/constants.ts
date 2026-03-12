// Pipeline step definitions used by PipelineLog and usePipeline hook.

export const PIPELINE_STEPS = [
  { id: 'screener', label: 'Running fit assessment...' },
  { id: 'generator', label: 'Generating resume variant...' },
] as const

export type PipelineStepId = (typeof PIPELINE_STEPS)[number]['id']
