import { DataTable } from '../../components/terminal/DataTable'
import type { TerminologyAlignment } from '../../types'

interface TerminologyTableProps {
  terminology: TerminologyAlignment[]
}

const columns = [
  { key: 'myTerm' as const, header: 'Your Term' },
  { key: 'jdTerm' as const, header: 'JD Term' },
]

export function TerminologyTable({ terminology }: TerminologyTableProps) {
  if (terminology.length === 0) return null

  return (
    <div>
      <h3 style={{ marginBottom: 'var(--space-4)' }}>Terminology Alignment</h3>
      <DataTable columns={columns} data={terminology} />
    </div>
  )
}
