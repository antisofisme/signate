/**
 * ARSAKA_PUGUH - Guest Guard Component
 *
 * Protects routes that should only be accessible to non-authenticated users.
 * Redirects to dashboard if already authenticated.
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface GuestGuardProps {
  children: React.ReactNode
}

export function GuestGuard({ children }: GuestGuardProps) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  // Get the intended destination from state, or default to app dashboard
  const from = (location.state as { from?: Location })?.from?.pathname || '/app'

  if (isAuthenticated) {
    // Redirect authenticated users to their intended destination or dashboard
    return <Navigate to={from} replace />
  }

  return <>{children}</>
}

export default GuestGuard
