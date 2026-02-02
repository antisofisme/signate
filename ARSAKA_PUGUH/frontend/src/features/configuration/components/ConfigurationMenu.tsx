/**
 * Configuration Menu - Master Data Management
 * Container with tabs for managing all configuration master data
 */

import { useState } from 'react'
import { FunctionalAreasTab } from './FunctionalAreasTab'
import { DecisionTypesTab } from './DecisionTypesTab'
import { ApproverRolesTab } from './ApproverRolesTab'

type TabKey = 'functional-areas' | 'decision-types' | 'approver-roles'

export function ConfigurationMenu() {
  const [activeTab, setActiveTab] = useState<TabKey>('functional-areas')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Configuration</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage master data for governance, UI grouping, and decision contracts
          </p>
        </div>

        {/* Tabs */}
        <div className="container mx-auto px-4">
          <div className="flex gap-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('functional-areas')}
              className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'functional-areas'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Functional Areas
            </button>
            <button
              onClick={() => setActiveTab('decision-types')}
              className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'decision-types'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Decision Types
            </button>
            <button
              onClick={() => setActiveTab('approver-roles')}
              className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'approver-roles'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Approver Roles
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="container mx-auto px-4 py-6">
        {activeTab === 'functional-areas' && <FunctionalAreasTab />}
        {activeTab === 'decision-types' && <DecisionTypesTab />}
        {activeTab === 'approver-roles' && <ApproverRolesTab />}
      </div>
    </div>
  )
}
