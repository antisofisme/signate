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
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import DashboardPage from '@/pages/DashboardPage';
import SelectOrganizationPage from '@/pages/SelectOrganizationPage';
import SettingsPage from '@/pages/SettingsPage';
import AuditLogsPage from '@/pages/AuditLogsPage';
import TagsPage from '@/pages/TagsPage';
import ContentPage from '@/pages/ContentPage';
import PlaylistsPage from '@/pages/PlaylistsPage';
import DevicesPage from '@/pages/DevicesPage';
import DevicePreviewPage from '@/pages/DevicePreviewPage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';

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
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },
  {
    path: '/reset-password',
    element: <ResetPasswordPage />,
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
        element: <DevicesPage />,
      },
      {
        path: 'contents',
        element: <ContentPage />,
      },
      {
        path: 'playlists',
        element: <PlaylistsPage />,
      },
      {
        path: 'tags',
        element: <TagsPage />,
      },
      {
        path: 'audit-logs',
        element: <AuditLogsPage />,
      },
      {
        path: 'analytics',
        element: <AnalyticsPage />,
      },
      {
        path: 'widgets',
        element: <div className="p-8">Widgets Page - Coming Soon</div>,
      },
    ],
  },

  // Device Preview - Full Screen (Protected but no layout)
  {
    path: '/devices/:deviceId/preview',
    element: (
      <ProtectedRoute>
        <DevicePreviewPage />
      </ProtectedRoute>
    ),
  },

  // 404 Catch-all
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])
