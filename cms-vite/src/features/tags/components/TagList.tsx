/**
 * Tag List Component
 * Table display of tags with actions
 */

import { Pencil, Trash2, Tag as TagIcon, FileSymlink, Monitor, File } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState, TABLE_STYLES, SortableTableHeader } from '@/shared/components';
import type { SortConfig } from '@/shared/components';
import { TagBadge } from './TagBadge';
import type { Tag } from '../types/tag';

interface TagListProps {
  tags: Tag[];
  isLoading: boolean;
  searchQuery: string;
  onEdit?: (tag: Tag) => void;
  onDelete?: (tag: Tag) => void;
  onManageContent?: (tag: Tag) => void;
  // Sorting props (optional - controlled by parent)
  sortConfig?: SortConfig | null;
  onSortChange?: (config: SortConfig | null) => void;
}

export function TagList({
  tags,
  isLoading,
  searchQuery,
  onEdit,
  onDelete,
  onManageContent,
  sortConfig,
  onSortChange,
}: TagListProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return <TableSkeleton columns={6} rows={5} />;
  }

  if (tags.length === 0) {
    return (
      <EmptyState
        icon={TagIcon}
        title={searchQuery ? t('tags.noTagsMatch') : t('tags.noTagsYet')}
        description={searchQuery ? '' : t('tags.createFirstTag') || ''}
      />
    );
  }

  return (
    <div className={TABLE_STYLES.container}>
      <div className="overflow-x-auto">
        <table className={`${TABLE_STYLES.table} table-fixed`}>
        <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={`${TABLE_STYLES.th} w-[20%]`}>
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="tag_name"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('tags.tag')}
                </SortableTableHeader>
              ) : (
                t('tags.tag')
              )}
            </th>
            <th className={`${TABLE_STYLES.th} w-[25%]`}>
              {t('tags.description')}
            </th>
            <th className={`${TABLE_STYLES.th} w-24 text-center`}>
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="content_count"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('tags.contentCount', 'Contents')}
                </SortableTableHeader>
              ) : (
                t('tags.contentCount', 'Contents')
              )}
            </th>
            <th className={`${TABLE_STYLES.th} w-24 text-center`}>
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="device_count"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('tags.deviceCount', 'Devices')}
                </SortableTableHeader>
              ) : (
                t('tags.deviceCount', 'Devices')
              )}
            </th>
            <th className={`${TABLE_STYLES.th} w-28`}>
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="created_at"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('tags.created')}
                </SortableTableHeader>
              ) : (
                t('tags.created')
              )}
            </th>
            <th className={`${TABLE_STYLES.th} w-32`}>
              {t('tags.actions')}
            </th>
          </tr>
        </thead>
        <tbody className={TABLE_STYLES.tbody}>
          {tags.map((tag) => (
            <tr key={tag.id} className={TABLE_STYLES.tr}>
              <td className={TABLE_STYLES.td}>
                <TagBadge tag={tag} />
              </td>
              <td className={TABLE_STYLES.td}>
                {tag.description || '-'}
              </td>
              <td className={`${TABLE_STYLES.td} text-center`}>
                <div className="flex items-center justify-center gap-1.5">
                  <File className="h-4 w-4 text-gray-400" />
                  <span className={(tag.content_count ?? 0) > 0 ? 'font-medium' : 'text-gray-400'}>
                    {tag.content_count ?? 0} {t('tags.contentSuffix', 'konten')}
                  </span>
                </div>
              </td>
              <td className={`${TABLE_STYLES.td} text-center`}>
                <div className="flex items-center justify-center gap-1.5">
                  <Monitor className="h-4 w-4 text-gray-400" />
                  <span className={(tag.device_count ?? 0) > 0 ? 'font-medium' : 'text-gray-400'}>
                    {tag.device_count ?? 0} {t('tags.deviceSuffix', 'device')}
                  </span>
                </div>
              </td>
              <td className={`${TABLE_STYLES.td} ${TABLE_STYLES.muted}`}>
                {new Date(tag.created_at).toLocaleDateString('id-ID')}
              </td>
              <td className={TABLE_STYLES.td}>
                <div className="flex items-center gap-2">
                  {onManageContent && (
                    <button
                      onClick={() => onManageContent(tag)}
                      className={TABLE_STYLES.actionBtnGreen}
                      title={t('tags.manageContent', 'Manage Content')}
                    >
                      <FileSymlink className="h-4 w-4" />
                    </button>
                  )}
                  {onEdit && (
                    <button
                      onClick={() => onEdit(tag)}
                      className={TABLE_STYLES.actionBtnBlue}
                      title={t('tags.edit')}
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(tag)}
                      className={TABLE_STYLES.actionBtnRed}
                      title={t('tags.delete')}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                  {!onEdit && !onDelete && !onManageContent && (
                    <span className="text-sm text-gray-400 dark:text-gray-500">-</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </div>
  );
}

export default TagList;
