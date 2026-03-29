import { useListResumeVariants } from '../hooks/useResumeGeneration'
import { ResumeVariantResponse } from '../types/resume'
import styles from './ResumeHistory.module.css'

interface ResumeHistoryProps {
  jdId: string
  onSelectVariant?: (variant: ResumeVariantResponse) => void
}

export function ResumeHistory({ jdId, onSelectVariant }: ResumeHistoryProps) {
  const { data: variants, isLoading, error } = useListResumeVariants(jdId)

  if (isLoading) return <div className={styles.loadingState}>Loading variants...</div>
  if (error) return <div className={styles.errorState}>Error loading variants</div>
  if (!variants || variants.length === 0) {
    return <div className={styles.emptyState}>No resume variants yet</div>
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
    <div className={styles.container}>
      <h3 className={styles.title}>Resume Variants</h3>

      <div className={styles.list}>
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
    <div>
      <button onClick={() => onSelect?.(variant)} className={styles.variantButton}>
        <div className={styles.variantVersion}>v{variant.version}</div>
        <div className={styles.variantTime}>{formatTimeAgo(variant.createdAt)}</div>
        <div className={styles.variantScore}>
          Score: {(variant.screenerReport.screenerAnalysis.overallScore * 100).toFixed(0)}%
        </div>
      </button>

      {children.length > 0 && (
        <div className={styles.childrenContainer}>
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
