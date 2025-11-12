/**
 * Routes Configuration
 *
 * LAYER 1: PRESENTATION
 * Main application routing with code splitting
 */

import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import DashboardLayout from '@/shared/components/layout/DashboardLayout';

// Loading component
const PageLoader = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

// Lazy load pages for code splitting
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const SelectOrganizationPage = lazy(() => import('@/pages/SelectOrganizationPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const AuditLogsPage = lazy(() => import('@/pages/AuditLogsPage'));
const TagsPage = lazy(() => import('@/pages/TagsPage'));
const ContentPage = lazy(() => import('@/pages/ContentPage'));
const PlaylistsPage = lazy(() => import('@/pages/PlaylistsPage'));
const DevicesPage = lazy(() => import('@/pages/DevicesPage'));
const DeviceGroupsPage = lazy(() => import('@/pages/DeviceGroupsPage'));
const DevicePreviewPage = lazy(() => import('@/pages/DevicePreviewPage'));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const WidgetsPage = lazy(() => import('@/features/widgets/pages/WidgetsPage'));
const TemplatesPage = lazy(() => import('@/features/templates/pages/TemplatesPage'));
const TranslationsPage = lazy(() => import('@/features/translations/pages/TranslationsPage'));
const SchedulesPage = lazy(() => import('@/features/schedules/pages/SchedulesPage'));
const RolesPage = lazy(() => import('@/pages/RolesPage'));
const SessionsPage = lazy(() => import('@/pages/SessionsPage'));
const PMSConfigPage = lazy(() => import('@/features/pms/pages/PMSConfigPage'));
const WeatherConfigPage = lazy(() => import('@/features/weather/pages/WeatherConfigPage'));

// Wrapper for lazy loaded components
const LazyPage = ({ component: Component }: { component: React.LazyExoticComponent<() => JSX.Element> }) => (
  <Suspense fallback={<PageLoader />}>
    <Component />
  </Suspense>
);

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/login',
    element: <LazyPage component={LoginPage} />,
  },
  {
    path: '/register',
    element: <LazyPage component={RegisterPage} />,
  },
  {
    path: '/forgot-password',
    element: <LazyPage component={ForgotPasswordPage} />,
  },
  {
    path: '/reset-password',
    element: <LazyPage component={ResetPasswordPage} />,
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
        element: <LazyPage component={DashboardPage} />,
      },
      {
        path: 'select-organization',
        element: <LazyPage component={SelectOrganizationPage} />,
      },
      // Settings (Organizations & Users)
      {
        path: 'settings',
        element: <LazyPage component={SettingsPage} />,
      },
      // Device Management
      {
        path: 'devices',
        element: <LazyPage component={DevicesPage} />,
      },
      {
        path: 'device-groups',
        element: <LazyPage component={DeviceGroupsPage} />,
      },
      {
        path: 'devices/:id/preview',
        element: <LazyPage component={DevicePreviewPage} />,
      },
      // Content Management
      {
        path: 'contents',
        element: <LazyPage component={ContentPage} />,
      },
      {
        path: 'playlists',
        element: <LazyPage component={PlaylistsPage} />,
      },
      {
        path: 'tags',
        element: <LazyPage component={TagsPage} />,
      },
      // Schedules
      {
        path: 'schedules',
        element: <LazyPage component={SchedulesPage} />,
      },
      // Analytics & Audit
      {
        path: 'analytics',
        element: <LazyPage component={AnalyticsPage} />,
      },
      {
        path: 'audit-logs',
        element: <LazyPage component={AuditLogsPage} />,
      },
      // User Management
      {
        path: 'roles',
        element: <LazyPage component={RolesPage} />,
      },
      {
        path: 'sessions',
        element: <LazyPage component={SessionsPage} />,
      },
      // Customization
      {
        path: 'widgets',
        element: <LazyPage component={WidgetsPage} />,
      },
      {
        path: 'templates',
        element: <LazyPage component={TemplatesPage} />,
      },
      {
        path: 'translations',
        element: <LazyPage component={TranslationsPage} />,
      },
      // Integrations
      {
        path: 'integrations/pms',
        element: <LazyPage component={PMSConfigPage} />,
      },
      {
        path: 'integrations/weather',
        element: <LazyPage component={WeatherConfigPage} />,
      },
    ],
  },
]);
