/**
 * Device Logs Modal Component
 *
 * Comprehensive console logs and connection logs viewer
 * Uses centralized Modal component with tabs in header
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Terminal, Network, Gauge, Tv, Monitor } from 'lucide-react';
import { Modal, Tabs, type Tab } from '@/shared/components';
import { DeviceLogsViewer, type LogsViewTab } from '../DeviceLogsViewer';
import type { Device } from '../../types/device';

interface DeviceLogsModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function DeviceLogsModal({ isOpen, device, onClose }: DeviceLogsModalProps) {
  const { t } = useTranslation();

  const LOGS_TABS: Tab[] = [
    {
      id: 'console',
      label: t('devices.modals.console'),
      icon: Terminal,
    },
    {
      id: 'connection',
      label: t('devices.modals.connection'),
      icon: Network,
    },
    {
      id: 'speedtest',
      label: t('devices.modals.speedTest'),
      icon: Gauge,
    },
  ];
  const [activeTab, setActiveTab] = useState<LogsViewTab>('console');

  if (!device) return null;

  // Device type icon
  const DeviceIcon = device.device_type === 'tv' ? Tv : Monitor;

  // Calculate online status
  const isOnline = device.last_seen_at
    ? new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000
    : false;

  // Custom header with device info and tabs
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
              {t('devices.modals.deviceLogs')}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              {/* Status Badge */}
              {device.status === 'pending' ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                  {t('devices.modals.pendingActivation')}
                </span>
              ) : isOnline ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  {t('devices.online')}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  <span className="w-2 h-2 bg-red-500 rounded-full" />
                  {t('devices.offline')}
                </span>
              )}
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {device.device_name}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs tabs={LOGS_TABS} activeTab={activeTab} onChange={(id) => setActiveTab(id as LogsViewTab)} />
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="5xl"
      customHeader={customHeader}
    >
      {/* Logs Content - uses flex-1 from Modal's content area */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <DeviceLogsViewer
          deviceId={device.id}
          deviceName={device.device_name}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </div>
    </Modal>
  );
}
