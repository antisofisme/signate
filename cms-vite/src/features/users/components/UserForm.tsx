/**
 * User Form Component
 *
 * Form for creating/editing users
 * Following CMS UI Development skill standards
 */

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, UserPlus, Save } from 'lucide-react';
import { USER_ROLES } from '@/lib/constants/app';
import { Button, Modal, FormInput, FormSelect, FormSwitch } from '@/shared/components';
import type { User, CreateUserRequest, UpdateUserRequest } from '../types/user';

// Role options
const roleOptions = [
  { value: USER_ROLES.SUPER_ADMIN, label: 'Super Admin' },
  { value: USER_ROLES.ADMIN, label: 'Admin' },
  { value: USER_ROLES.MANAGER, label: 'Manager' },
  { value: USER_ROLES.VIEWER, label: 'Viewer' },
];

// Validation schemas
const baseSchema = {
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores, and hyphens'),
  email: z
    .string()
    .email('Invalid email address')
    .max(100, 'Email must be less than 100 characters'),
  full_name: z
    .string()
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name must be less than 100 characters')
    .optional()
    .or(z.literal('')),
  role: z.enum([USER_ROLES.SUPER_ADMIN, USER_ROLES.ADMIN, USER_ROLES.MANAGER, USER_ROLES.VIEWER] as const),
  organization_id: z.string().min(1, 'Please select an organization'), // String for form, converted to number on submit
};

const createUserSchema = z.object({
  ...baseSchema,
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
});

const updateUserSchema = z.object({
  ...baseSchema,
  is_active: z.boolean(),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;
type UpdateUserFormData = z.infer<typeof updateUserSchema>;

interface UserFormProps {
  user?: User;
  organizations: Array<{ id: number; name: string }>;
  onClose: () => void;
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => void;
  isLoading: boolean;
}

export function UserForm({ user, organizations, onClose, onSubmit, isLoading }: UserFormProps) {
  const { t } = useTranslation();
  const isEditing = !!user;

  // Organization options
  const organizationOptions = organizations.map(org => ({
    value: org.id.toString(),
    label: org.name,
  }));

  // Form setup
  const methods = useForm<CreateUserFormData | UpdateUserFormData>({
    resolver: zodResolver(isEditing ? updateUserSchema : createUserSchema),
    defaultValues: isEditing
      ? {
          username: user.username,
          email: user.email,
          full_name: user.full_name || '',
          role: user.role,
          organization_id: user.organization_id.toString(),
          is_active: user.is_active,
        }
      : {
          username: '',
          email: '',
          full_name: '',
          password: '',
          role: USER_ROLES.VIEWER,
          organization_id: organizations[0]?.id.toString() || '0',
        },
  });

  const handleSubmit = (data: CreateUserFormData | UpdateUserFormData) => {
    if (isEditing) {
      // For update, we only send email, full_name, role, is_active
      const editData = data as UpdateUserFormData;
      const updateData: UpdateUserRequest = {
        email: editData.email,
        full_name: editData.full_name || undefined,
        role: editData.role,
        is_active: editData.is_active,
      };
      onSubmit(updateData);
    } else {
      // For create, we need all fields including organization_id as number
      const createData = data as CreateUserFormData;
      const formData: CreateUserRequest = {
        username: createData.username,
        email: createData.email,
        password: createData.password,
        full_name: createData.full_name || '',
        role: createData.role,
        organization_id: Number(createData.organization_id),
      };
      onSubmit(formData);
    }
  };

  const handleClose = () => {
    methods.reset();
    onClose();
  };

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title={
        isEditing
          ? t('users.form.editUser') || 'Edit User'
          : t('users.form.createUser') || 'Create User'
      }
      maxWidth="2xl"
    >
      <FormProvider {...methods}>
        <form onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-4">
          {/* Username */}
          <FormInput
            name="username"
            label={t('users.form.username') || 'Username'}
            placeholder={t('users.form.usernamePlaceholder') || 'Enter username'}
            disabled={isEditing} // Username cannot be changed
            autoComplete="username"
          />

          {/* Email */}
          <FormInput
            name="email"
            type="email"
            label={t('users.form.email') || 'Email'}
            placeholder={t('users.form.emailPlaceholder') || 'Enter email address'}
            autoComplete="email"
          />

          {/* Full Name */}
          <FormInput
            name="full_name"
            label={t('users.form.fullName') || 'Full Name'}
            placeholder={t('users.form.fullNamePlaceholder') || 'Enter full name (optional)'}
            autoComplete="name"
          />

          {/* Password (create only) */}
          {!isEditing && (
            <FormInput
              name="password"
              type="password"
              label={t('users.form.password') || 'Password'}
              placeholder={t('users.form.passwordPlaceholder') || 'Enter password'}
              autoComplete="new-password"
              description={t('users.form.passwordHelp') || 'Min 8 characters, at least 1 uppercase, 1 lowercase, and 1 number'}
            />
          )}

          {/* Role */}
          <FormSelect
            name="role"
            label={t('users.form.role') || 'Role'}
            options={roleOptions}
            placeholder={t('users.form.selectRole') || 'Select role'}
          />

          {/* Organization */}
          <FormSelect
            name="organization_id"
            label={t('users.form.organization') || 'Organization'}
            options={organizationOptions}
            placeholder={t('users.form.selectOrganization') || 'Select organization'}
          />

          {/* Active Status (edit only) */}
          {isEditing && (
            <FormSwitch
              name="is_active"
              label={t('users.form.activeLabel') || 'Active User'}
              description={t('users.form.activeHelp') || 'Inactive users cannot log in'}
            />
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
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
              variant="primary"
              disabled={isLoading}
              loading={isLoading}
              leftIcon={isEditing ? <Save className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
            >
              {isEditing ? (t('users.actions.update') || 'Update User') : (t('users.actions.create') || 'Create User')}
            </Button>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}

export default UserForm;
