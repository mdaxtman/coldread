import { useState } from 'react'
import {
  useGenerateResume,
  useRefineResume,
  useGetLatestResume,
} from '../hooks/useResumeGeneration'
import { ResumeVariantResponse } from '../types/resume'

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
    <div className="space-y-4 p-4 border rounded-lg">
      <h3 className="text-lg font-semibold">Generate Resume</h3>

      <div className="space-y-2">
        <label className="flex items-center space-x-2">
          <input
            type="radio"
            value="full"
            checked={mode === 'full'}
            onChange={(e) => setMode(e.target.value as 'full' | 'refine')}
            disabled={isLoading}
          />
          <span>Full regenerate (all 3 steps)</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="radio"
            value="refine"
            checked={mode === 'refine'}
            onChange={(e) => setMode(e.target.value as 'full' | 'refine')}
            disabled={!latestResume || isLoading}
          />
          <span>Refine existing variant</span>
          {!latestResume && <span className="text-sm text-gray-500">(No variant yet)</span>}
        </label>
      </div>

      {error && (
        <div className="p-2 bg-red-100 text-red-800 rounded text-sm">
          {error instanceof Error ? error.message : 'An error occurred'}
        </div>
      )}

      <button
        onClick={handleGenerate}
        disabled={isLoading || (mode === 'refine' && !canRefine)}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        {isLoading ? 'Generating...' : 'Generate'}
      </button>
    </div>
  )
}
