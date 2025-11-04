/**
 * Users Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for user management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '@/features/users/services/usersApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';
import type {
  CreateUserRequest,
  UpdateUserRequest,
  ChangePasswordRequest,
  UserListFilters,
} from '../types/user';

/**
 * Get all users with filters
 */
export function useUsers(filters?: UserListFilters) {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => usersApi.list(filters),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Get single user
 */
export function useUser(id: number) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => usersApi.get(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!id,
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
      queryClient.invalidateQueries({ queryKey: ['users'] });

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
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['users', variables.id] });

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
      queryClient.invalidateQueries({ queryKey: ['users', variables.id] });

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
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.removeQueries({ queryKey: ['users', id] });

      // Show success toast
      toast.success('User berhasil dihapus');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
