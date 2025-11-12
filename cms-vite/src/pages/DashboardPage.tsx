/**
 * Dashboard Page
 *
 * LAYER 1: PRESENTATION
 * Main dashboard with comprehensive system overview
 */

import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/lib/stores/authStore';
import { PageHeader } from '@/shared/components';
import {
  useDashboardStats,
  useDeviceHealth,
  useLiveDevices,
  useContentPerformance,
  useActivePlaylistAssignments,
  useRecentActivity,
  useSystemAlerts,
  useSystemInfo,
} from '@/features/dashboard/api/dashboard.api';
import OverviewMetrics from '@/features/dashboard/components/OverviewMetrics';
import DeviceHealthOverview from '@/features/dashboard/components/DeviceHealthOverview';
import LiveDeviceMonitor from '@/features/dashboard/components/LiveDeviceMonitor';
import ContentPerformanceAnalytics from '@/features/dashboard/components/ContentPerformanceAnalytics';
import ActivePlaylistsTable from '@/features/dashboard/components/ActivePlaylistsTable';
import RecentActivityFeed from '@/features/dashboard/components/RecentActivityFeed';
import SystemAlertsPanel from '@/features/dashboard/components/SystemAlertsPanel';
import SystemInfoPanel from '@/features/dashboard/components/SystemInfoPanel';

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  // Fetch all dashboard data
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: deviceHealth, isLoading: healthLoading } = useDeviceHealth();
  const { data: liveDevices, isLoading: devicesLoading } = useLiveDevices();
  const { data: contentPerformance, isLoading: contentLoading } = useContentPerformance(10);
  const { data: playlists, isLoading: playlistsLoading } = useActivePlaylistAssignments();
  const { data: recentActivity, isLoading: activityLoading } = useRecentActivity(20);
  const { data: systemAlerts, isLoading: alertsLoading } = useSystemAlerts();
  const { data: systemInfo, isLoading: systemInfoLoading } = useSystemInfo();

  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('dashboard.title')}
        description={`${t('dashboard.welcome')}, ${user?.full_name || user?.username}!`}
      />

      {/* Dashboard Content */}
      <div className="space-y-6">
        {/* Section 1: Overview Metrics */}
        <OverviewMetrics stats={stats} isLoading={statsLoading} />

        {/* Section 2: Device Health Overview */}
        <DeviceHealthOverview data={deviceHealth} isLoading={healthLoading} />

        {/* Section 3: Live Device Monitor */}
        <LiveDeviceMonitor devices={liveDevices} isLoading={devicesLoading} />

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Section 4: Content Performance Analytics */}
          <ContentPerformanceAnalytics data={contentPerformance} isLoading={contentLoading} />

          {/* Section 7: Recent Activity Feed */}
          <RecentActivityFeed data={recentActivity} isLoading={activityLoading} />
        </div>

        {/* Section 5: Active Playlists & Assignments */}
        <ActivePlaylistsTable data={playlists} isLoading={playlistsLoading} />

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Section 9: System Alerts */}
          <SystemAlertsPanel data={systemAlerts} isLoading={alertsLoading} />

          {/* Section 10: Storage & System Info */}
          <SystemInfoPanel data={systemInfo} isLoading={systemInfoLoading} />
        </div>
      </div>
    </>
  );
}
