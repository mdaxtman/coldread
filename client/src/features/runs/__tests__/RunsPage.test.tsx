import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../../../api/client', () => ({
  getRuns: vi.fn().mockResolvedValue([
    {
      id: 'run-1',
      jobDescriptionId: 'jd-1',
      kind: 'fit',
      status: 'completed',
      error: null,
      startedAt: '2026-07-03T10:00:00Z',
      finishedAt: '2026-07-03T10:00:07Z',
      durationMs: 6780,
      tokensIn: 3318,
      tokensOut: 1102,
      estCostUsd: 0.041,
      jdTitle: 'Staff FE',
      jdCompany: 'Foundry',
    },
  ]),
  getUsageSummary: vi
    .fn()
    .mockResolvedValue({ tokensIn: 0, tokensOut: 0, estCostUsd: 0, runCount: 0 }),
}))

// RunsPage renders links via TanStack <Link>; a <Link> rendered outside a
// RouterProvider throws, so we mount it via a real memory router (same
// pattern as AnalyzePage.test.tsx) rather than rendering <RunsPage /> bare.

describe('RunsPage', () => {
  it('lists runs with telemetry columns', async () => {
    const history = createMemoryHistory({ initialEntries: ['/runs'] })
    const { routeTree } = await import('../../../app/routes')
    const router = createRouter({ routeTree, history })
    render(
      <QueryClientProvider client={new QueryClient()}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )
    expect(await screen.findByText('Staff FE')).toBeInTheDocument()
    expect(screen.getByText(/\$0\.041/)).toBeInTheDocument()
    expect(screen.getByText(/3,?318/)).toBeInTheDocument()
  })
})
