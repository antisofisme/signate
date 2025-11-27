/**
 * Device Groups Page
 *
 * LAYER 1: PRESENTATION
 * Page wrapper for Device Groups management
 */

import { PageHeader, AccessDenied, PageSkeleton } from '@/shared/components'
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions'
import { DeviceGroups } from '@/features/devices/components/DeviceGroups'
import { useTranslation } from 'react-i18next'

export default function DeviceGroupsPage() {
  const { t } = useTranslation()
  const { hasPermission, isLoading } = useCanPerformAction('device_groups', 'read')

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
        title={t('deviceGroups.title')}
        description={t('deviceGroups.description')}
      />
      <DeviceGroups />
    </>
  )
}
