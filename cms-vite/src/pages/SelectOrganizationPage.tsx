/**
 * Select Organization Page
 *
 * LAYER 1: PRESENTATION
 * Allows users with multiple organizations to select which one to use
 */

import { Building2, Check } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import { useSelectOrganization } from '@/features/auth/hooks/useAuth';

export default function SelectOrganizationPage() {
  const { organizations, selectedOrgId } = useAuthStore();
  const selectOrganization = useSelectOrganization();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-2xl w-full max-w-2xl">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
            Select Organization
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Choose which organization to manage
          </p>
        </div>

        {/* Organizations List */}
        <div className="space-y-3">
          {organizations.map((org) => (
            <button
              key={org.id}
              onClick={() => selectOrganization(org.id)}
              className={`w-full p-4 rounded-lg border-2 transition-all ${
                selectedOrgId === org.id
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-400 bg-white dark:bg-gray-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      {org.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      PIN: {org.organization_pin}
                    </p>
                  </div>
                </div>
                {selectedOrgId === org.id && (
                  <Check className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Info */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">
          You can switch organizations anytime from the settings
        </p>
      </div>
    </div>
  );
}
