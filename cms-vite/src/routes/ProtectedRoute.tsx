/**
 * Protected Route Component
 *
 * LAYER 1: PRESENTATION
 * Guards routes that require authentication
 */

import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/lib/stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
