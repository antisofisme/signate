/**
 * Menu Media Page
 *
 * LAYER 1: PRESENTATION
 * Dedicated page for managing menu media (images for menu items)
 */

import { useTranslation } from 'react-i18next';
import { PageHeader, PageSkeleton, AccessDenied } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { MenuMediaTab } from '../components/MenuMediaTab';

export default function MenuMediaPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('menus', 'read');

  // Permission loading
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Access denied
  if (!canView) {
    return <AccessDenied />;
  }

  return (
    <>
      <PageHeader
        title={t('menus.mediaTitle', 'Menu Media')}
        description={t('menus.mediaSubtitle', 'Upload and manage images for your digital menu items')}
      />

      <div className="space-y-6">
        <MenuMediaTab />
      </div>
    </>
  );
}
