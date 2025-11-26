/**
 * Organization Quota Page
 *
 * Full page view for managing organization quotas
 * Combines QuotaDashboard and QuotaSettingsForm
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/shared/components';
import { Button } from '@/components/ui/button';
import { ArrowLeft, TrendingUp } from 'lucide-react';
import { useOrganizationQuota } from '../hooks/useOrganizationQuota';
import { QuotaDashboard } from '../components/QuotaDashboard';
import { QuotaSettingsForm } from '../components/QuotaSettingsForm';
import { useAuthStore } from '@/lib/stores/authStore';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

export default function OrganizationQuotaPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const orgId = id ? parseInt(id, 10) : user?.organization_id;

  const {
    data: quota,
    isLoading,
    isError,
    error,
    refetch,
  } = useOrganizationQuota(orgId);

  // Loading state
  if (isLoading) {
    return (
      <>
        <PageHeader
          title={t('organizations.organizationQuota')}
          description={t('organizations.loadingQuotaInfo')}
        />
        <div className="space-y-6">
          <Skeleton className="h-48 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
          <Skeleton className="h-96 w-full" />
        </div>
      </>
    );
  }

  // Error state
  if (isError || !quota) {
    return (
      <>
        <PageHeader
          title={t('organizations.organizationQuota')}
          description={t('organizations.errorLoadingQuota')}
        />
        <Alert variant="destructive">
          <AlertDescription>
            {t('organizations.failedToLoadQuota')}: {error?.message || t('organizations.unknownError')}
          </AlertDescription>
        </Alert>
        <div className="mt-4">
          <Button onClick={() => navigate(-1)} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('organizations.goBack')}
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('organizations.quotaManagement')}
        description={t('organizations.quotaManagementDescription')}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/settings')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t('organizations.backToSettings')}
            </Button>
          </div>
        }
      />

      {/* Content */}
      <div className="space-y-8">
        {/* Quota Dashboard */}
        <QuotaDashboard
          quota={quota}
          organizationId={orgId!}
          isLoading={isLoading}
          onRefresh={() => refetch()}
        />

        {/* Quota Settings Form (Admin Only) */}
        <QuotaSettingsForm
          quota={quota}
          organizationId={orgId!}
        />
      </div>
    </>
  );
}
