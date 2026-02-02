/**
 * Domain Layout - Phase 4 + Phase 6 Help Integration
 * Main layout with 5-domain navigation and help system
 */

import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import {
  Users,
  Building2,
  Scale,
  CheckCircle,
  BarChart3,
  Menu,
  X,
  LayoutDashboard,
  LogOut,
  User,
  HelpCircle,
  CreditCard,
  FolderKanban,
  Settings,
  Shield,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useTenantStore } from '@/stores/tenantStore'
import { useHelpStore } from '@/stores/helpStore'
import { useLogout } from '@/features/auth/hooks'
import { Button } from '@/components/ui/button'
import { TenantSelector } from '@/components/TenantSelector'
import { Badge } from '@/components/ui/badge'
import { HelpSidebar, GuidedTour } from '@/components/help'

interface DomainConfig {
  name: string
  path: string
  icon: React.ElementType
  color: string
  bgColor: string
  description: string
}

const domains: DomainConfig[] = [
  {
    name: 'IAM',
    path: '/app/iam',
    icon: Users,
    color: 'text-iam',
    bgColor: 'bg-iam',
    description: 'Identity & Access',
  },
  {
    name: 'Tenant',
    path: '/app/tenant',
    icon: Building2,
    color: 'text-tenant',
    bgColor: 'bg-tenant',
    description: 'Tenant Isolation',
  },
  {
    name: 'Decision',
    path: '/app/decision',
    icon: Scale,
    color: 'text-decision',
    bgColor: 'bg-decision',
    description: 'Rules & Policy',
  },
  {
    name: 'Workflow',
    path: '/app/workflow',
    icon: CheckCircle,
    color: 'text-workflow',
    bgColor: 'bg-workflow',
    description: 'Approvals',
  },
  {
    name: 'Control',
    path: '/app/control',
    icon: BarChart3,
    color: 'text-control',
    bgColor: 'bg-control',
    description: 'Audit & Metrics',
  },
]

function getDomainFromPath(pathname: string): DomainConfig | undefined {
  return domains.find(d => pathname.startsWith(d.path))
}

export function DomainLayout() {
  const location = useLocation()
  const currentDomain = getDomainFromPath(location.pathname)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user } = useAuthStore()
  const { currentTenant } = useTenantStore()
  const { setCurrentPage, setOpen: setHelpOpen, hasSeenWelcome, setActiveTour, markWelcomeSeen } = useHelpStore()
  const logoutMutation = useLogout()

  // Track current page for contextual help
  useEffect(() => {
    setCurrentPage(location.pathname)
  }, [location.pathname, setCurrentPage])

  // Show welcome tour for first-time users on dashboard
  useEffect(() => {
    if (!hasSeenWelcome && location.pathname === '/app') {
      // Delay to allow page to render
      const timer = setTimeout(() => {
        setActiveTour('dashboard-intro')
        markWelcomeSeen()
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [hasSeenWelcome, location.pathname, setActiveTour, markWelcomeSeen])

  return (
    <div className="min-h-screen bg-background">
      {/* Top Header */}
      <header className={cn(
        "sticky top-0 z-40 border-b transition-colors",
        currentDomain ? currentDomain.bgColor : "bg-primary"
      )}>
        <div className="flex h-14 items-center px-4 gap-4">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden text-white p-2 hover:bg-white/10 rounded"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-2 text-white">
            <span className="font-bold text-lg">ARSAKA_PUGUH</span>
            <span className="text-white/70 text-sm hidden sm:inline">SaaS</span>
          </div>

          {/* Tenant Selector */}
          <div className="hidden md:block" data-tour="tenant-selector">
            <TenantSelector className="bg-white/10 border-white/20 text-white hover:bg-white/20" />
          </div>

          {/* Current Tenant Badge (mobile) */}
          {currentTenant && (
            <Badge variant="outline" className="md:hidden text-white border-white/50 text-xs">
              {currentTenant.name}
            </Badge>
          )}

          {/* Current Domain Badge */}
          {currentDomain && (
            <div className="flex items-center gap-2 text-white">
              <currentDomain.icon size={18} />
              <span className="font-medium">{currentDomain.name}</span>
              <span className="text-white/70 text-sm hidden md:inline">
                {currentDomain.description}
              </span>
            </div>
          )}

          {/* User Info & Logout */}
          <div className="ml-auto flex items-center gap-3">
            {user && (
              <div className="hidden sm:flex items-center gap-2 text-white/80 text-sm">
                <User size={16} />
                <span>{user.name || user.email}</span>
              </div>
            )}
            {/* Help Button */}
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/10"
              onClick={() => setHelpOpen(true)}
              data-tour="help-button"
            >
              <HelpCircle size={16} className="mr-2" />
              <span className="hidden sm:inline">Help</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/10"
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
            >
              <LogOut size={16} className="mr-2" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside
          data-tour="sidebar"
          className={cn(
            "fixed inset-y-0 left-0 z-30 w-64 transform bg-card border-r pt-14 transition-transform lg:translate-x-0 lg:static lg:pt-0",
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <nav className="p-4 space-y-1">
            {/* Mobile Tenant Selector */}
            <div className="md:hidden mb-4">
              <TenantSelector className="w-full" />
            </div>

            {/* Dashboard Link */}
            <NavLink
              to="/app"
              end
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mb-4",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <LayoutDashboard size={18} />
              <div className="flex flex-col">
                <span>Dashboard</span>
                <span className="text-xs opacity-70">Overview</span>
              </div>
            </NavLink>

            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4 px-3">
              Domains
            </div>
            {domains.map((domain) => (
              <NavLink
                key={domain.path}
                to={domain.path}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? cn(domain.bgColor, "text-white")
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <domain.icon size={18} />
                <div className="flex flex-col">
                  <span>{domain.name}</span>
                  <span className="text-xs opacity-70">{domain.description}</span>
                </div>
              </NavLink>
            ))}

            {/* SaaS & Settings Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-6 mb-4 px-3">
              SaaS & Settings
            </div>

            <NavLink
              to="/app/projects"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <FolderKanban size={18} />
              <div className="flex flex-col">
                <span>Projects</span>
                <span className="text-xs opacity-70">Manage Projects</span>
              </div>
            </NavLink>

            <NavLink
              to="/app/billing"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-emerald-600 text-white"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <CreditCard size={18} />
              <div className="flex flex-col">
                <span>Billing</span>
                <span className="text-xs opacity-70">Subscription & Invoices</span>
              </div>
            </NavLink>

            <NavLink
              to="/app/account/security"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Shield size={18} />
              <div className="flex flex-col">
                <span>Security</span>
                <span className="text-xs opacity-70">API Keys & Sessions</span>
              </div>
            </NavLink>

            <NavLink
              to="/app/settings"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Settings size={18} />
              <div className="flex flex-col">
                <span>Settings</span>
                <span className="text-xs opacity-70">Account Settings</span>
              </div>
            </NavLink>
          </nav>

          {/* Tenant Info */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-muted">
            <div className="text-xs text-muted-foreground">
              {currentTenant ? (
                <>
                  <strong>{currentTenant.name}</strong>
                  <p className="mt-1">
                    Plan: <Badge variant="outline" className="text-[10px]">{currentTenant.plan}</Badge>
                    {' | '}Role: <Badge variant="outline" className="text-[10px]">{currentTenant.role}</Badge>
                  </p>
                </>
              ) : (
                <p>Select a tenant to get started</p>
              )}
            </div>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      {/* Help System Components */}
      <HelpSidebar />
      <GuidedTour />

      {/* Floating Help Button (mobile) */}
      <Button
        variant="default"
        size="icon"
        className="fixed bottom-4 right-4 rounded-full shadow-lg lg:hidden z-50 bg-amber-500 hover:bg-amber-600"
        onClick={() => setHelpOpen(true)}
        data-tour="help-button-mobile"
      >
        <HelpCircle className="h-5 w-5" />
      </Button>
    </div>
  )
}
