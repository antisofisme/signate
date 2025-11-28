/**
 * Organization Form Modal Component
 *
 * LAYER 1: PRESENTATION
 * Form for creating/editing organizations
 */

import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { Modal, Button, FormInput, FormTextarea } from '@/shared/components';
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

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <Button
          variant="ghost"
          onClick={onClose}
          disabled={isLoading}
        >
          {t('organizations.cancel')}
        </Button>
        <Button
          variant="primary"
          type="submit"
          form="organization-form"
          disabled={isLoading}
          loading={isLoading}
        >
          {organization ? t('organizations.update') : t('organizations.create')}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={organization ? t('organizations.editOrganization') : t('organizations.createOrganization')}
      maxWidth="2xl"
      footer={footer}
      closeOnBackdropClick={!isLoading}
    >
      <FormProvider {...methods}>
        <form
          id="organization-form"
          onSubmit={methods.handleSubmit(handleFormSubmit)}
          className="p-6 space-y-4"
        >
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
        </form>
      </FormProvider>
    </Modal>
  );
}

export default OrganizationForm;
