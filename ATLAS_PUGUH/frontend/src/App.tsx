/**
 * ATLAS_PUGUH Frontend - SaaS Platform
 * 5-Domain CMS Architecture with Auth
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Layout
import { DomainLayout } from '@/components/layout/DomainLayout'

// Auth Guards
import { AuthGuard, GuestGuard } from '@/components/auth'

// Public Pages
import { Landing } from '@/pages/public'

// Auth Pages
import {
  Login,
  Register,
  ForgotPassword,
  ResetPassword,
  VerifyEmail,
} from '@/pages/auth'

// IAM Domain
import {
  UserList,
  UserDetail,
  RoleList,
  RoleDetail,
  ServiceAccounts,
  PermissionMatrix,
} from '@/domains/iam/pages'

// Tenant Domain
import {
  TenantList,
  TenantDetail,
  TenantMembers,
  IsolationCheck,
} from '@/domains/tenant/pages'

// Decision Domain
import {
  RuleList,
  RuleDetail,
  CreateRuleDraft,
  RuleVersions,
  RequestActivation,
  DecisionTypes,
  DecisionHistory,
  DecisionDetail,
} from '@/domains/decision/pages'

// Workflow Domain
import {
  MyPending,
  AllWorkflows,
  WorkflowDetail,
  WorkflowApprove,
  WorkflowReject,
  Escalations,
} from '@/domains/workflow/pages'

// Control Domain
import {
  AuditTrail,
  AuditDetail,
  EventTimeline,
  EventDetail,
  DLQView,
  MetricsDashboard,
} from '@/domains/control/pages'

// Dashboard
import { Dashboard } from '@/pages/Dashboard'

// Billing Pages
import { PricingPage, BillingSettingsPage, InvoicesPage } from '@/pages/billing'

// Project Feature
import { ProjectListPage, ProjectSettingsPage } from '@/features/project'

// Create QueryClient for TanStack Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* ============================================ */}
          {/* PUBLIC ROUTES */}
          {/* ============================================ */}

          {/* Landing Page - Public */}
          <Route path="/" element={<Landing />} />

          {/* Pricing Page - Public */}
          <Route path="/pricing" element={<PricingPage />} />

          {/* Auth Routes - Guest Only (redirect if already logged in) */}
          <Route
            path="/login"
            element={
              <GuestGuard>
                <Login />
              </GuestGuard>
            }
          />
          <Route
            path="/register"
            element={
              <GuestGuard>
                <Register />
              </GuestGuard>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <GuestGuard>
                <ForgotPassword />
              </GuestGuard>
            }
          />
          <Route
            path="/reset-password"
            element={
              <GuestGuard>
                <ResetPassword />
              </GuestGuard>
            }
          />
          <Route path="/verify-email" element={<VerifyEmail />} />

          {/* ============================================ */}
          {/* PROTECTED ROUTES - Require Authentication */}
          {/* ============================================ */}
          <Route
            path="/app/*"
            element={
              <AuthGuard>
                <DomainLayout />
              </AuthGuard>
            }
          >
            {/* Dashboard - Home Page */}
            <Route index element={<Dashboard />} />

            {/* ============================================ */}
            {/* IAM Domain - READ-ONLY */}
            {/* ============================================ */}
            <Route path="iam" element={<Navigate to="/app/iam/users" replace />} />
            <Route path="iam/users" element={<UserList />} />
            <Route path="iam/users/:id" element={<UserDetail />} />
            <Route path="iam/roles" element={<RoleList />} />
            <Route path="iam/roles/:id" element={<RoleDetail />} />
            <Route path="iam/service-accounts" element={<ServiceAccounts />} />
            <Route path="iam/permissions" element={<PermissionMatrix />} />

            {/* ============================================ */}
            {/* Tenant Domain - READ-ONLY */}
            {/* ============================================ */}
            <Route path="tenant" element={<Navigate to="/app/tenant/list" replace />} />
            <Route path="tenant/list" element={<TenantList />} />
            <Route path="tenant/:id" element={<TenantDetail />} />
            <Route path="tenant/:id/members" element={<TenantMembers />} />
            <Route path="tenant/isolation-check" element={<IsolationCheck />} />

            {/* ============================================ */}
            {/* Decision Domain - 2 MUTATIONS */}
            {/* ============================================ */}
            <Route path="decision" element={<Navigate to="/app/decision/rules" replace />} />
            <Route path="decision/rules" element={<RuleList />} />
            <Route path="decision/rules/new" element={<CreateRuleDraft />} />
            <Route path="decision/rules/:id" element={<RuleDetail />} />
            <Route path="decision/rules/:id/versions" element={<RuleVersions />} />
            <Route path="decision/rules/:id/activate" element={<RequestActivation />} />
            <Route path="decision/types" element={<DecisionTypes />} />
            <Route path="decision/history" element={<DecisionHistory />} />
            <Route path="decision/history/:id" element={<DecisionDetail />} />

            {/* ============================================ */}
            {/* Workflow Domain - 4 MUTATIONS */}
            {/* ============================================ */}
            <Route path="workflow" element={<Navigate to="/app/workflow/pending" replace />} />
            <Route path="workflow/pending" element={<MyPending />} />
            <Route path="workflow/all" element={<AllWorkflows />} />
            <Route path="workflow/escalations" element={<Escalations />} />
            <Route path="workflow/:id" element={<WorkflowDetail />} />
            <Route path="workflow/:id/approve" element={<WorkflowApprove />} />
            <Route path="workflow/:id/reject" element={<WorkflowReject />} />

            {/* ============================================ */}
            {/* Control Domain - READ-ONLY */}
            {/* ============================================ */}
            <Route path="control" element={<Navigate to="/app/control/audit" replace />} />
            <Route path="control/audit" element={<AuditTrail />} />
            <Route path="control/audit/:id" element={<AuditDetail />} />
            <Route path="control/events" element={<EventTimeline />} />
            <Route path="control/events/:id" element={<EventDetail />} />
            <Route path="control/dlq" element={<DLQView />} />
            <Route path="control/metrics" element={<MetricsDashboard />} />

            {/* ============================================ */}
            {/* Billing Routes */}
            {/* ============================================ */}
            <Route path="billing" element={<BillingSettingsPage />} />
            <Route path="billing/pricing" element={<PricingPage />} />
            <Route path="billing/invoices" element={<InvoicesPage />} />

            {/* ============================================ */}
            {/* Project Routes */}
            {/* ============================================ */}
            <Route path=":tenantSlug/projects" element={<ProjectListPage />} />
            <Route path=":tenantSlug/:projectSlug/settings" element={<ProjectSettingsPage />} />
            <Route path=":tenantSlug/:projectSlug/dashboard" element={<Dashboard />} />

            {/* Project-scoped Domain Routes (future) */}
            {/* These routes include project context for resource isolation */}
            <Route path=":tenantSlug/:projectSlug/decision/*" element={<Navigate to="/app/decision" replace />} />
            <Route path=":tenantSlug/:projectSlug/workflow/*" element={<Navigate to="/app/workflow" replace />} />
          </Route>

          {/* ============================================ */}
          {/* LEGACY REDIRECTS (for old URLs) */}
          {/* ============================================ */}
          <Route path="/iam/*" element={<Navigate to="/app/iam" replace />} />
          <Route path="/tenant/*" element={<Navigate to="/app/tenant" replace />} />
          <Route path="/decision/*" element={<Navigate to="/app/decision" replace />} />
          <Route path="/workflow/*" element={<Navigate to="/app/workflow" replace />} />
          <Route path="/control/*" element={<Navigate to="/app/control" replace />} />

          {/* 404 */}
          <Route
            path="*"
            element={
              <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                  <h1 className="text-4xl font-bold mb-4">404</h1>
                  <p className="text-muted-foreground mb-4">Page not found</p>
                  <a href="/" className="text-amber-600 hover:underline">
                    Go to Home
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
