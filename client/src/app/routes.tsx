import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { AppShell } from '../components/layout/AppShell'
import { AnalyzePage } from '../features/analyze/AnalyzePage'
import { RunView } from '../features/analyze/RunView'
import { RunsPage } from '../features/runs/RunsPage'
import { RunDetailPage } from '../features/runs/RunDetailPage'
import { PromptsPage } from '../features/prompts/PromptsPage'

const rootRoute = createRootRoute({ component: AppShell })

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: AnalyzePage,
  validateSearch: (search: Record<string, unknown>): { jd?: string } => ({
    jd: typeof search.jd === 'string' && search.jd.length > 0 ? search.jd : undefined,
  }),
})

const analyzeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/analyze/$jdId',
  component: RunView,
})

const runsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/runs',
  component: RunsPage,
})

const runDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/runs/$runId',
  component: RunDetailPage,
})

const promptsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/prompts',
  component: PromptsPage,
})

export const routeTree = rootRoute.addChildren([
  indexRoute,
  analyzeRoute,
  runsRoute,
  runDetailRoute,
  promptsRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
