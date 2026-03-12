import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { router } from './routes'
import { MOCK_PIPELINE_RESULT } from '../mocks/data'

// Toggle to false to disable mock data seeding.
const USE_MOCK = true

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

if (USE_MOCK) {
  queryClient.setQueryData(['pipelineResult'], MOCK_PIPELINE_RESULT)
}

export const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
