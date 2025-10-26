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
    <div>
      {/* Header */}
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <div className="pt-4">
          <h1 className="text-3xl font-bold text-gray-800">Widgets</h1>
          <p className="text-gray-600 text-sm mt-1">
            Create interactive content and widgets to display on devices
          </p>
        </div>
      </div>

      <div className="px-6">
        {/* Tab Navigation */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
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
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <p className="text-sm text-gray-600">
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
