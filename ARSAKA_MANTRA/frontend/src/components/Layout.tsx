import { useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'

const mainNavigation = [
  { name: 'Dashboard', href: '/' },
  { name: 'Matrix', href: '/matrix' },
  { name: 'Decisions', href: '/decisions' },
  { name: 'Validator', href: '/validate' },
]

// Projection views per MANTRA-L1-PROJECTION-CATALOG-001
const projectionNavigation = [
  { name: 'Timeline', href: '/timeline', description: 'Evolution chains' },
  { name: 'Scope', href: '/scope', description: 'FE/BE/Infra impact' },
  { name: 'Relationships', href: '/relationships', description: 'Cross-references' },
  { name: 'Changes', href: '/changes', description: 'Change summary' },
]

export default function Layout() {
  const location = useLocation()
  const [showProjections, setShowProjections] = useState(false)

  const isProjectionActive = projectionNavigation.some(p => location.pathname === p.href)

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-3">
                <span className="text-2xl font-bold text-mantra-500">ATLAS</span>
                <span className="text-xl text-gray-400">MANTRA</span>
              </Link>
            </div>
            <nav className="flex items-center space-x-4">
              {mainNavigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    location.pathname === item.href
                      ? 'bg-mantra-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  )}
                >
                  {item.name}
                </Link>
              ))}

              {/* Projections Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowProjections(!showProjections)}
                  onBlur={() => setTimeout(() => setShowProjections(false), 150)}
                  className={clsx(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1',
                    isProjectionActive
                      ? 'bg-mantra-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  )}
                >
                  Projections
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showProjections && (
                  <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-md shadow-lg border border-gray-700 z-50">
                    {projectionNavigation.map((item) => (
                      <Link
                        key={item.name}
                        to={item.href}
                        className={clsx(
                          'block px-4 py-2 text-sm transition-colors',
                          location.pathname === item.href
                            ? 'bg-mantra-600 text-white'
                            : 'text-gray-300 hover:bg-gray-700'
                        )}
                        onClick={() => setShowProjections(false)}
                      >
                        <div>{item.name}</div>
                        <div className="text-xs text-gray-500">{item.description}</div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>ARSAKA_MANTRA - Decision Matrix Constitutional Law System</span>
            <span>AI Authority = ZERO | Per MANTRA-LAW-001</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
