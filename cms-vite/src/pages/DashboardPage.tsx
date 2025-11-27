/**
 * Dashboard Page (Control Room)
 *
 * LAYER 1: PRESENTATION
 * Real-time system monitoring and live status overview
 *
 * Focus: Live device status, current alerts, active playlists, recent activity
 * (Analytics page focuses on historical trends and reports)
 *
 * NOTE: Auto-polling removed for performance optimization.
 * Use the Refresh button to manually update data.
 */

import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/lib/stores/authStore';
import { PageHeader, RefreshButton, PageSkeleton, AccessDenied } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useDashboardStats,
  useDeviceHealth,
  useLiveDevices,
  useActivePlaylistAssignments,
  useRecentActivity,
  useSystemAlerts,
  useSystemInfo,
} from '@/features/dashboard/api/dashboard.api';
import OverviewMetrics from '@/features/dashboard/components/OverviewMetrics';
import DeviceHealthOverview from '@/features/dashboard/components/DeviceHealthOverview';
import LiveDeviceMonitor from '@/features/dashboard/components/LiveDeviceMonitor';
import ActivePlaylistsTable from '@/features/dashboard/components/ActivePlaylistsTable';
import RecentActivityFeed from '@/features/dashboard/components/RecentActivityFeed';
import SystemAlertsPanel from '@/features/dashboard/components/SystemAlertsPanel';
import SystemInfoPanel from '@/features/dashboard/components/SystemInfoPanel';
import { QuotaAlertBanner } from '@/features/organizations/components/QuotaAlertBanner';
import { useOrganizationQuota } from '@/features/organizations/hooks/useOrganizationQuota';

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Permission check
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('dashboard', 'view');

  // Show loading skeleton while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Show access denied if user lacks permission
  if (!canView) {
    return <AccessDenied />;
  }

  // Fetch all dashboard data with refetch functions
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useDashboardStats();
  const { data: deviceHealth, isLoading: healthLoading, refetch: refetchHealth } = useDeviceHealth();
  const { data: liveDevices, isLoading: devicesLoading, refetch: refetchDevices } = useLiveDevices();
  const { data: playlists, isLoading: playlistsLoading, refetch: refetchPlaylists } = useActivePlaylistAssignments();
  const { data: recentActivity, isLoading: activityLoading, refetch: refetchActivity } = useRecentActivity(20);
  const { data: systemAlerts, isLoading: alertsLoading, refetch: refetchAlerts } = useSystemAlerts();
  const { data: systemInfo, isLoading: systemInfoLoading, refetch: refetchSystemInfo } = useSystemInfo();

  // Fetch organization quota for alerts
  const { data: quota, refetch: refetchQuota } = useOrganizationQuota(user?.organization_id);

  // Combined refresh handler - refreshes all dashboard data
  const handleRefreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchStats(),
        refetchHealth(),
        refetchDevices(),
        refetchPlaylists(),
        refetchActivity(),
        refetchAlerts(),
        refetchSystemInfo(),
        refetchQuota(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [
    refetchStats,
    refetchHealth,
    refetchDevices,
    refetchPlaylists,
    refetchActivity,
    refetchAlerts,
    refetchSystemInfo,
    refetchQuota,
  ]);

  return (
    <>
      {/* Page Header with Refresh Button */}
      <PageHeader
        title={t('dashboard.title')}
        description={`${t('dashboard.welcome')}, ${user?.full_name || user?.username}!`}
        actions={
          <RefreshButton
            onClick={handleRefreshAll}
            isLoading={isRefreshing}
            label={t('common.refresh', 'Refresh')}
            title={t('dashboard.refreshAll', 'Refresh all dashboard data')}
          />
        }
      />

      {/* Quota Alert Banner - Shows critical warnings */}
      {quota && user?.organization_id && (
        <QuotaAlertBanner quota={quota} organizationId={user.organization_id} />
      )}

      {/* Dashboard Content */}
      <div className="space-y-6">
        {/* Section 1: Overview Metrics */}
        <OverviewMetrics stats={stats} isLoading={statsLoading} />

        {/* Section 2: Device Health Overview */}
        <DeviceHealthOverview data={deviceHealth} isLoading={healthLoading} />

        {/* Section 3: Live Device Monitor */}
        <LiveDeviceMonitor devices={liveDevices} isLoading={devicesLoading} />

        {/* Section 4: Active Playlists & Assignments */}
        <ActivePlaylistsTable data={playlists} isLoading={playlistsLoading} />

        {/* Recent Activity Feed - Full Width */}
        <RecentActivityFeed data={recentActivity} isLoading={activityLoading} />

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
