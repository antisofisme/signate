/**
 * Sidebar Layout - ARSAKA_TUTUR
 * Domain-based navigation matching MANTRA/PUGUH style
 * Light theme with colored domain headers
 */

import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { clsx } from 'clsx'
import {
  MessageSquare,
  Users,
  Building2,
  Key,
  Search,
  Brain,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  History,
  Shield,
  Database,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

// Domain definitions
type Domain = 'chat' | 'admin'

interface DomainConfig {
  label: string
  description: string
  color: {
    text: string
    bg: string
    bgHover: string
    bgActive: string
  }
  icon: typeof MessageSquare
}

const DOMAINS: Record<Domain, DomainConfig> = {
  chat: {
    label: 'Chat & AI',
    description: 'RAG Chat System',
    color: {
      text: 'text-blue-600',
      bg: 'bg-blue-600',
      bgHover: 'hover:bg-blue-50',
      bgActive: 'bg-blue-600',
    },
    icon: MessageSquare,
  },
  admin: {
    label: 'Administration',
    description: 'System Management',
    color: {
      text: 'text-emerald-600',
      bg: 'bg-emerald-600',
      bgHover: 'hover:bg-emerald-50',
      bgActive: 'bg-emerald-600',
    },
    icon: Shield,
  },
}

// Navigation items grouped by domain
const NAVIGATION = {
  overview: [
    { name: 'Dashboard', href: '/', icon: BarChart3, description: 'Overview' },
  ],
  chat: [
    { name: 'Chat', href: '/chat', icon: MessageSquare, description: 'RAG Chat' },
    { name: 'Search', href: '/search', icon: Search, description: 'Semantic Search' },
    { name: 'Memory', href: '/memory', icon: Brain, description: 'User Facts' },
    { name: 'Sessions', href: '/sessions', icon: History, description: 'Chat History' },
  ],
  admin: [
    { name: 'Tenants', href: '/tenants', icon: Building2, description: 'Organizations' },
    { name: 'Users', href: '/users', icon: Users, description: 'User Management' },
    { name: 'API Keys', href: '/api-keys', icon: Key, description: 'Access Tokens' },
    { name: 'Settings', href: '/settings', icon: Settings, description: 'Configuration' },
  ],
}

// Determine current domain from path
function getDomainFromPath(pathname: string): Domain | null {
  const chatPaths = ['/chat', '/search', '/memory', '/sessions']
  const adminPaths = ['/tenants', '/users', '/api-keys', '/settings']

  if (chatPaths.some(p => pathname.startsWith(p))) return 'chat'
  if (adminPaths.some(p => pathname.startsWith(p))) return 'admin'
  return null
}

export function SidebarLayout() {
  const location = useLocation()
  const currentDomain = getDomainFromPath(location.pathname)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { logout, user } = useAuthStore()

  const domainConfig = currentDomain ? DOMAINS[currentDomain] : null
  const headerBg = domainConfig?.color.bg || 'bg-indigo-600'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Header */}
      <header className={clsx(
        'sticky top-0 z-40 border-b transition-colors duration-300',
        headerBg
      )}>
        <div className="flex h-14 items-center px-4 gap-4">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden text-white p-2 hover:bg-white/10 rounded"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-2 text-white">
            <MessageSquare className="h-6 w-6" />
            <span className="font-bold text-lg">ARSAKA_TUTUR</span>
            <span className="text-white/70 text-sm hidden sm:inline">|</span>
            <span className="text-white/70 text-sm hidden sm:inline">RAG Memory System</span>
          </div>

          {/* Current Domain Badge */}
          {domainConfig && (
            <div className="ml-auto flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-white">
              <domainConfig.icon className="h-4 w-4" />
              <span className="font-medium text-sm">{domainConfig.label}</span>
            </div>
          )}
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={clsx(
          'fixed inset-y-0 left-0 z-30 w-64 transform bg-white border-r transition-transform',
          'pt-14 lg:pt-0',
          'lg:sticky lg:top-14 lg:h-[calc(100vh-3.5rem)] lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}>
          <div className="flex flex-col h-full">
            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
              {/* Dashboard */}
              {NAVIGATION.overview.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  end
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mb-4',
                    isActive
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <div className="flex flex-col">
                    <span>{item.name}</span>
                    <span className="text-xs opacity-70">{item.description}</span>
                  </div>
                </NavLink>
              ))}

              {/* Chat & AI Section */}
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                Chat & AI
              </div>

              {NAVIGATION.chat.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? clsx(DOMAINS.chat.color.bgActive, 'text-white')
                      : clsx('text-gray-600', DOMAINS.chat.color.bgHover)
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <div className="flex flex-col">
                    <span>{item.name}</span>
                    <span className="text-xs opacity-70">{item.description}</span>
                  </div>
                </NavLink>
              ))}

              {/* Administration Section */}
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-6 mb-3 px-3">
                Administration
              </div>

              {NAVIGATION.admin.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? clsx(DOMAINS.admin.color.bgActive, 'text-white')
                      : clsx('text-gray-600', DOMAINS.admin.color.bgHover)
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <div className="flex flex-col">
                    <span>{item.name}</span>
                    <span className="text-xs opacity-70">{item.description}</span>
                  </div>
                </NavLink>
              ))}
            </nav>

            {/* User Info & Logout */}
            <div className="border-t p-4 bg-gray-50">
              {user && (
                <div className="mb-3 px-3">
                  <p className="text-sm font-medium text-gray-900">{user.display_name}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              )}
              <button
                onClick={logout}
                className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-5 w-5" />
                Logout
              </button>
            </div>

            {/* System Info */}
            <div className="p-3 border-t bg-blue-50">
              <div className="text-xs text-blue-800">
                <div className="flex items-center gap-2 mb-1">
                  <Database className="h-4 w-4" />
                  <span className="font-bold">4-Layer Memory</span>
                </div>
                <p className="opacity-70">Working | Episodic | Semantic | Temporal</p>
              </div>
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
        <main className="flex-1 p-6 lg:p-8 min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
