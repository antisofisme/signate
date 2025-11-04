/**
 * Settings Page
 *
 * LAYER 1: PRESENTATION
 * Tabbed settings page with Organizations and Users management
 */

import { useState } from 'react';
import { Building, Users, Settings as SettingsIcon } from 'lucide-react';
import OrganizationsTab from '@/features/organizations/components/OrganizationsTab';
import UsersTab from '@/features/users/components/UsersTab';

type TabType = 'organizations' | 'users';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('organizations');

  const tabs = [
    {
      id: 'organizations' as TabType,
      name: 'Organizations',
      icon: Building,
      component: OrganizationsTab,
    },
    {
      id: 'users' as TabType,
      name: 'Users',
      icon: Users,
      component: UsersTab,
    },
  ];

  const ActiveComponent = tabs.find((tab) => tab.id === activeTab)?.component;

  return (
    <div className="p-8">
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <SettingsIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Settings
          </h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage system settings, organizations, and users (HMR enabled ✅)
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">{ActiveComponent && <ActiveComponent />}</div>
    </div>
  );
}
