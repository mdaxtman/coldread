import { useListResumeVariants } from '../hooks/useResumeGeneration'
import { ResumeVariantResponse } from '../types/resume'

interface ResumeHistoryProps {
  jdId: string
  onSelectVariant?: (variant: ResumeVariantResponse) => void
}

export function ResumeHistory({ jdId, onSelectVariant }: ResumeHistoryProps) {
  const { data: variants, isLoading, error } = useListResumeVariants(jdId)

  if (isLoading) return <div>Loading variants...</div>
  if (error) return <div>Error loading variants</div>
  if (!variants || variants.length === 0) {
    return <div className="p-4 text-gray-500">No resume variants yet</div>
  }

  // Build lineage tree
  const buildLineage = (variants: ResumeVariantResponse[]) => {
    const byId = new Map(variants.map((v) => [v.id, v]))
    const byParent = new Map<string | null, ResumeVariantResponse[]>()

    for (const variant of variants) {
      const parentId = variant.parentVariantId || 'root'
      if (!byParent.has(parentId)) byParent.set(parentId, [])
      byParent.get(parentId)!.push(variant)
    }

    return { byId, byParent }
  }

  const { byParent } = buildLineage(variants)
  const roots = byParent.get('root') || []

  return (
    <div className="p-4 border rounded-lg space-y-4">
      <h3 className="text-lg font-semibold">Resume Variants</h3>

      <div className="space-y-3">
        {roots.map((variant) => (
          <ResumeVariantNode
            key={variant.id}
            variant={variant}
            children={byParent.get(variant.id) || []}
            onSelect={onSelectVariant}
          />
        ))}
      </div>
    </div>
  )
}

function ResumeVariantNode({
  variant,
  children,
  onSelect,
}: {
  variant: ResumeVariantResponse
  children: ResumeVariantResponse[]
  onSelect?: (v: ResumeVariantResponse) => void
}) {
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`

    return date.toLocaleDateString()
  }

  return (
    <div className="ml-0">
      <button
        onClick={() => onSelect?.(variant)}
        className="block w-full text-left p-3 rounded border hover:bg-blue-50 transition"
      >
        <div className="font-semibold">v{variant.version}</div>
        <div className="text-sm text-gray-600">{formatTimeAgo(variant.createdAt)}</div>
        <div className="text-sm text-gray-500">
          Score: {(variant.screenerReport.screenerAnalysis.overallScore * 100).toFixed(0)}%
        </div>
      </button>

      {children.length > 0 && (
        <div className="ml-4 border-l-2 border-gray-300 pl-4 space-y-2 mt-2">
          {children.map((child) => (
            <ResumeVariantNode
              key={child.id}
              variant={child}
              children={[]} // Simplified: assume single-level chains
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}
