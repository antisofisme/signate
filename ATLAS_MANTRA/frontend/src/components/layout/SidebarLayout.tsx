/**
 * Sidebar Layout - ATLAS_MANTRA
 * Domain-based navigation per Decision Groups
 * Light theme like PUGUH
 */

import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { clsx } from 'clsx'
import {
  GROUPS,
  GROUP_LABELS,
} from '../../shared/constants'
import { FloatingChat } from '../ai'

// Icons
const Icons = {
  Menu: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  X: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Dashboard: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
    </svg>
  ),
  Target: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" strokeWidth={2} />
      <circle cx="12" cy="12" r="6" strokeWidth={2} />
      <circle cx="12" cy="12" r="2" strokeWidth={2} />
    </svg>
  ),
  Layers: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  ),
  Shield: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  Refresh: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  Check: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  List: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  ),
  Grid: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  Timeline: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
    </svg>
  ),
  Link: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  ),
  Audit: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>
  ),
  Key: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
    </svg>
  ),
  AI: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  Stack: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  Scope: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  Changes: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
}

const GROUP_ICONS: Record<string, React.FC> = {
  'INT': Icons.Target,
  'ARCH': Icons.Layers,
  'CTL': Icons.Shield,
  'EVO': Icons.Refresh,
}

const GROUP_COLORS: Record<string, { text: string; bg: string; hover: string }> = {
  'INT': { text: 'text-blue-600', bg: 'bg-blue-600', hover: 'hover:bg-blue-50' },
  'ARCH': { text: 'text-green-600', bg: 'bg-green-600', hover: 'hover:bg-green-50' },
  'CTL': { text: 'text-orange-600', bg: 'bg-orange-600', hover: 'hover:bg-orange-50' },
  'EVO': { text: 'text-purple-600', bg: 'bg-purple-600', hover: 'hover:bg-purple-50' },
}

const GROUP_PATH_MAP: Record<string, string> = {
  'int': 'INT',
  'arch': 'ARCH',
  'ctl': 'CTL',
  'evo': 'EVO',
}

function getGroupFromPath(pathname: string): string | undefined {
  const match = pathname.match(/\/group\/([a-z]+)/i)
  return match ? GROUP_PATH_MAP[match[1].toLowerCase()] : undefined
}

export function SidebarLayout() {
  const location = useLocation()
  const currentGroup = getGroupFromPath(location.pathname)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const currentColors = currentGroup ? GROUP_COLORS[currentGroup] : null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Header */}
      <header className={clsx(
        "sticky top-0 z-40 border-b transition-colors",
        currentColors ? currentColors.bg : "bg-indigo-600"
      )}>
        <div className="flex h-14 items-center px-4 gap-4">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden text-white p-2 hover:bg-white/10 rounded"
          >
            {sidebarOpen ? <Icons.X /> : <Icons.Menu />}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-2 text-white">
            <span className="font-bold text-lg">ATLAS_MANTRA</span>
            <span className="text-white/70 text-sm hidden sm:inline">Decision Matrix</span>
          </div>

          {/* Current Group Badge */}
          {currentGroup && (
            <div className="ml-auto flex items-center gap-2 text-white">
              {GROUP_ICONS[currentGroup] && (
                <span>{GROUP_ICONS[currentGroup]({})}</span>
              )}
              <span className="font-medium">{GROUP_LABELS[currentGroup]}</span>
            </div>
          )}
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={clsx(
          "fixed inset-y-0 left-0 z-30 w-64 transform bg-white border-r transition-transform",
          "pt-14 lg:pt-0",
          "lg:sticky lg:top-14 lg:h-[calc(100vh-3.5rem)] lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}>
          <nav className="p-4 space-y-1 overflow-y-auto h-[calc(100%-4rem)] lg:h-[calc(100%-4rem)]">
            {/* Dashboard Link */}
            <NavLink
              to="/"
              end
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mb-4",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Dashboard />
              <div className="flex flex-col">
                <span>Dashboard</span>
                <span className="text-xs opacity-70">Overview</span>
              </div>
            </NavLink>

            {/* Decision Groups */}
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
              Decision Groups
            </div>

            {GROUPS.map((groupId) => {
              const Icon = GROUP_ICONS[groupId]
              const colors = GROUP_COLORS[groupId]
              return (
                <NavLink
                  key={groupId}
                  to={`/group/${groupId.toLowerCase()}`}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => clsx(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? clsx(colors.bg, "text-white")
                      : clsx("text-gray-600", colors.hover)
                  )}
                >
                  <Icon />
                  <div className="flex flex-col">
                    <span>{GROUP_LABELS[groupId]}</span>
                    <span className="text-xs opacity-70">{groupId}</span>
                  </div>
                </NavLink>
              )
            })}

            {/* Global Views */}
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-6 mb-3 px-3">
              Global Views
            </div>

            <NavLink
              to="/matrix"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Grid />
              <span>Matrix View</span>
            </NavLink>

            <NavLink
              to="/decisions"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.List />
              <span>All Decisions</span>
            </NavLink>

            {/* Projections */}
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-6 mb-3 px-3">
              Projections
            </div>

            <NavLink
              to="/timeline"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Timeline />
              <span>Timeline</span>
            </NavLink>

            <NavLink
              to="/relationships"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Link />
              <span>Relationships</span>
            </NavLink>

            <NavLink
              to="/scope"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Scope />
              <span>Scope</span>
            </NavLink>

            <NavLink
              to="/tech-stack"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Stack />
              <span>Tech Stack</span>
            </NavLink>

            <NavLink
              to="/changes"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Changes />
              <span>Changes</span>
            </NavLink>

            {/* Tools */}
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-6 mb-3 px-3">
              Tools
            </div>

            <NavLink
              to="/validate"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Check />
              <span>Validator</span>
            </NavLink>

            <NavLink
              to="/audit"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Audit />
              <span>Audit Log</span>
            </NavLink>

            {/* Settings */}
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-6 mb-3 px-3">
              Settings
            </div>

            <NavLink
              to="/settings/api-keys"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.Key />
              <span>API Keys</span>
            </NavLink>

            <NavLink
              to="/settings/ai"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icons.AI />
              <span>AI Settings</span>
            </NavLink>
          </nav>

          {/* Constitutional Notice - Fixed at bottom of sidebar */}
          <div className="sticky bottom-0 left-0 right-0 p-3 border-t bg-amber-50 mt-auto">
            <div className="text-xs text-amber-800">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-red-600 font-bold">AI = ZERO</span>
                <span className="text-gray-400">|</span>
                <span className="text-green-600 font-bold">HUMAN ONLY</span>
              </div>
              <p className="opacity-70">Per MANTRA-LAW-001</p>
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

      {/* AI Chat Assistant - Floating Widget */}
      <FloatingChat />
    </div>
  )
}
