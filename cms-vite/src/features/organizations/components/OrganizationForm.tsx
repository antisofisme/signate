/**
 * Organization Form Modal Component
 *
 * LAYER 1: PRESENTATION
 * Form for creating/editing organizations
 */

import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FormInput, FormTextarea } from '@/shared/components';
import { Button } from '@/components/ui/button';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
} from '../types/organization';

// Validation schema
const organizationSchema = z.object({
  name: z.string().min(1, 'Organization name is required').max(200, 'Name is too long'),
  description: z.string().max(500, 'Description is too long').optional().or(z.literal('')),
  address: z.string().max(500, 'Address is too long').optional().or(z.literal('')),
  contact_email: z.string().email('Invalid email').max(100, 'Email is too long').optional().or(z.literal('')),
  contact_phone: z.string().max(20, 'Phone is too long').optional().or(z.literal('')),
  logo_url: z.string().url('Invalid URL').max(500, 'URL is too long').optional().or(z.literal('')),
  is_active: z.boolean().optional(),
});

type OrganizationFormData = z.infer<typeof organizationSchema>;

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

  const methods = useForm<OrganizationFormData>({
    resolver: zodResolver(organizationSchema),
    defaultValues: {
      name: organization?.name || '',
      description: organization?.description || '',
      address: organization?.address || '',
      contact_email: organization?.contact_email || '',
      contact_phone: organization?.contact_phone || '',
      logo_url: organization?.logo_url || '',
      is_active: organization?.is_active ?? true,
    },
  });

  const handleFormSubmit = (data: OrganizationFormData) => {
    if (organization) {
      // Update
      const updateData: UpdateOrganizationRequest = {
        name: data.name,
        description: data.description || undefined,
        address: data.address || undefined,
        contact_email: data.contact_email || undefined,
        contact_phone: data.contact_phone || undefined,
        logo_url: data.logo_url || undefined,
        is_active: data.is_active,
      };
      onSubmit(updateData);
    } else {
      // Create
      const createData: CreateOrganizationRequest = {
        name: data.name,
        description: data.description || undefined,
        address: data.address || undefined,
        contact_email: data.contact_email || undefined,
        contact_phone: data.contact_phone || undefined,
        logo_url: data.logo_url || undefined,
      };
      onSubmit(createData);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl my-8">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {organization ? t('organizations.editOrganization') : t('organizations.createOrganization')}
        </h3>

        <FormProvider {...methods}>
          <form onSubmit={methods.handleSubmit(handleFormSubmit)} className="space-y-4">
            {/* Name */}
            <FormInput
              name="name"
              label={`${t('organizations.organizationName')} *`}
              placeholder={t('organizations.organizationNamePlaceholder', 'Enter organization name')}
              required
            />

            {/* Description */}
            <FormTextarea
              name="description"
              label={t('organizations.description')}
              placeholder={t('organizations.descriptionPlaceholder')}
              rows={3}
            />

            {/* Address */}
            <FormTextarea
              name="address"
              label={t('organizations.address')}
              placeholder={t('organizations.addressPlaceholder')}
              rows={2}
            />

            {/* Contact Info - Grid */}
            <div className="grid grid-cols-2 gap-4">
              <FormInput
                name="contact_email"
                label={t('organizations.contactEmail')}
                type="email"
                placeholder={t('organizations.contactEmailPlaceholder')}
              />
              <FormInput
                name="contact_phone"
                label={t('organizations.contactPhone')}
                type="tel"
                placeholder={t('organizations.contactPhonePlaceholder')}
              />
            </div>

            {/* Logo URL */}
            <FormInput
              name="logo_url"
              label={t('organizations.logoUrl')}
              type="url"
              placeholder={t('organizations.logoUrlPlaceholder')}
            />

            {/* Active Status - only for Edit */}
            {organization && (
              <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <input
                  type="checkbox"
                  id="isActive"
                  {...methods.register('is_active')}
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
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
              >
                {t('organizations.cancel')}
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    {t('organizations.saving')}
                  </>
                ) : organization ? (
                  t('organizations.update')
                ) : (
                  t('organizations.create')
                )}
              </Button>
            </div>
          </form>
        </FormProvider>
      </div>
    </div>
  );
}

export default OrganizationForm;
