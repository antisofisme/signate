import { Link, useLocation } from 'react-router-dom'
import { Monitor, FileImage, LayoutDashboard, LogOut, Tag, ListVideo, Puzzle, Settings, Menu, X } from 'lucide-react'
import { useState } from 'react'

export default function Layout({ children, setIsAuthenticated }) {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

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
    <div className="min-h-screen bg-gray-100">
      {/* Mobile Burger Menu Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-[60] lg:hidden p-2 bg-blue-600 text-white rounded-lg shadow-lg"
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
      <div className={`fixed inset-y-0 left-0 w-64 bg-white shadow-xl border-r border-gray-400 z-50 transform transition-transform duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 bg-blue-600">
            <h1 className="text-xl font-bold text-white">Signage Admin</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              )
            })}
          </nav>

          {/* Logout */}
          <div className="p-4 border-t">
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-3 text-gray-700 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors"
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
