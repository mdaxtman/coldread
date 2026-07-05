import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../../../api/client', () => ({
  createJobDescription: vi.fn(),
  getRuns: vi.fn().mockResolvedValue([]),
  getUsageSummary: vi
    .fn()
    .mockResolvedValue({ tokensIn: 0, tokensOut: 0, estCostUsd: 0, runCount: 0 }),
}))

describe('AnalyzePage ?jd= ingest', () => {
  it('prefills the textarea from ?jd= and scrubs the param', async () => {
    const history = createMemoryHistory({ initialEntries: ['/?jd=Hello%20JD'] })
    const { routeTree } = await import('../../../app/routes')
    const router = createRouter({ routeTree, history })
    render(
      <QueryClientProvider client={new QueryClient()}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )
    const textarea = await screen.findByRole('textbox')
    await waitFor(() => expect(textarea).toHaveValue('Hello JD'))
    await waitFor(() => expect(router.state.location.search).toEqual({}))
  })
})
