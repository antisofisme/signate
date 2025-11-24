/**
 * Logs Tab - Device Management Modal
 *
 * Technical logs for debugging:
 * - Console logs
 * - Connection logs
 * - Speed test logs
 */

import { useState } from 'react';
import { Terminal, Network, Gauge } from 'lucide-react';
import { Tabs, type Tab } from '@/shared/components';
import type { Device } from '../../../types/device';
import { DeviceLogsViewer, type LogsViewTab } from '../../DeviceLogsViewer';

interface LogsTabProps {
  device: Device;
}

const LOGS_TABS: Tab[] = [
  {
    id: 'console',
    label: 'Console',
    icon: Terminal,
  },
  {
    id: 'connection',
    label: 'Connection',
    icon: Network,
  },
  {
    id: 'speedtest',
    label: 'Speed Test',
    icon: Gauge,
  },
];

export function LogsTab({ device }: LogsTabProps) {
  const [activeLogsTab, setActiveLogsTab] = useState<LogsViewTab>('console');

  return (
    <>
      {/* Tabs Navigation in Header */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 -mx-6 px-6">
        <Tabs
          tabs={LOGS_TABS}
          activeTab={activeLogsTab}
          onChange={(id) => setActiveLogsTab(id as LogsViewTab)}
        />
      </div>

      {/* Logs Viewer Content */}
      <div className="flex-1 -mx-6">
        <DeviceLogsViewer
          deviceId={device.id}
          deviceName={device.device_name}
          activeTab={activeLogsTab}
          onTabChange={setActiveLogsTab}
        />
      </div>
    </>
  );
}
