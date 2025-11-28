/**
 * Organizations Page
 *
 * LAYER 1: PRESENTATION
 * Main page for organization management - orchestration only
 */

import { useState } from 'react';
import { Plus, Building, Shield } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  useOrganizations,
  useCreateOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from '../hooks/useOrganizations';
import { OrganizationList } from '../components/OrganizationList';
import { OrganizationForm } from '../components/OrganizationForm';
import { ConfirmDialog, TableSkeleton, AccessDenied, Button } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
} from '../types/organization';

export default function OrganizationsPage() {
  const { t } = useTranslation();
  const { data: organizationsData, isLoading } = useOrganizations();
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

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
            </div>
          ))}
        </div>
        <TableSkeleton rows={5} columns={5} />
      </div>
    );
  }

  return (
    <>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('organizations.totalOrganizations')}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {totalOrgs}
              </p>
            </div>
            <Building className="w-10 h-10 text-blue-600 dark:text-blue-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('organizations.active')}
              </p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {activeOrgs}
              </p>
            </div>
            <Shield className="w-10 h-10 text-green-600 dark:text-green-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('organizations.inactive')}
              </p>
              <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                {inactiveOrgs}
              </p>
            </div>
            <Shield className="w-10 h-10 text-gray-600 dark:text-gray-400" />
          </div>
        </div>
      </div>

      {/* Actions */}
      {canCreate && (
        <div className="mb-6 flex justify-end">
          <Button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            {t('organizations.createOrganization')}
          </Button>
        </div>
      )}

      {/* Organizations Table */}
      <OrganizationList
        organizations={organizations}
        onEdit={canEdit ? setEditingOrg : undefined}
        onDelete={canDelete ? setDeletingOrg : undefined}
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
