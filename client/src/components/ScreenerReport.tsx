import { ScreenerReportData } from '../types/resume'

interface ScreenerReportProps {
  report: ScreenerReportData
}

export function ScreenerReport({ report }: ScreenerReportProps) {
  const { screenerAnalysis, refinementChanges } = report

  return (
    <div className="space-y-6 p-4 border rounded-lg bg-gray-50">
      <h3 className="text-lg font-semibold">ATS Analysis & Refinement</h3>

      {/* Screener Analysis */}
      <section>
        <h4 className="text-sm font-bold uppercase text-gray-600 mb-3">ATS Screener Analysis</h4>
        <div className="bg-white p-4 rounded space-y-4">
          <div>
            <span className="text-sm font-semibold">Overall Score:</span>
            <div className="flex items-center space-x-2 mt-1">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${screenerAnalysis.overallScore * 100}%`,
                  }}
                />
              </div>
              <span className="text-sm font-bold">
                {(screenerAnalysis.overallScore * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {screenerAnalysis.terminologyMismatches.length > 0 && (
            <div>
              <span className="text-sm font-semibold">Terminology Mismatches:</span>
              <ul className="mt-2 space-y-1">
                {screenerAnalysis.terminologyMismatches.map((tm, i) => (
                  <li key={i} className="text-sm">
                    <code className="bg-yellow-50 px-1">{tm.myTerm}</code>
                    {' → '}
                    <code className="bg-green-50 px-1">{tm.jdTerm}</code>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {screenerAnalysis.coverageGaps && screenerAnalysis.coverageGaps.length > 0 && (
            <div>
              <span className="text-sm font-semibold">Coverage Gaps:</span>
              <ul className="mt-2 space-y-2">
                {screenerAnalysis.coverageGaps.map((gap, i) => (
                  <li key={i} className="text-sm">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                        gap.gapType === 'hard'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {gap.gapType.toUpperCase()}
                    </span>
                    <div className="mt-1">{gap.requirement}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

      {/* Refinement Changes */}
      <section>
        <h4 className="text-sm font-bold uppercase text-gray-600 mb-3">Refinement Changes</h4>
        <div className="bg-white p-4 rounded space-y-4">
          <div>
            <span className="text-sm font-semibold">Coverage Improvement:</span>
            <div className="flex items-center space-x-2 mt-1">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{
                    width: `${refinementChanges.coverageImprovement * 100}%`,
                  }}
                />
              </div>
              <span className="text-sm font-bold">
                +{(refinementChanges.coverageImprovement * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {refinementChanges.changes.length > 0 && (
            <div>
              <span className="text-sm font-semibold">Changes Made:</span>
              <ul className="mt-2 space-y-2">
                {refinementChanges.changes.map((change, i) => (
                  <li key={i} className="text-sm">
                    <span className="font-mono bg-blue-50 px-1">{change.section}</span>:{' '}
                    {change.changeDescription}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {refinementChanges.remainingGaps.length > 0 && (
            <div>
              <span className="text-sm font-semibold">Authentic Gaps (Unfixable):</span>
              <ul className="mt-2 space-y-2">
                {refinementChanges.remainingGaps.map((gap, i) => (
                  <li key={i} className="text-sm text-gray-700">
                    <div className="font-semibold">{gap.requirement}</div>
                    <div className="text-gray-600 italic">{gap.whyUnfixable}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
