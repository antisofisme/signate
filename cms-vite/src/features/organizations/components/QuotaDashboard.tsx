/**
 * Quota Dashboard Component
 *
 * Main quota overview dashboard showing all quota metrics, warnings, and overall status
 * Displays: Devices, Users, Content (items + storage), Playlists
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Server,
  Users,
  FileText,
  Folder,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  TrendingUp,
  HardDrive,
  Activity
} from 'lucide-react';
import { QuotaUsageCard } from './QuotaUsageCard';
import type { OrganizationQuota } from '../types/organization';
import { cn } from '@/lib/utils';

interface QuotaDashboardProps {
  quota: OrganizationQuota;
  organizationId: number;
  isLoading?: boolean;
  onRefresh?: () => void;
}

export function QuotaDashboard({
  quota,
  organizationId,
  isLoading = false,
  onRefresh
}: QuotaDashboardProps) {

  // Determine overall status based on percentage
  const getOverallStatus = () => {
    const percentage = quota.total_percentage_used;
    if (percentage >= 95) return { label: 'Critical', variant: 'destructive' as const, color: 'text-red-600' };
    if (percentage >= 80) return { label: 'Warning', variant: 'warning' as const, color: 'text-orange-600' };
    if (percentage >= 60) return { label: 'Moderate', variant: 'default' as const, color: 'text-yellow-600' };
    return { label: 'Healthy', variant: 'success' as const, color: 'text-green-600' };
  };

  const status = getOverallStatus();

  // Calculate warnings
  const hasWarnings = quota.warnings && quota.warnings.length > 0;
  const criticalResources = [
    { name: 'Devices', percentage: quota.devices.percentage_used },
    { name: 'Users', percentage: quota.users.percentage_used },
    { name: 'Content Items', percentage: quota.content.items_percentage_used },
    { name: 'Storage', percentage: quota.content.size_percentage_used },
    { name: 'Playlists', percentage: quota.playlists.percentage_used },
  ].filter(r => r.percentage >= 90);

  return (
    <div className="space-y-6">
      {/* Overall Status Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Organization Quota Status</CardTitle>
              <CardDescription>
                Monitor and manage your organization's resource usage
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center gap-4">
              <Activity className={cn("h-8 w-8", status.color)} />
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Overall Usage</div>
                <div className="text-3xl font-bold">{quota.total_percentage_used.toFixed(1)}%</div>
              </div>
            </div>
            <Badge
              variant={status.variant}
              className={cn(
                "text-lg px-4 py-2",
                status.variant === 'destructive' && 'bg-red-100 text-red-800',
                status.variant === 'warning' && 'bg-orange-100 text-orange-800',
                status.variant === 'default' && 'bg-yellow-100 text-yellow-800',
                status.variant === 'success' && 'bg-green-100 text-green-800'
              )}
            >
              {status.label}
            </Badge>
          </div>

          {/* Critical Resources Alert */}
          {criticalResources.length > 0 && (
            <Alert variant="destructive" className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Critical Resources</AlertTitle>
              <AlertDescription>
                The following resources have exceeded 90% usage:
                <div className="flex flex-wrap gap-2 mt-2">
                  {criticalResources.map((resource) => (
                    <Badge key={resource.name} variant="destructive">
                      {resource.name}: {resource.percentage.toFixed(1)}%
                    </Badge>
                  ))}
                </div>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Quota Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Devices Quota */}
        <QuotaUsageCard
          title="Devices"
          description="Connected displays"
          quota={quota.devices}
          icon={<Server className="h-5 w-5 text-blue-600" />}
        />

        {/* Users Quota */}
        <QuotaUsageCard
          title="Users"
          description="CMS admin users"
          quota={quota.users}
          icon={<Users className="h-5 w-5 text-purple-600" />}
        />

        {/* Content Quota (Storage) */}
        <QuotaUsageCard
          title="Content"
          description="Media files"
          quota={quota.content}
          icon={<FileText className="h-5 w-5 text-orange-600" />}
          isStorage={true}
        />

        {/* Playlists Quota */}
        <QuotaUsageCard
          title="Playlists"
          description="Content schedules"
          quota={quota.playlists}
          icon={<Folder className="h-5 w-5 text-green-600" />}
        />
      </div>

      {/* Warnings Section */}
      {hasWarnings && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <CardTitle>Quota Warnings</CardTitle>
            </div>
            <CardDescription>
              Action required to prevent service interruption
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {quota.warnings.map((warning, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">{warning}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Resource Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Breakdown</CardTitle>
          <CardDescription>Detailed view of all quota limits and usage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Devices */}
            <div className="flex items-center justify-between py-3 border-b">
              <div className="flex items-center gap-3">
                <Server className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="font-medium">Devices</div>
                  <div className="text-sm text-gray-500">Connected displays and monitors</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">{quota.devices.current} / {quota.devices.max}</div>
                <div className="text-sm text-gray-500">{quota.devices.available} available</div>
              </div>
            </div>

            {/* Users */}
            <div className="flex items-center justify-between py-3 border-b">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-purple-600" />
                <div>
                  <div className="font-medium">Users</div>
                  <div className="text-sm text-gray-500">CMS administrator accounts</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">{quota.users.current} / {quota.users.max}</div>
                <div className="text-sm text-gray-500">{quota.users.available} available</div>
              </div>
            </div>

            {/* Content Items */}
            <div className="flex items-center justify-between py-3 border-b">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-orange-600" />
                <div>
                  <div className="font-medium">Content Items</div>
                  <div className="text-sm text-gray-500">Total number of media files</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  {quota.content.current_items.toLocaleString()} / {quota.content.max_items.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">
                  {quota.content.available_items.toLocaleString()} available
                </div>
              </div>
            </div>

            {/* Storage Size */}
            <div className="flex items-center justify-between py-3 border-b">
              <div className="flex items-center gap-3">
                <HardDrive className="h-5 w-5 text-indigo-600" />
                <div>
                  <div className="font-medium">Storage Size</div>
                  <div className="text-sm text-gray-500">Total disk space used</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  {quota.content.current_size_gb.toFixed(2)} GB / {quota.content.max_size_gb} GB
                </div>
                <div className="text-sm text-gray-500">
                  {quota.content.available_size_gb.toFixed(2)} GB available
                </div>
              </div>
            </div>

            {/* Playlists */}
            <div className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <Folder className="h-5 w-5 text-green-600" />
                <div>
                  <div className="font-medium">Playlists</div>
                  <div className="text-sm text-gray-500">Content scheduling schedules</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">{quota.playlists.current} / {quota.playlists.max}</div>
                <div className="text-sm text-gray-500">{quota.playlists.available} available</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Best Practices Section */}
      {quota.total_percentage_used < 60 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <CardTitle>Quota Health</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Your organization's quota usage is healthy. Continue monitoring regularly to ensure smooth operations.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
