/**
 * Change Password Dialog Component
 *
 * Modal dialog for changing user passwords
 * Following CMS UI Development skill standards
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Key, Loader2 } from 'lucide-react';
import { Button, Modal, FormInput } from '@/shared/components';
import type { User, ChangePasswordRequest } from '../types/user';

// Validation schema
const changePasswordSchema = z.object({
  new_password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

interface ChangePasswordDialogProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
  onSubmit: (data: ChangePasswordRequest) => void;
  isLoading: boolean;
}

export function ChangePasswordDialog({
  isOpen,
  user,
  onClose,
  onSubmit,
  isLoading,
}: ChangePasswordDialogProps) {
  const { t } = useTranslation();

  const methods = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      new_password: '',
      confirm_password: '',
    },
  });

  const handleSubmit = (data: ChangePasswordFormData) => {
    onSubmit({ new_password: data.new_password });
  };

  const handleClose = () => {
    methods.reset();
    onClose();
  };

  if (!user) return null;

  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={isLoading}
      >
        {t('common.cancel') || 'Cancel'}
      </Button>
      <Button
        type="submit"
        form="change-password-form"
        variant="primary"
        disabled={isLoading}
        loading={isLoading}
        leftIcon={<Key className="w-4 h-4" />}
      >
        {t('users.actions.change') || 'Change Password'}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('users.changePassword.title') || 'Change Password'}
      maxWidth="md"
      footer={footer}
    >
      <FormProvider {...methods}>
        <form id="change-password-form" onSubmit={methods.handleSubmit(handleSubmit)} className="p-6 space-y-4">
          {/* User info */}
          <div className="mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('users.changePassword.user') || 'User'}: <span className="font-medium text-gray-900 dark:text-white">{user.username}</span>
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('users.changePassword.email') || 'Email'}: <span className="font-medium text-gray-900 dark:text-white">{user.email}</span>
            </p>
          </div>

          {/* New password */}
          <FormInput
            name="new_password"
            type="password"
            label={t('users.changePassword.newPassword') || 'New Password'}
            placeholder={t('users.changePassword.newPasswordPlaceholder') || 'Enter new password'}
            autoComplete="new-password"
          />

          {/* Confirm password */}
          <FormInput
            name="confirm_password"
            type="password"
            label={t('users.changePassword.confirmPassword') || 'Confirm Password'}
            placeholder={t('users.changePassword.confirmPasswordPlaceholder') || 'Re-enter new password'}
            autoComplete="new-password"
          />

          {/* Password requirements */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('users.changePassword.requirements') || 'Password Requirements:'}
            </p>
            <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <li>• {t('users.changePassword.minLength') || 'At least 8 characters'}</li>
              <li>• {t('users.changePassword.uppercase') || 'One uppercase letter'}</li>
              <li>• {t('users.changePassword.lowercase') || 'One lowercase letter'}</li>
              <li>• {t('users.changePassword.number') || 'One number'}</li>
            </ul>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}

export default ChangePasswordDialog;
