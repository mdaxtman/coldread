import { Card } from '../../components/ui/Card'
import type { Match } from '../../types'

interface MatchesListProps {
  matches: Match[]
}

export const MatchesList = ({ matches }: MatchesListProps) => {
  if (matches.length === 0) return null

  return (
    <Card>
      <h3 style={{ marginBottom: 'var(--space-4)' }}>Matches</h3>
      <ul
        style={{
          listStyle: 'none',
          padding: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-2)',
        }}
      >
        {matches.map((match, i) => (
          <li
            key={i}
            style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: 'var(--space-2)',
              fontSize: 'var(--text-sm)',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--text-faint)',
                textTransform: 'uppercase',
              }}
            >
              {match.priority}
            </span>
            <span style={{ color: 'var(--fit-strong)' }}>{match.requirement}</span>
            {match.notes && <span style={{ color: 'var(--text-muted)' }}>— {match.notes}</span>}
          </li>
        ))}
      </ul>
    </Card>
  )
}
