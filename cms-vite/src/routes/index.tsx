/**
 * Routes Configuration
 *
 * LAYER 1: PRESENTATION
 * Main application routing
 */

import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import DashboardLayout from '@/shared/components/layout/DashboardLayout';

// Pages
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';
import SelectOrganizationPage from '@/pages/SelectOrganizationPage';
import SettingsPage from '@/pages/SettingsPage';
// import DevicesPage from '@/pages/DevicesPage'; // TODO: Create DevicesPage

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },

  // Protected Routes
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'select-organization',
        element: <SelectOrganizationPage />,
      },
      // Settings (Organizations & Users)
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      // Device Management
      {
        path: 'devices',
        element: <div className="p-8">Devices Page - Coming Soon</div>,
      },
      {
        path: 'contents',
        element: <div className="p-8">Contents Page - Coming Soon</div>,
      },
      {
        path: 'playlists',
        element: <div className="p-8">Playlists Page - Coming Soon</div>,
      },
      {
        path: 'tags',
        element: <div className="p-8">Tags Page - Coming Soon</div>,
      },
      {
        path: 'activities',
        element: <div className="p-8">Activity Logs - Coming Soon</div>,
      },
      {
        path: 'widgets',
        element: <div className="p-8">Widgets Page - Coming Soon</div>,
      },
    ],
  },

  // 404 Catch-all
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])
