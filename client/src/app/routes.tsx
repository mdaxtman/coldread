import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { AppShell } from '../components/layout/AppShell'
import { LandingPage } from '../features/landing/LandingPage'
import { ResultsDashboard } from '../features/results/ResultsDashboard'
import { JobDetailPage } from '../features/job-detail/JobDetailPage'

const rootRoute = createRootRoute({
  component: AppShell,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: LandingPage,
})

const resultsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/results/$jdId',
  component: ResultsDashboard,
})

const jobDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/job/$jdId',
  component: JobDetailPage,
})

const routeTree = rootRoute.addChildren([indexRoute, resultsRoute, jobDetailRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
