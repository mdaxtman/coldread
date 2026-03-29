import { useState } from 'react'
import {
  useGenerateResume,
  useRefineResume,
  useGetLatestResume,
} from '../hooks/useResumeGeneration'
import { ResumeVariantResponse } from '../types/resume'
import styles from './ResumeGenerator.module.css'

interface ResumeGeneratorProps {
  jdId: string
  onSuccess?: (variant: ResumeVariantResponse) => void
}

export function ResumeGenerator({ jdId, onSuccess }: ResumeGeneratorProps) {
  const [mode, setMode] = useState<'full' | 'refine'>('full')
  const generateMutation = useGenerateResume(jdId)
  const refineMutation = useRefineResume(jdId, '') // variant ID will be set in handler
  const { data: latestResume } = useGetLatestResume(jdId)

  const handleGenerate = async () => {
    if (mode === 'full') {
      const variant = await generateMutation.mutateAsync()
      onSuccess?.(variant)
    } else if (mode === 'refine' && latestResume) {
      const variant = await refineMutation.mutateAsync()
      onSuccess?.(variant)
    }
  }

  const isLoading = generateMutation.isPending || refineMutation.isPending
  const error = generateMutation.error || refineMutation.error
  const canRefine = latestResume !== null && mode === 'refine'

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Generate Resume</h3>

      <div className={styles.options}>
        <label className={styles.option}>
          <input
            type="radio"
            value="full"
            checked={mode === 'full'}
            onChange={(e) => setMode(e.target.value as 'full' | 'refine')}
            disabled={isLoading}
          />
          <span>Full regenerate (all 3 steps)</span>
        </label>
        <label className={styles.option}>
          <input
            type="radio"
            value="refine"
            checked={mode === 'refine'}
            onChange={(e) => setMode(e.target.value as 'full' | 'refine')}
            disabled={!latestResume || isLoading}
          />
          <span>Refine existing variant</span>
          {!latestResume && <span className={styles.optionLabel}>(No variant yet)</span>}
        </label>
      </div>

      {error && (
        <div className={styles.error}>
          {error instanceof Error ? error.message : 'An error occurred'}
        </div>
      )}

      <button
        onClick={handleGenerate}
        disabled={isLoading || (mode === 'refine' && !canRefine)}
        className={styles.button}
      >
        {isLoading ? 'Generating...' : 'Generate'}
      </button>
    </div>
  )
}
