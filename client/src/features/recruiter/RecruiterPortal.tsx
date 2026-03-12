import { Link } from '@tanstack/react-router'
import { Button } from '../../components/ui/Button'
import { FitSummary } from '../results/FitSummary'
import { MatchesList } from '../results/MatchesList'
import { GapsList } from '../results/GapsList'
import { usePipelineResult } from '../../hooks/usePipelineResult'

export function RecruiterPortal() {
  const { result } = usePipelineResult()

  if (!result) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-20) 0', color: 'var(--text-muted)' }}>
        <p>No results available.</p>
        <Link to="/" style={{ marginTop: 'var(--space-4)', display: 'inline-block' }}>
          <Button variant="secondary">Run Analysis</Button>
        </Link>
      </div>
    )
  }

  const { fitReport } = result

  return (
    <div style={{ animation: 'fadeIn var(--duration-normal) var(--ease-default)' }}>
      <h1 style={{ fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-2)' }}>
        Candidate Summary
      </h1>
      <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-8)' }}>
        Read-only overview for recruiters.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        <FitSummary report={fitReport} />
        <MatchesList matches={fitReport.matches} />
        <GapsList gaps={fitReport.gaps} />
      </div>
    </div>
  )
}
