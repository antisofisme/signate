/**
 * Organizations Page
 *
 * LAYER 1: PRESENTATION
 * Main page for organization management - orchestration only
 */

import { useState } from 'react';
import { Plus, Building, Shield, Loader2 } from 'lucide-react';
import {
  useOrganizations,
  useCreateOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from '../hooks/useOrganizations';
import { OrganizationList } from '../components/OrganizationList';
import { OrganizationForm } from '../components/OrganizationForm';
import { DeleteConfirmModal } from '@/shared/components/DeleteConfirmModal';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
} from '../types/organization';

export default function OrganizationsPage() {
  const { data: organizationsData, isLoading } = useOrganizations();
  const createMutation = useCreateOrganization();
  const updateMutation = useUpdateOrganization();
  const deleteMutation = useDeleteOrganization();

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

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
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
                Total Organizations
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
                Active
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
                Inactive
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
      <div className="mb-6 flex justify-end">
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" />
          Create Organization
        </button>
      </div>

      {/* Organizations Table */}
      <OrganizationList
        organizations={organizations}
        onEdit={setEditingOrg}
        onDelete={setDeletingOrg}
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

      {deletingOrg && (
        <DeleteConfirmModal
          isOpen={!!deletingOrg}
          title="Delete Organization"
          message="Are you sure you want to delete this organization?"
          itemName={deletingOrg.name}
          onClose={() => setDeletingOrg(null)}
          onConfirm={handleDelete}
          isLoading={deleteMutation.isPending}
        />
      )}
    </>
  );
}
