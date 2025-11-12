/**
 * User Form Component
 *
 * Form for creating/editing users (simplified)
 */

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import type { User, CreateUserRequest, UpdateUserRequest } from '../types/user';

interface UserFormProps {
  user?: User;
  organizations: any[];
  onClose: () => void;
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => void;
  isLoading: boolean;
}

export function UserForm({ user, organizations, onClose, onSubmit, isLoading }: UserFormProps) {
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState(user?.role || 'viewer');
  const [orgId, setOrgId] = useState(user?.organization_id || organizations[0]?.id || 0);
  const [isActive, setIsActive] = useState(user?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (user) {
      onSubmit({ username, email, full_name: fullName, role, organization_id: orgId, is_active: isActive } as UpdateUserRequest);
    } else {
      onSubmit({ username, email, full_name: fullName, password, role, organization_id: orgId } as CreateUserRequest);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl my-8">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {user ? 'Edit User' : 'Create User'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required placeholder="Username" className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg" />
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="Email" className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg" />
          <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full Name" className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg" />
          {!user && <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Password" className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg" />}
          <select value={role} onChange={(e) => setRole(e.target.value as any)} className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg">
            <option value="super_admin">Super Admin</option>
            <option value="admin">Admin</option>
            <option value="editor">Editor</option>
            <option value="viewer">Viewer</option>
          </select>
          <select value={orgId} onChange={(e) => setOrgId(parseInt(e.target.value))} className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg">
            {organizations.map(org => <option key={org.id} value={org.id}>{org.name}</option>)}
          </select>
          {user && (
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="w-4 h-4" />
              <label className="text-sm text-gray-700 dark:text-gray-300">Active</label>
            </div>
          )}
          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancel</button>
            <button type="submit" disabled={isLoading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
              {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" />Saving...</> : user ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UserForm;
