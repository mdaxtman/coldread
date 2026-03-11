import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { AppShell } from '../components/layout/AppShell'
import { LandingPage } from '../features/landing/LandingPage'
import { ResultsDashboard } from '../features/results/ResultsDashboard'
import { RecruiterPortal } from '../features/recruiter/RecruiterPortal'

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
  path: '/results',
  component: ResultsDashboard,
})

const recruiterRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/recruiter',
  component: RecruiterPortal,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  resultsRoute,
  recruiterRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
