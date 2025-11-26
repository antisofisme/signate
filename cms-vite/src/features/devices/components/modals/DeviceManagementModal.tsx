/**
 * Unified Device Management Modal
 *
 * Single modal with tabs for all device management functions:
 * - Overview: Device info + quick actions
 * - Health: Metrics + diagnostics
 * - Commands: Remote control
 * - Content: Assignment management
 * - Logs: Debugging
 * - Settings: Configuration
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  Activity,
  Terminal as TerminalIcon,
  Tv,
  Monitor,
} from 'lucide-react';
import { Modal, Tabs, TabPanel, type Tab } from '@/shared/components';
import type { Device } from '../../types/device';

// Tab components
import { OverviewTab } from './tabs/OverviewTab';
import { HealthTab } from './tabs/HealthTab';
import { CommandsTab } from './tabs/CommandsTab';

export type DeviceTabId = 'overview' | 'health' | 'commands';

interface DeviceManagementModalProps {
  isOpen: boolean;
  device: Device | null;
  defaultTab?: DeviceTabId;
  onClose: () => void;
  onRefresh?: () => void;
}

export function DeviceManagementModal({
  isOpen,
  device,
  defaultTab = 'overview',
  onClose,
  onRefresh,
}: DeviceManagementModalProps) {
  const { t } = useTranslation();

  const DEVICE_TABS: Tab[] = [
    {
      id: 'overview',
      label: t('devices.modals.overview'),
      icon: LayoutDashboard,
    },
    {
      id: 'health',
      label: t('devices.modals.health'),
      icon: Activity,
    },
    {
      id: 'commands',
      label: t('devices.modals.commands'),
      icon: TerminalIcon,
    },
  ];
  const [activeTab, setActiveTab] = useState<DeviceTabId>(defaultTab);

  if (!device) return null;

  // Calculate online status
  const isOnline = device.last_seen_at
    ? new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000
    : false;

  // Device type icon
  const DeviceIcon = device.device_type === 'tv' ? Tv : Monitor;

  // Custom header with device info and tab navigation
  const customHeader = (
    <div className="sticky top-0 bg-white dark:bg-gray-800 z-10">
      {/* Device Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-12 h-12 rounded-lg flex items-center justify-center ${
              device.device_type === 'tv'
                ? 'bg-blue-100 dark:bg-blue-900'
                : 'bg-purple-100 dark:bg-purple-900'
            }`}
          >
            <DeviceIcon
              className={`w-6 h-6 ${
                device.device_type === 'tv'
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-purple-600 dark:text-purple-400'
              }`}
            />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {device.device_name}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              {/* Status Badge */}
              {device.status === 'pending' ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                  Pending Activation
                </span>
              ) : isOnline ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Online
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  <span className="w-2 h-2 bg-red-500 rounded-full" />
                  Offline
                </span>
              )}
              <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                {device.device_type} • ID: {device.id}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs tabs={DEVICE_TABS} activeTab={activeTab} onChange={(id) => setActiveTab(id as DeviceTabId)} />
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="7xl"
      customHeader={customHeader}
      className="h-[90vh]"
    >
      {/* Tab Panels */}
      <div className="overflow-y-auto max-h-[calc(90vh-180px)]">
        <TabPanel activeTab={activeTab} tabId="overview">
          <OverviewTab device={device} isOnline={isOnline} onRefresh={onRefresh} />
        </TabPanel>

        <TabPanel activeTab={activeTab} tabId="health">
          <HealthTab device={device} isOnline={isOnline} />
        </TabPanel>

        <TabPanel activeTab={activeTab} tabId="commands">
          <CommandsTab device={device} isOnline={isOnline} />
        </TabPanel>
      </div>
    </Modal>
  );
}
