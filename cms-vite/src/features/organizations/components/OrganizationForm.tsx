/**
 * Organization Form Modal Component
 *
 * LAYER 1: PRESENTATION
 * Form for creating/editing organizations
 */

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
} from '../types/organization';

interface OrganizationFormProps {
  organization?: Organization;
  onClose: () => void;
  onSubmit: (data: CreateOrganizationRequest | UpdateOrganizationRequest) => void;
  isLoading: boolean;
}

export function OrganizationForm({
  organization,
  onClose,
  onSubmit,
  isLoading,
}: OrganizationFormProps) {
  const { t } = useTranslation();
  const [name, setName] = useState(organization?.name || '');
  const [description, setDescription] = useState(organization?.description || '');
  const [address, setAddress] = useState(organization?.address || '');
  const [contactEmail, setContactEmail] = useState(organization?.contact_email || '');
  const [contactPhone, setContactPhone] = useState(organization?.contact_phone || '');
  const [logoUrl, setLogoUrl] = useState(organization?.logo_url || '');
  const [isActive, setIsActive] = useState(organization?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (organization) {
      // Update
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
      // Create
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
          {organization ? t('organizations.editOrganization') : t('organizations.createOrganization')}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('organizations.organizationName')} *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('organizations.description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder={t('organizations.descriptionPlaceholder')}
            />
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('organizations.address')}
            </label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              rows={2}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder={t('organizations.addressPlaceholder')}
            />
          </div>

          {/* Contact Info - Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('organizations.contactEmail')}
              </label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder={t('organizations.contactEmailPlaceholder')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('organizations.contactPhone')}
              </label>
              <input
                type="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                maxLength={20}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder={t('organizations.contactPhonePlaceholder')}
              />
            </div>
          </div>

          {/* Logo URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('organizations.logoUrl')}
            </label>
            <input
              type="url"
              value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder={t('organizations.logoUrlPlaceholder')}
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
                {t('organizations.organizationIsActive')}
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
              {t('organizations.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('organizations.saving')}
                </>
              ) : organization ? (
                t('organizations.update')
              ) : (
                t('organizations.create')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default OrganizationForm;
