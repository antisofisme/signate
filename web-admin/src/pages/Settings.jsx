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
    <div>
      {/* Header */}
      <div className="sticky top-0 z-50 bg-white dark:bg-gray-800 dark:bg-gray-800 pb-4 mb-4 border-b border-gray-200 dark:border-gray-700 px-6">
        <div className="pt-4">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
            Manage system configuration and preferences
          </p>
        </div>
      </div>

      <div className="px-6">
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
  )
}
