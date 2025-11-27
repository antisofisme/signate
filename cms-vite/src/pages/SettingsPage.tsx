/**
 * Settings Page
 *
 * LAYER 1: PRESENTATION
 * Tabbed settings page with Organizations, Users, Sessions, and Roles management
 */

import { useState } from 'react';
import { Building, Users, Shield, Key } from 'lucide-react';
import OrganizationsTab from '@/features/organizations/pages/OrganizationsPage';
import UsersTab from '@/features/users/pages/UsersPage';
import SessionsTab from '@/features/sessions/pages/SessionsPage';
import RolesTab from '@/pages/RolesPage';
import { PageHeader } from '@/shared/components';

type TabType = 'organizations' | 'users' | 'sessions' | 'roles';

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
    {
      id: 'sessions' as TabType,
      name: 'Active Sessions',
      icon: Shield,
      component: SessionsTab,
    },
    {
      id: 'roles' as TabType,
      name: 'Roles & Permissions',
      icon: Key,
      component: RolesTab,
    },
  ];

  const ActiveComponent = tabs.find((tab) => tab.id === activeTab)?.component;

  return (
    <>
      {/* Sticky Page Header */}
      <PageHeader
        title="Settings"
        description="Manage system settings, organizations, and users"
      />

      {/* Content */}
      <div className="space-y-6">

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
    </>
  );
}
