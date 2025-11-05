/**
 * Dashboard Page
 *
 * LAYER 1: PRESENTATION
 */

import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/lib/stores/authStore';
import { PageHeader } from '@/shared/components';

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  return (
    <>
      {/* Sticky Page Header */}
      <PageHeader
        title={t('dashboard.title')}
        description={`${t('dashboard.welcome')}, ${user?.full_name || user?.username}!`}
      />

      {/* Content */}
      <div className="space-y-6">

        {/* Stats Grid - Placeholder */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
              {t('dashboard.totalDevices')}
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              0
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
              {t('dashboard.activeContent')}
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              0
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
              {t('navigation.playlists')}
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              0
            </p>
          </div>
        </div>

        {/* User Info */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mt-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {t('dashboard.userInfo')}
          </h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {t('dashboard.username')}
              </dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">
                {user?.username}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {t('dashboard.email')}
              </dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">
                {user?.email || t('dashboard.notAvailable')}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {t('dashboard.role')}
              </dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                  {user?.role}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {t('dashboard.status')}
              </dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                  {user?.is_active ? t('dashboard.active') : t('dashboard.inactive')}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </>
  );
}
