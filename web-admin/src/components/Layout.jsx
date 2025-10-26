import { Link, useLocation } from 'react-router-dom'
import { Monitor, FileImage, LayoutDashboard, LogOut, Tag, ListVideo, Puzzle, Settings, Menu, X, Sun, Moon } from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { devicesAPI } from '../services/api'
import { useTheme } from '../contexts/ThemeContext'

export default function Layout({ children, setIsAuthenticated }) {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { theme, toggleTheme, isDark } = useTheme()

  // FASE 2.2: Fetch devices to count pending approvals (optimized for lower memory usage)
  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchInterval: 60000, // Refresh every 60 seconds (reduced from 10s)
  })

  const pendingCount = devices?.devices?.filter(d => d.status === 'pending').length || 0

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
  }

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Devices', href: '/devices', icon: Monitor },
    { name: 'Content', href: '/content', icon: FileImage },
    { name: 'Playlists', href: '/playlists', icon: ListVideo },
    { name: 'Tags', href: '/tags', icon: Tag },
    { name: 'Widgets', href: '/widgets', icon: Puzzle },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
      {/* Mobile Burger Menu Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-[60] lg:hidden p-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg shadow-lg"
        aria-label="Toggle menu"
      >
        {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 shadow-xl border-r border-gray-400 dark:border-gray-700 z-50 transform transition-transform duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 bg-blue-600 dark:bg-blue-700">
            "<h1 className="text-xl font-bold text-white">Signage Admin</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              const showBadge = item.name === 'Devices' && pendingCount > 0

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center">
                    <Icon className="w-5 h-5 mr-3" />
                    <span className="font-medium">{item.name}</span>
                  </div>
                  {/* FASE 2.2: Notification badge for pending devices */}
                  {showBadge && (
                    <span className="ml-auto bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5 animate-pulse">
                      {pendingCount}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Theme Toggle & Logout */}
          <div className="p-4 border-t dark:border-gray-700 space-y-2">
            {/* FASE 9.2: Dark Mode Toggle */}
            <button
              onClick={toggleTheme}
              className="flex items-center w-full px-4 py-3 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle theme"
            >
              {isDark ? (
                <>
                  <Sun className="w-5 h-5 mr-3" />
                  <span className="font-medium">Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-5 h-5 mr-3" />
                  <span className="font-medium">Dark Mode</span>
                </>
              )}
            </button>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-3 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors"
            >
              <LogOut className="w-5 h-5 mr-3" />
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:ml-64">
        <main>
          {children}
        </main>
      </div>
    </div>
  )
}
