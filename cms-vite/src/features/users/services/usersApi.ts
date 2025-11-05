/**
 * Users API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all user management API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  ChangePasswordRequest,
  UserListData,
  UserListFilters,
  UserResponse,
  UserListResponse,
} from '../types/user';

export const usersApi = {
  /**
   * Get all users with filters
   * @param filters - Filter options
   * @returns List of users with stats
   */
  list: async (filters?: UserListFilters): Promise<UserListData> => {
    const params = new URLSearchParams();

    if (filters?.organization_id) {
      params.append('organization_id', filters.organization_id.toString());
    }
    if (filters?.role) {
      params.append('role', filters.role);
    }
    if (filters?.active_only) {
      params.append('active_only', 'true');
    }

    const { data } = await apiClient.get<UserListData>(
      `${API_ENDPOINTS.USERS.LIST}?${params.toString()}`
    );
    return data;
  },

  /**
   * Get user by ID
   * @param id - User ID
   * @returns User with organization name
   */
  get: async (id: number): Promise<User> => {
    const { data } = await apiClient.get<User>(
      API_ENDPOINTS.USERS.GET(id)
    );
    return data;
  },

  /**
   * Create new user
   * @param userData - User data
   * @returns Created user
   */
  create: async (userData: CreateUserRequest): Promise<User> => {
    const { data } = await apiClient.post<User>(
      API_ENDPOINTS.USERS.CREATE,
      userData
    );
    return data;
  },

  /**
   * Update user
   * @param id - User ID
   * @param userData - Updated user data
   * @returns Updated user
   */
  update: async (id: number, userData: UpdateUserRequest): Promise<User> => {
    const { data } = await apiClient.put<User>(
      API_ENDPOINTS.USERS.UPDATE(id),
      userData
    );
    return data;
  },

  /**
   * Change user password
   * @param id - User ID
   * @param passwordData - New password
   * @returns Updated user
   */
  changePassword: async (
    id: number,
    passwordData: ChangePasswordRequest
  ): Promise<User> => {
    const { data } = await apiClient.put<User>(
      API_ENDPOINTS.USERS.CHANGE_PASSWORD(id),
      passwordData
    );
    return data;
  },

  /**
   * Delete user (soft delete)
   * @param id - User ID
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.USERS.DELETE(id));
  },
};
