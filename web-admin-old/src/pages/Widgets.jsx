import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Calendar, MessageSquare, Globe, Cloud, Timer, Clock, Hotel } from 'lucide-react'

// Tab Components (will be created)
import CalendarTab from '../components/widgets/CalendarTab'
import TextTab from '../components/widgets/TextTab'
import IFrameTab from '../components/widgets/IFrameTab'
import WeatherTab from '../components/widgets/WeatherTab'
import CountdownTab from '../components/widgets/CountdownTab'
import ClockTab from '../components/widgets/ClockTab'
import SystemPMSTab from '../components/widgets/SystemPMSTab'

/**
 * Widgets Page
 * Interactive content and widgets management
 *
 * Tabs:
 * - Calendar: Calendar events and displays
 * - Welcome Message: Greeting messages
 * - iFrame: Embed external websites/URLs
 * - Simple Message: Text message displays
 * - Weather: Weather information widgets
 * - Countdown: Countdown timers
 * - Clock: Clock and time displays
 */
export default function Widgets() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') || 'calendar'

  const tabs = [
    {
      id: 'calendar',
      label: 'Calendar',
      icon: Calendar,
      description: 'Create and manage calendar event displays',
      component: CalendarTab
    },
    {
      id: 'text',
      label: 'Text',
      icon: MessageSquare,
      description: 'Create and display text messages',
      component: TextTab
    },
    {
      id: 'iframe',
      label: 'iFrame',
      icon: Globe,
      description: 'Embed external websites and web content',
      component: IFrameTab
    },
    {
      id: 'weather',
      label: 'Weather',
      icon: Cloud,
      description: 'Show weather information and forecasts',
      component: WeatherTab
    },
    {
      id: 'countdown',
      label: 'Countdown',
      icon: Timer,
      description: 'Create countdown timers for events',
      component: CountdownTab
    },
    {
      id: 'clock',
      label: 'Clock',
      icon: Clock,
      description: 'Display time and date information',
      component: ClockTab
    },
    {
      id: 'systempms',
      label: 'SystemPMS',
      icon: Hotel,
      description: 'Integrate with Property Management System for hotel data',
      component: SystemPMSTab
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
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Widgets</h1>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mt-1">
              Create interactive content and widgets to display on devices
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
            <nav className="flex -mb-px overflow-x-auto">
              {tabs.map((tab) => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id

                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`
                      flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap
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
