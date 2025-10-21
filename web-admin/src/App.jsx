import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

// Pages (will be created next)
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import Content from './pages/Content'
import Layout from './components/Layout'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
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
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}

export default App
