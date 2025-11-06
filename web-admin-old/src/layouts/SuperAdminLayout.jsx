import { useState } from 'react'
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Building2,
  Users,
  TrendingUp,
  Settings,
  Menu,
  X,
  LogOut,
  ChevronRight,
  Shield
} from 'lucide-react'

/**
 * SuperAdminLayout Component
 * Layout for Super Admin with top navbar and sidebar
 *
 * Features:
 * - Top navbar with breadcrumb and user menu
 * - Collapsible sidebar with super admin menu
 * - Responsive design
 * - Dark mode support
 * - Role badge indicator
 */
export default function SuperAdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const menuItems = [
    {
      path: '/super/dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Global overview and statistics'
    },
    {
      path: '/super/tenants',
      label: 'Organizations',
      icon: Building2,
      description: 'Manage tenant organizations'
    },
    {
      path: '/super/users',
      label: 'Users',
      icon: Users,
      description: 'Manage all users'
    },
    {
      path: '/super/analytics',
      label: 'Analytics',
      icon: TrendingUp,
      description: 'Global analytics and insights'
    },
    {
      path: '/super/system',
      label: 'System',
      icon: Settings,
      description: 'System settings and maintenance'
    }
  ]

  const handleLogout = () => {
    // TODO: Implement logout
    localStorage.removeItem('token')
    navigate('/login')
  }

  // Get breadcrumb from current path
  const getBreadcrumb = () => {
    const path = location.pathname
    if (path === '/super/dashboard') return 'Dashboard'
    if (path.startsWith('/super/tenants')) return 'Organizations'
    if (path.startsWith('/super/users')) return 'Users'
    if (path.startsWith('/super/analytics')) return 'Analytics'
    if (path.startsWith('/super/system')) return 'System'
    return 'Super Admin'
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      {/* Top Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Logo + Menu Toggle */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                {sidebarOpen ? (
                  <X className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                ) : (
                  <Menu className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                )}
              </button>

              <Link to="/super/dashboard" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                    Super Admin
                  </h1>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Control Panel
                  </p>
                </div>
              </Link>
            </div>

            {/* Center: Breadcrumb */}
            <div className="hidden md:flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Link to="/super/dashboard" className="hover:text-gray-900 dark:hover:text-gray-100">
                Super Admin
              </Link>
              <ChevronRight className="w-4 h-4" />
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {getBreadcrumb()}
              </span>
            </div>

            {/* Right: User Menu */}
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                <Shield className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
                  Super Admin
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Sidebar */}
      <aside
        className={`
          fixed top-16 left-0 bottom-0 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 z-40 transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-start gap-3 px-4 py-3 rounded-lg transition-all group
                  ${isActive
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`} />
                <div className="flex-1 min-w-0">
                  <p className={`font-medium ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-gray-100'}`}>
                    {item.label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">
                    {item.description}
                  </p>
                </div>
              </Link>
            )
          })}
        </nav>

        {/* Bottom Section - System Info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <span className="text-xs font-semibold text-purple-900 dark:text-purple-300">
                System Status
              </span>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-400">Status</span>
                <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                  Online
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-400">Version</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">v2.0.0</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
        />
      )}

      {/* Main Content */}
      <main className="lg:ml-64 pt-16 min-h-screen">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
