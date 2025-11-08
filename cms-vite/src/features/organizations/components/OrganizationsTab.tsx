/**
 * Organizations Tab Component
 *
 * LAYER 1: PRESENTATION
 * Organizations management tab content (moved from OrganizationsPage)
 */

import { useState } from 'react';
import {
  Plus,
  Building,
  Shield,
  Edit,
  Trash2,
  Users,
  Monitor,
  Loader2,
} from 'lucide-react';
import {
  useOrganizations,
  useCreateOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from '../hooks/useOrganizations';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
} from '../types/organization';

// Reusable Delete Confirmation Modal
interface DeleteConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  itemName: string;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({
  isOpen,
  title,
  message,
  itemName,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {title}
        </h3>
        <p className="text-gray-700 dark:text-gray-300 mb-2">{message}</p>
        <p className="text-gray-900 dark:text-white font-semibold mb-6">
          {itemName}
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// Organization Modal
interface OrganizationModalProps {
  organization?: Organization;
  onClose: () => void;
  onSubmit: (data: any) => void;
  isLoading: boolean;
}

function OrganizationModal({
  organization,
  onClose,
  onSubmit,
  isLoading,
}: OrganizationModalProps) {
  const [name, setName] = useState(organization?.name || '');
  // REMOVED: Organization PIN state (No-PIN flow)
  const [description, setDescription] = useState(organization?.description || '');
  const [address, setAddress] = useState(organization?.address || '');
  const [contactEmail, setContactEmail] = useState(organization?.contact_email || '');
  const [contactPhone, setContactPhone] = useState(organization?.contact_phone || '');
  const [logoUrl, setLogoUrl] = useState(organization?.logo_url || '');
  const [isActive, setIsActive] = useState(organization?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (organization) {
      // Update - all fields except PIN
      const data: UpdateOrganizationRequest = {
        name,
        description: description || undefined,
        address: address || undefined,
        contact_email: contactEmail || undefined,
        contact_phone: contactPhone || undefined,
        logo_url: logoUrl || undefined,
        is_active: isActive,
      };
      onSubmit(data);
    } else {
      // Create - REMOVED: Organization PIN (No-PIN flow)
      const data: CreateOrganizationRequest = {
        name,
        description: description || undefined,
        address: address || undefined,
        contact_email: contactEmail || undefined,
        contact_phone: contactPhone || undefined,
        logo_url: logoUrl || undefined,
      };
      onSubmit(data);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl my-8">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {organization ? 'Edit Organization' : 'Create Organization'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Organization Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* REMOVED: Organization PIN input section (No-PIN flow) */}

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Brief description of the organization"
            />
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Address
            </label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              rows={2}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Physical address"
            />
          </div>

          {/* Contact Info - Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Contact Email
              </label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="email@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Contact Phone
              </label>
              <input
                type="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                maxLength={20}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="+62 xxx xxx xxx"
              />
            </div>
          </div>

          {/* Logo URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Logo URL
            </label>
            <input
              type="url"
              value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="https://example.com/logo.png"
            />
          </div>

          {/* Active Status - only for Edit */}
          {organization && (
            <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <input
                type="checkbox"
                id="isActive"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label
                htmlFor="isActive"
                className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer"
              >
                Organization is Active
              </label>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : organization ? (
                'Update'
              ) : (
                'Create'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function OrganizationsTab() {
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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Name
              </th>
              {/* REMOVED: PIN table header (No-PIN flow) */}
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Users
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Devices
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {organizations?.map((org) => (
              <tr key={org.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Building className="w-5 h-5 text-gray-400 mr-2" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {org.name}
                    </span>
                  </div>
                </td>
                {/* REMOVED: PIN table cell (No-PIN flow) */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Users className="w-4 h-4 mr-1" />
                    {org.user_count || 0}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Monitor className="w-4 h-4 mr-1" />
                    {org.device_count || 0}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      org.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}
                  >
                    {org.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setEditingOrg(org)}
                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setDeletingOrg(org)}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <OrganizationModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />
      )}

      {editingOrg && (
        <OrganizationModal
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
