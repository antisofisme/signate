/**
 * ATLAS_PANDAWA Frontend - Main App Component
 * Root application component
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@stores/authStore'
import LoginForm from '@features/auth/components/LoginForm'

// Create TanStack Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app">
          <header className="app-header">
            <h1>ATLAS_PANDAWA</h1>
            <p>Enterprise Hospitality Platform</p>
          </header>

          <main className="app-main">
            <Routes>
              <Route
                path="/login"
                element={isAuthenticated ? <Navigate to="/" replace /> : <LoginForm />}
              />

              <Route
                path="/"
                element={
                  isAuthenticated ? (
                    <Dashboard />
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />

              {/* Future module routes will be added here per phase */}
              {/* Phase 2: PMS routes */}
              {/* Phase 3: POS routes */}
              {/* Phase 4: Accounting routes */}
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

function Dashboard() {
  const user = useAuthStore((state) => state.user)
  const tenant = useAuthStore((state) => state.tenant)

  return (
    <div className="dashboard">
      <h2>Welcome, {user?.full_name || user?.username}!</h2>
      {tenant && <p>Organization: {tenant.name}</p>}

      <div className="modules">
        <p>Available Modules:</p>
        <ul>
          <li>PMS - Property Management System (Phase 2)</li>
          <li>POS - Point of Sale (Phase 3)</li>
          <li>Accounting (Phase 4)</li>
          <li>HRM - Human Resource Management (Phase 5)</li>
          <li>Inventory (Phase 6)</li>
        </ul>
      </div>
    </div>
  )
}

export default App
