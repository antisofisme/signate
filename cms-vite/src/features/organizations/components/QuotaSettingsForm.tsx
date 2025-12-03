/**
 * Quota Settings Form Component
 *
 * Admin-only form to update organization quota limits
 * Validates that new limits are not lower than current usage
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/shared/components';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  AlertTriangle,
  Save,
  Server,
  Users,
  FileText,
  HardDrive,
  Folder,
  Shield,
  Info
} from 'lucide-react';
import { useUpdateQuota } from '../hooks/useOrganizationQuota';
import type { OrganizationQuota, UpdateQuotaRequest } from '../types/organization';
import { useAuthStore } from '@/lib/stores/authStore';

// Validation schema
const quotaSchema = z.object({
  max_devices: z.coerce.number().min(1, 'Must be at least 1').max(10000, 'Maximum 10,000'),
  max_users: z.coerce.number().min(1, 'Must be at least 1').max(1000, 'Maximum 1,000'),
  max_content_items: z.coerce.number().min(1, 'Must be at least 1').max(100000, 'Maximum 100,000'),
  max_content_size_gb: z.coerce.number().min(1, 'Must be at least 1 GB').max(10000, 'Maximum 10,000 GB'),
  max_playlists: z.coerce.number().min(1, 'Must be at least 1').max(10000, 'Maximum 10,000'),
});

type QuotaFormData = z.infer<typeof quotaSchema>;

interface QuotaSettingsFormProps {
  quota: OrganizationQuota;
  organizationId: number;
}

export function QuotaSettingsForm({ quota, organizationId }: QuotaSettingsFormProps) {
  const { user } = useAuthStore();
  const updateQuotaMutation = useUpdateQuota();

  // Check if user is admin (only admins can update quotas)
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<QuotaFormData>({
    resolver: zodResolver(quotaSchema),
    defaultValues: {
      max_devices: quota.devices.max,
      max_users: quota.users.max,
      max_content_items: quota.content.max_items,
      max_content_size_gb: quota.content.max_size_gb,
      max_playlists: quota.playlists.max,
    },
  });

  // Watch all form values to show warnings
  const formValues = watch();

  // Calculate warnings for each field
  const getFieldWarning = (field: keyof QuotaFormData, currentUsage: number): string | null => {
    const newLimit = formValues[field];
    if (newLimit < currentUsage) {
      return `New limit (${newLimit}) is lower than current usage (${currentUsage})`;
    }
    return null;
  };

  const warnings = {
    devices: getFieldWarning('max_devices', quota.devices.current),
    users: getFieldWarning('max_users', quota.users.current),
    contentItems: getFieldWarning('max_content_items', quota.content.current_items),
    contentSize: Number(formValues.max_content_size_gb) < quota.content.current_size_gb
      ? `New limit (${formValues.max_content_size_gb} GB) is lower than current usage (${quota.content.current_size_gb.toFixed(2)} GB)`
      : null,
    playlists: getFieldWarning('max_playlists', quota.playlists.current),
  };

  const hasWarnings = Object.values(warnings).some(w => w !== null);

  const onSubmit = async (data: QuotaFormData) => {
    if (!isAdmin) {
      return;
    }

    // Validate that new limits are not lower than current usage
    if (hasWarnings) {
      // Show confirmation if there are warnings
      const confirmed = window.confirm(
        'Warning: You are setting limits lower than current usage. This may cause issues. Continue?'
      );
      if (!confirmed) {
        return;
      }
    }

    const updateData: UpdateQuotaRequest = {
      max_devices: data.max_devices,
      max_users: data.max_users,
      max_content_items: data.max_content_items,
      max_content_size_gb: data.max_content_size_gb,
      max_playlists: data.max_playlists,
    };

    await updateQuotaMutation.mutateAsync({
      orgId: organizationId,
      data: updateData,
    });
  };

  if (!isAdmin) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quota Settings</CardTitle>
          <CardDescription>Admin access required</CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <Shield className="h-4 w-4" />
            <AlertDescription>
              Only administrators can modify organization quotas. Please contact your system administrator.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-blue-600" />
          <div>
            <CardTitle>Quota Settings</CardTitle>
            <CardDescription>Configure resource limits for this organization (Admin Only)</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Global Warning */}
          {hasWarnings && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Warning: Some new limits are lower than current usage. This may prevent new resources from being created or cause service interruptions.
              </AlertDescription>
            </Alert>
          )}

          {/* Info Alert */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Changes take effect immediately. Ensure new limits align with your organization's subscription tier.
            </AlertDescription>
          </Alert>

          {/* Devices */}
          <div className="space-y-2">
            <Label htmlFor="max_devices" className="flex items-center gap-2">
              <Server className="h-4 w-4 text-blue-600" />
              Maximum Devices
            </Label>
            <Input
              id="max_devices"
              type="number"
              {...register('max_devices')}
              placeholder="e.g., 50"
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">
                Current usage: <strong>{quota.devices.current}</strong> devices
              </span>
              {warnings.devices && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {warnings.devices}
                </Badge>
              )}
            </div>
            {errors.max_devices && (
              <p className="text-xs text-red-600">{errors.max_devices.message}</p>
            )}
          </div>

          {/* Users */}
          <div className="space-y-2">
            <Label htmlFor="max_users" className="flex items-center gap-2">
              <Users className="h-4 w-4 text-purple-600" />
              Maximum Users
            </Label>
            <Input
              id="max_users"
              type="number"
              {...register('max_users')}
              placeholder="e.g., 20"
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">
                Current usage: <strong>{quota.users.current}</strong> users
              </span>
              {warnings.users && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {warnings.users}
                </Badge>
              )}
            </div>
            {errors.max_users && (
              <p className="text-xs text-red-600">{errors.max_users.message}</p>
            )}
          </div>

          {/* Content Items */}
          <div className="space-y-2">
            <Label htmlFor="max_content_items" className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-orange-600" />
              Maximum Content Items
            </Label>
            <Input
              id="max_content_items"
              type="number"
              {...register('max_content_items')}
              placeholder="e.g., 1000"
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">
                Current usage: <strong>{quota.content.current_items.toLocaleString()}</strong> items
              </span>
              {warnings.contentItems && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {warnings.contentItems}
                </Badge>
              )}
            </div>
            {errors.max_content_items && (
              <p className="text-xs text-red-600">{errors.max_content_items.message}</p>
            )}
          </div>

          {/* Storage Size */}
          <div className="space-y-2">
            <Label htmlFor="max_content_size_gb" className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-indigo-600" />
              Maximum Storage Size (GB)
            </Label>
            <Input
              id="max_content_size_gb"
              type="number"
              step="0.1"
              {...register('max_content_size_gb')}
              placeholder="e.g., 100"
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">
                Current usage: <strong>{quota.content.current_size_gb.toFixed(2)} GB</strong>
              </span>
              {warnings.contentSize && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {warnings.contentSize}
                </Badge>
              )}
            </div>
            {errors.max_content_size_gb && (
              <p className="text-xs text-red-600">{errors.max_content_size_gb.message}</p>
            )}
          </div>

          {/* Playlists */}
          <div className="space-y-2">
            <Label htmlFor="max_playlists" className="flex items-center gap-2">
              <Folder className="h-4 w-4 text-green-600" />
              Maximum Playlists
            </Label>
            <Input
              id="max_playlists"
              type="number"
              {...register('max_playlists')}
              placeholder="e.g., 100"
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">
                Current usage: <strong>{quota.playlists.current}</strong> playlists
              </span>
              {warnings.playlists && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {warnings.playlists}
                </Badge>
              )}
            </div>
            {errors.max_playlists && (
              <p className="text-xs text-red-600">{errors.max_playlists.message}</p>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <Button
              type="submit"
              disabled={!isDirty || isSubmitting || updateQuotaMutation.isPending}
              loading={isSubmitting || updateQuotaMutation.isPending}
              leftIcon={<Save className="h-4 w-4" />}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
