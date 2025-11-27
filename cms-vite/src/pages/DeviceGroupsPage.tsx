/**
 * Device Groups Page
 *
 * LAYER 1: PRESENTATION
 * Page wrapper for Device Groups management
 */

import { PageHeader, AccessDenied, PageSkeleton } from '@/shared/components'
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions'
import { DeviceGroups } from '@/features/devices/components/DeviceGroups'

export default function DeviceGroupsPage() {
  const { hasPermission, isLoading } = useCanPerformAction('device_groups', 'view')

  // Show loading while checking permission
  if (isLoading) {
    return <PageSkeleton />
  }

  // Check view permission
  if (!hasPermission) {
    return <AccessDenied />
  }

  return (
    <>
      <PageHeader
        title="Device Groups"
        description="Organize devices into groups for bulk management"
      />
      <DeviceGroups />
    </>
  )
}
