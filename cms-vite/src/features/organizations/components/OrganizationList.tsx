/**
 * Organization List Component
 *
 * LAYER 1: PRESENTATION
 * Table display of organizations with actions
 */

import { Building, Shield, Edit, Trash2, Users, Monitor, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { EmptyState, Button, TABLE_STYLES } from '@/shared/components';
import type { Organization } from '../types/organization';

interface OrganizationListProps {
  organizations: Organization[];
  onEdit?: (org: Organization) => void;
  onDelete?: (org: Organization) => void;
}

export function OrganizationList({
  organizations,
  onEdit,
  onDelete,
}: OrganizationListProps) {
  const { t } = useTranslation();

  // Show empty state if no organizations
  if (!organizations || organizations.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <EmptyState
          icon={Building}
          title={t('organizations.noOrganizations', 'No organizations')}
          description={t('organizations.noOrganizationsDescription', 'There are no organizations yet. Create your first organization to get started.')}
        />
      </div>
    );
  }

  return (
    <div className={TABLE_STYLES.container}>
      <table className={TABLE_STYLES.table}>
        <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={TABLE_STYLES.th}>
              {t('organizations.name')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('organizations.status')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('organizations.users')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('organizations.devices')}
            </th>
            {(onEdit || onDelete) && (
              <th className={TABLE_STYLES.th}>
                {t('organizations.actions')}
              </th>
            )}
          </tr>
        </thead>
        <tbody className={TABLE_STYLES.tbody}>
          {organizations.map((org) => (
            <tr key={org.id} className={TABLE_STYLES.tr}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <Building className="w-5 h-5 text-gray-400 mr-2" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {org.name}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    org.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}
                >
                  {org.is_active ? t('organizations.active') : t('organizations.inactive')}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Users className="w-4 h-4 mr-1" />
                  {org.user_count || 0}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Monitor className="w-4 h-4 mr-1" />
                  {org.device_count || 0}
                </div>
              </td>
              {(onEdit || onDelete) && (
                <td className={TABLE_STYLES.td}>
                  <div className="flex items-center gap-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(org)}
                        className={TABLE_STYLES.actionBtnBlue}
                        title={t('organizations.editOrganization', 'Edit organization')}
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => onDelete(org)}
                        className={TABLE_STYLES.actionBtnRed}
                        title={t('organizations.deleteOrganization', 'Delete organization')}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default OrganizationList;
