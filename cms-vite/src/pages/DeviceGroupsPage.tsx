/**
 * Device Groups Page
 *
 * LAYER 1: PRESENTATION
 * Page wrapper for Device Groups management
 */

import { PageHeader } from '@/shared/components'
import { DeviceGroups } from '@/features/devices/components/DeviceGroups'

export default function DeviceGroupsPage() {
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
