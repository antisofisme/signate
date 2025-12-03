/**
 * Change Password Modal Component
 *
 * RHF-based modal for changing user password
 * Uses shared Modal and FormInput components
 */

import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Key } from 'lucide-react';
import { Modal, Button, FormInput } from '@/shared/components';
import type { User } from '../types/user';

// Validation schema
const changePasswordSchema = z.object({
  new_password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirm_password: z.string().min(1, 'Please confirm the password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

interface ChangePasswordModalProps {
  isOpen: boolean;
  user: User;
  onClose: () => void;
  onSubmit: (newPassword: string) => void;
  isLoading: boolean;
}

export function ChangePasswordModal({
  isOpen,
  user,
  onClose,
  onSubmit,
  isLoading,
}: ChangePasswordModalProps) {
  const methods = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      new_password: '',
      confirm_password: '',
    },
  });

  const handleSubmit = (data: ChangePasswordFormData) => {
    onSubmit(data.new_password);
  };

  const handleClose = () => {
    methods.reset();
    onClose();
  };

  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={isLoading}
      >
        Cancel
      </Button>
      <Button
        type="submit"
        form="change-password-form"
        variant="primary"
        disabled={isLoading}
        loading={isLoading}
        leftIcon={<Key className="w-4 h-4" />}
      >
        Change Password
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Change Password"
      subtitle={`${user.full_name} (@${user.username})`}
      maxWidth="md"
      footer={footer}
    >
      <FormProvider {...methods}>
        <form
          id="change-password-form"
          onSubmit={methods.handleSubmit(handleSubmit)}
          className="p-6 space-y-4"
        >
          <FormInput
            name="new_password"
            type="password"
            label="New Password"
            placeholder="Enter new password"
            autoComplete="new-password"
            description="Min 8 characters, at least 1 uppercase, 1 lowercase, and 1 number"
          />

          <FormInput
            name="confirm_password"
            type="password"
            label="Confirm Password"
            placeholder="Confirm new password"
            autoComplete="new-password"
          />
        </form>
      </FormProvider>
    </Modal>
  );
}

export default ChangePasswordModal;
