import { Card } from '../../components/ui/Card'

interface MatchesListProps {
  matches: string[]
}

export const MatchesList = ({ matches }: MatchesListProps) => {
  if (matches.length === 0) return null

  return (
    <Card>
      <h3 style={{ marginBottom: 'var(--space-4)' }}>Matches</h3>
      <ul
        style={{
          paddingLeft: 'var(--space-5)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-2)',
        }}
      >
        {matches.map((match, i) => (
          <li key={i} style={{ color: 'var(--fit-strong)', fontSize: 'var(--text-sm)' }}>
            {match}
          </li>
        ))}
      </ul>
    </Card>
  )
}
