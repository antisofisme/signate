/**
 * Users Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for user management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '@/features/users/api/usersApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';
import { useSelectedOrgId, userKeys } from '@/shared/hooks';
import type {
  CreateUserRequest,
  UpdateUserRequest,
  ChangePasswordRequest,
  UserListFilters,
} from '../types/user';

// Export user keys for use in other components
export { userKeys };

/**
 * Get all users with filters
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export function useUsers(filters?: UserListFilters) {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: userKeys.list(orgId, filters),
    queryFn: () => usersApi.list(filters),
    staleTime: 1 * 60 * 1000, // 1 minute
    enabled: !!orgId, // Only fetch when organization is selected
  });
}

/**
 * Get single user
 */
export function useUser(id: number) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: () => usersApi.get(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!id && id > 0,
  });
}

/**
 * Create user mutation
 */
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData: CreateUserRequest) => usersApi.create(userData),
    onSuccess: (data) => {
      // Invalidate user list
      queryClient.invalidateQueries({ queryKey: userKeys.all });

      // Invalidate dashboard (user count changes)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      // Invalidate RBAC queries (new user may have roles)
      queryClient.invalidateQueries({ queryKey: ['roles'] });

      // Show success toast
      toast.success(`User "${data.username}" berhasil dibuat`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Update user mutation
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserRequest }) =>
      usersApi.update(id, data),
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: userKeys.all });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(variables.id) });

      // Invalidate RBAC queries (role may have changed)
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      queryClient.invalidateQueries({ queryKey: ['permissions'] });

      // Show success toast
      toast.success(`User "${data.username}" berhasil diupdate`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Change password mutation
 */
export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: ChangePasswordRequest;
    }) => usersApi.changePassword(id, data),
    onSuccess: (data, variables) => {
      // Invalidate user queries
      queryClient.invalidateQueries({ queryKey: userKeys.detail(variables.id) });

      // Show success toast
      toast.success(`Password untuk "${data.username}" berhasil diubah`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Delete user mutation
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => usersApi.delete(id),
    onSuccess: (_, id) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: userKeys.all });
      queryClient.removeQueries({ queryKey: userKeys.detail(id) });

      // Invalidate dashboard (user count changes)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      // Invalidate session queries (user's sessions are invalidated)
      queryClient.invalidateQueries({ queryKey: ['sessions'] });

      // Invalidate RBAC queries (user's roles are removed)
      queryClient.invalidateQueries({ queryKey: ['roles'] });

      // Invalidate audit logs (may reference this user)
      queryClient.invalidateQueries({ queryKey: ['audit'] });

      // Show success toast
      toast.success('User berhasil dihapus');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
