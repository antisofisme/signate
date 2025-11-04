/**
 * Organization Selector Component
 * Menampilkan daftar organisasi untuk dipilih user
 */

import { useSelectOrganization } from '@/features/auth/hooks/useAuth';
import { useAuthStore } from '@/lib/stores/authStore';
import { formatDate } from '@/lib/utils/dateTime';

export function OrgSelector() {
  const { organizations } = useAuthStore();
  const selectOrganization = useSelectOrganization();

  if (organizations.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Tidak ada organisasi tersedia</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Pilih Organisasi</h2>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {organizations.map((org) => (
          <button
            key={org.id}
            onClick={() => selectOrganization(org.id)}
            disabled={!org.is_active}
            className={`
              p-6 rounded-lg border-2 text-left transition-all
              ${
                org.is_active
                  ? 'border-gray-300 hover:border-blue-500 hover:shadow-lg cursor-pointer bg-white'
                  : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
              }
            `}
          >
            {/* Organization Name */}
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{org.name}</h3>
              {!org.is_active && (
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                  Inactive
                </span>
              )}
            </div>

            {/* Organization PIN */}
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                PIN: <span className="font-mono font-semibold">{org.organization_pin}</span>
              </p>
            </div>

            {/* Created Date */}
            <div className="text-xs text-gray-500">
              Dibuat: {formatDate(org.created_at)}
            </div>

            {/* Active Status Indicator */}
            {org.is_active && (
              <div className="mt-4 text-blue-600 font-medium text-sm flex items-center">
                <svg
                  className="w-5 h-5 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                Pilih organisasi ini
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Info Text */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-sm text-blue-800">
          <strong>Info:</strong> Pilih organisasi untuk melanjutkan ke dashboard.
          Anda dapat mengganti organisasi kapan saja dari menu navigasi.
        </p>
      </div>
    </div>
  );
}
