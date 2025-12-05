/**
 * Organization List Component
 *
 * LAYER 1: PRESENTATION
 * Table display of organizations with actions
 */

import { Building, Pencil, Trash2, Users, Monitor } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { EmptyState, TABLE_STYLES, ACTION_BUTTON, SortableTableHeader, TableSkeleton } from '@/shared/components';
import type { SortConfig } from '@/shared/components';
import type { Organization } from '../types/organization';

interface OrganizationListProps {
  organizations: Organization[];
  isLoading?: boolean;
  onEdit?: (org: Organization) => void;
  onDelete?: (org: Organization) => void;
  // Sorting props
  sortConfig?: SortConfig | null;
  onSortChange?: (config: SortConfig | null) => void;
}

export function OrganizationList({
  organizations,
  isLoading,
  onEdit,
  onDelete,
  sortConfig,
  onSortChange,
}: OrganizationListProps) {
  const { t } = useTranslation();

  // Loading state
  if (isLoading) {
    return <TableSkeleton columns={5} rows={5} />;
  }

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
      <div className="overflow-x-auto">
        <table className={`${TABLE_STYLES.table} table-fixed`}>
          <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={`${TABLE_STYLES.th} w-[30%]`}>
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="name"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('organizations.name')}
                </SortableTableHeader>
              ) : (
                t('organizations.name')
              )}
            </th>
            <th className={`${TABLE_STYLES.th} w-20`}>
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="is_active"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('organizations.status')}
                </SortableTableHeader>
              ) : (
                t('organizations.status')
              )}
            </th>
            <th className={`${TABLE_STYLES.th} w-24`}>
              {t('organizations.users')}
            </th>
            <th className={`${TABLE_STYLES.th} w-24`}>
              {t('organizations.devices')}
            </th>
            {(onEdit || onDelete) && (
              <th className={`${TABLE_STYLES.th} w-32`}>
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
                        className={ACTION_BUTTON.EDIT}
                        title={t('organizations.editOrganization', 'Edit organization')}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => onDelete(org)}
                        className={ACTION_BUTTON.DELETE}
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
    </div>
  );
}

export default OrganizationList;
