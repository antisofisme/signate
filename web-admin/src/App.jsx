import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'

// Pages (will be created next)
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import DevicePreview from './pages/DevicePreview'
import Contents from './pages/Contents'
import Tags from './pages/Tags'
import Playlists from './pages/Playlists'
import Activities from './pages/Activities'
import Widgets from './pages/Widgets'
import Settings from './pages/Settings'
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
    <ThemeProvider>
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

            <Route path="/devices/:id/preview" element={
              <PrivateRoute>
                <DevicePreview />
              </PrivateRoute>
            } />

            <Route path="/contents" element={
              <PrivateRoute>
                <Layout setIsAuthenticated={setIsAuthenticated}>
                  <Contents />
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

            <Route path="/activities" element={
              <PrivateRoute>
                <Layout setIsAuthenticated={setIsAuthenticated}>
                  <Activities />
                </Layout>
              </PrivateRoute>
            } />

            <Route path="/widgets" element={
              <PrivateRoute>
                <Layout setIsAuthenticated={setIsAuthenticated}>
                  <Widgets />
                </Layout>
              </PrivateRoute>
            } />

            <Route path="/settings" element={
              <PrivateRoute>
                <Layout setIsAuthenticated={setIsAuthenticated}>
                  <Settings />
                </Layout>
              </PrivateRoute>
            } />
          </Routes>
        </Router>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
