import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { WebSocketProvider } from '@/lib/websocket'
import { PageErrorBoundary } from '@/shared/components'
import { ToastProvider } from '@/shared/components/ToastProvider'
import { UploadQueuePanel } from '@/features/uploads/components/UploadQueuePanel'
import { router } from './routes'
import './i18n' // Initialize i18n
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PageErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <WebSocketProvider debug={false}>
          <RouterProvider router={router} />
          <ToastProvider />
          <UploadQueuePanel />
          <ReactQueryDevtools initialIsOpen={false} />
        </WebSocketProvider>
      </QueryClientProvider>
    </PageErrorBoundary>
  </React.StrictMode>,
)
