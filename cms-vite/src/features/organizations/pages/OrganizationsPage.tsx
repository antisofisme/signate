/**
 * Organizations Page
 *
 * LAYER 1: PRESENTATION
 * Main page for organization management - orchestration only
 */

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  useOrganizations,
  useCreateOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from '../hooks/useOrganizations';
import { OrganizationList } from '../components/OrganizationList';
import { OrganizationForm } from '../components/OrganizationForm';
import {
  ConfirmDialog,
  TableSkeleton,
  AccessDenied,
  Button,
  PageHeader,
  PageStats,
  PageToolbar,
} from '@/shared/components';
import { useTableSort } from '@/shared/hooks';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
} from '../types/organization';

export default function OrganizationsPage() {
  const { t } = useTranslation();

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'name', direction: 'asc' },
  });

  // Data fetching with sorting
  const { data: organizationsData, isLoading } = useOrganizations(sortParams);
  const createMutation = useCreateOrganization();
  const updateMutation = useUpdateOrganization();
  const deleteMutation = useDeleteOrganization();

  // Permission checks
  const { hasPermission: canView } = useCanPerformAction('organizations', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('organizations', 'create');
  const { hasPermission: canEdit } = useCanPerformAction('organizations', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('organizations', 'delete');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [deletingOrg, setDeletingOrg] = useState<Organization | null>(null);

  // Extract organizations from data
  const organizations = organizationsData?.organizations || [];

  // Stats
  const totalOrgs = organizationsData?.total || 0;
  const activeOrgs = organizationsData?.active || 0;
  const inactiveOrgs = totalOrgs - activeOrgs;

  const handleCreate = (data: CreateOrganizationRequest) => {
    createMutation.mutate(data, {
      onSuccess: () => setShowCreateModal(false),
    });
  };

  const handleUpdate = (data: UpdateOrganizationRequest) => {
    if (!editingOrg) return;
    updateMutation.mutate(
      { id: editingOrg.id, data },
      {
        onSuccess: () => setEditingOrg(null),
      }
    );
  };

  const handleDelete = () => {
    if (!deletingOrg) return;
    deleteMutation.mutate(deletingOrg.id, {
      onSuccess: () => setDeletingOrg(null),
    });
  };

  // Access control
  if (!canView) {
    return <AccessDenied />;
  }


  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('organizations.title', 'Organizations')}
        description={t('organizations.subtitle', 'Manage tenant organizations')}
      />

      {/* ROW 1: Stats */}
      <PageStats
        total={totalOrgs}
        totalLabel="organizations"
        stats={[
          { label: 'active', value: activeOrgs, color: 'text-green-600 dark:text-green-400' },
          { label: 'inactive', value: inactiveOrgs, color: 'text-gray-500' },
        ]}
      />

      {/* ROW 2: Toolbar */}
      <PageToolbar>
        <PageToolbar.Left>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {t('organizations.manageTenants', 'Manage tenant organizations and quotas')}
          </span>
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setShowCreateModal(true)}
              leftIcon={<Plus className="w-5 h-5" />}
            >
              {t('organizations.createOrganization')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Organizations Table */}
      <OrganizationList
        organizations={organizations}
        isLoading={isLoading}
        onEdit={canEdit ? setEditingOrg : undefined}
        onDelete={canDelete ? setDeletingOrg : undefined}
        sortConfig={sortConfig}
        onSortChange={onSortChange}
      />

      {/* Modals */}
      {showCreateModal && (
        <OrganizationForm
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />
      )}

      {editingOrg && (
        <OrganizationForm
          organization={editingOrg}
          onClose={() => setEditingOrg(null)}
          onSubmit={handleUpdate}
          isLoading={updateMutation.isPending}
        />
      )}

      <ConfirmDialog
        open={!!deletingOrg}
        onOpenChange={(open) => !open && setDeletingOrg(null)}
        title={t('organizations.deleteOrganization')}
        description={`${t('organizations.deleteConfirmMessage')} "${deletingOrg?.name}"?`}
        variant="danger"
        confirmLabel={t('organizations.delete', 'Delete')}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
