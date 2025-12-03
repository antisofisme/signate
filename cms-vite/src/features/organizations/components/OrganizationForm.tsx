/**
 * Organization Form Modal Component
 *
 * LAYER 1: PRESENTATION
 * Form for creating/editing organizations
 */

import { useState } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { Copy, Check, RefreshCw, Shield, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { Modal, Button, FormInput, FormTextarea, ConfirmDialog } from '@/shared/components';
import { useRegeneratePin } from '../hooks/useOrganizations';
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

  // PIN management state
  const [showPin, setShowPin] = useState(false);
  const [copiedPin, setCopiedPin] = useState(false);
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  const [currentPin, setCurrentPin] = useState(organization?.organization_pin || '');

  // PIN mutations
  const regeneratePinMutation = useRegeneratePin();

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

  // Copy PIN to clipboard
  const handleCopyPin = async () => {
    if (!currentPin) return;
    try {
      await navigator.clipboard.writeText(currentPin);
      setCopiedPin(true);
      toast.success('PIN berhasil disalin');
      setTimeout(() => setCopiedPin(false), 2000);
    } catch {
      toast.error('Gagal menyalin PIN');
    }
  };

  // Regenerate PIN
  const handleRegeneratePin = () => {
    if (!organization) return;
    regeneratePinMutation.mutate(organization.id, {
      onSuccess: (data) => {
        setCurrentPin(data.new_pin);
        setShowRegenerateConfirm(false);
      },
    });
  };

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
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

          {/* PIN Management Section - only for Edit */}
          {organization && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-5 h-5 text-amber-600" />
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                  {t('organizations.pinManagement', 'PIN Security')}
                </h4>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                {t('organizations.pinDescription', 'PIN digunakan untuk verifikasi operasi sensitif seperti menghapus menu. Jaga kerahasiaan PIN ini.')}
              </p>

              <div className="flex items-center gap-3">
                {/* PIN Display */}
                <div className="flex-1 relative">
                  <input
                    type={showPin ? 'text' : 'password'}
                    value={currentPin || '-'}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-mono text-center tracking-widest"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPin(!showPin)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title={showPin ? 'Sembunyikan PIN' : 'Tampilkan PIN'}
                  >
                    {showPin ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Copy Button */}
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={handleCopyPin}
                  disabled={!currentPin}
                  title="Salin PIN"
                >
                  {copiedPin ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>

                {/* Regenerate Button */}
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowRegenerateConfirm(true)}
                  disabled={regeneratePinMutation.isPending}
                  loading={regeneratePinMutation.isPending}
                  title="Generate PIN baru"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>

              {!currentPin && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                  ⚠️ PIN belum diatur. Klik tombol refresh untuk generate PIN baru.
                </p>
              )}
            </div>
          )}

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

      {/* Regenerate PIN Confirmation Dialog */}
      <ConfirmDialog
        open={showRegenerateConfirm}
        onOpenChange={setShowRegenerateConfirm}
        title={t('organizations.regeneratePinTitle', 'Generate PIN Baru?')}
        description={t('organizations.regeneratePinMessage', 'PIN lama akan digantikan dengan PIN baru yang di-generate secara acak. PIN sebelumnya tidak akan bisa digunakan lagi. Pastikan untuk menyimpan PIN baru.')}
        variant="warning"
        confirmLabel={t('organizations.regeneratePin', 'Generate PIN Baru')}
        onConfirm={handleRegeneratePin}
        isLoading={regeneratePinMutation.isPending}
      />
    </Modal>
  );
}

export default OrganizationForm;
