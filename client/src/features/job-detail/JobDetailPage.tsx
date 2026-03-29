import { useState } from 'react'
import { useParams } from '@tanstack/react-router'
import { ResumeGenerator } from '../../components/ResumeGenerator'
import { ScreenerReport } from '../../components/ScreenerReport'
import { ResumeHistory } from '../../components/ResumeHistory'
import { ResumeVariantResponse } from '../../types/resume'

export const JobDetailPage = () => {
  const { jdId } = useParams({ from: '/job/$jdId' })
  const [selectedVariant, setSelectedVariant] = useState<ResumeVariantResponse | null>(null)

  if (!jdId) {
    return (
      <div className="p-6">
        <p className="text-red-600">Job not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Job Analysis - Resume Generation</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Generator + History */}
        <div className="space-y-6">
          <ResumeGenerator jdId={jdId} onSuccess={setSelectedVariant} />
          <ResumeHistory jdId={jdId} onSelectVariant={setSelectedVariant} />
        </div>

        {/* Right: Selected Resume + Screener Report */}
        <div className="space-y-6">
          {selectedVariant && (
            <>
              <div className="border rounded-lg p-4 bg-white">
                <h3 className="text-lg font-semibold mb-3">Resume (v{selectedVariant.version})</h3>
                <pre className="text-sm whitespace-pre-wrap max-h-96 overflow-y-auto border p-2 bg-gray-50 rounded">
                  {selectedVariant.content}
                </pre>
              </div>
              <ScreenerReport report={selectedVariant.screenerReport} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
