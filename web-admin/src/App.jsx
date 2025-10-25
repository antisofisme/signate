import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

// Pages (will be created next)
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import Content from './pages/Content'
import Tags from './pages/Tags'
import Playlists from './pages/Playlists'
import Apps from './pages/Apps'
import Layout from './components/Layout'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache Settings - Prevent unnecessary refetching
      staleTime: 5 * 60 * 1000,        // Data stays fresh for 5 minutes
      cacheTime: 10 * 60 * 1000,       // Keep unused data in cache for 10 minutes
      refetchOnMount: false,            // Don't refetch on component mount if data is fresh
      refetchOnWindowFocus: false,      // Don't refetch on window focus
      retry: 1,                         // Retry failed requests once
    },
  },
})

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('token')
  )

  const PrivateRoute = ({ children }) => {
    return isAuthenticated ? children : <Navigate to="/login" />
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated} />} />

          <Route path="/" element={
            <PrivateRoute>
              <Layout setIsAuthenticated={setIsAuthenticated}>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          } />

          <Route path="/devices" element={
            <PrivateRoute>
              <Layout setIsAuthenticated={setIsAuthenticated}>
                <Devices />
              </Layout>
            </PrivateRoute>
          } />

          <Route path="/content" element={
            <PrivateRoute>
              <Layout setIsAuthenticated={setIsAuthenticated}>
                <Content />
              </Layout>
            </PrivateRoute>
          } />

          <Route path="/tags" element={
            <PrivateRoute>
              <Layout setIsAuthenticated={setIsAuthenticated}>
                <Tags />
              </Layout>
            </PrivateRoute>
          } />

          <Route path="/playlists" element={
            <PrivateRoute>
              <Layout setIsAuthenticated={setIsAuthenticated}>
                <Playlists />
              </Layout>
            </PrivateRoute>
          } />

          <Route path="/apps" element={
            <PrivateRoute>
              <Layout setIsAuthenticated={setIsAuthenticated}>
                <Apps />
              </Layout>
            </PrivateRoute>
          } />
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}

export default App
