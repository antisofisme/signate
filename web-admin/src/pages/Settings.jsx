import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Users, Database } from 'lucide-react'

// Tab Components
import UsersTab from '../components/settings/UsersTab'
import SystemTab from '../components/settings/SystemTab'

/**
 * Settings Page
 * Central configuration hub with tabbed interface
 *
 * Tabs:
 * - Users: User management, roles, permissions
 * - System: Backup, logs, maintenance, system info
 */
export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') || 'users'

  const tabs = [
    {
      id: 'users',
      label: 'Users',
      icon: Users,
      description: 'Manage users, roles, and permissions',
      component: UsersTab
    },
    {
      id: 'system',
      label: 'System',
      icon: Database,
      description: 'Backup, logs, and system maintenance',
      component: SystemTab
    }
  ]

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId })
  }

  const currentTab = tabs.find(t => t.id === activeTab) || tabs[0]
  const TabComponent = currentTab.component

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      {/* Page Header - Dashboard style */}
      <div className="fixed top-0 left-0 right-0 lg:left-64 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-md transition-colors">
        <div className="px-4 sm:px-6 lg:px-8 py-3">
          <div className="pl-12 lg:pl-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mt-1">
              Manage system configuration and preferences
            </p>
          </div>
        </div>
      </div>

      {/* Content with padding to account for fixed header */}
      <div className="pt-20 sm:pt-24 lg:pt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tab Navigation */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id

                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`
                      flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm transition-colors
                      ${isActive
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Tab Description */}
          <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 border-b border-gray-200">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {currentTab.description}
            </p>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            <TabComponent />
          </div>
        </div>
        </div>
      </div>
    </div>
  )
}
