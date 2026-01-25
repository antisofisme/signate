/**
 * ATLAS_CHAT_AI - Main Application
 * RAG Chat with 4-Layer Memory System
 *
 * Architecture: MANTRA/PUGUH style with domain-based navigation
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { SidebarLayout } from '@/components/layout/SidebarLayout'
import {
  Dashboard,
  Chat,
  Search,
  Memory,
  Sessions,
  Tenants,
  Users,
  APIKeys,
  Settings,
} from '@/pages'

// TanStack Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<SidebarLayout />}>
            {/* Overview */}
            <Route index element={<Dashboard />} />

            {/* Chat & AI Domain */}
            <Route path="chat" element={<Chat />} />
            <Route path="search" element={<Search />} />
            <Route path="memory" element={<Memory />} />
            <Route path="sessions" element={<Sessions />} />

            {/* Administration Domain */}
            <Route path="tenants" element={<Tenants />} />
            <Route path="users" element={<Users />} />
            <Route path="api-keys" element={<APIKeys />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          className: 'font-sans',
        }}
      />
    </QueryClientProvider>
  )
}

export default App
