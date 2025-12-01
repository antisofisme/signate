/**
 * Tag List Component
 * Table display of tags with actions
 */

import { Pencil, Trash2, Tag as TagIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState, TABLE_STYLES } from '@/shared/components';
import { TagBadge } from './TagBadge';
import type { Tag } from '../types/tag';

interface TagListProps {
  tags: Tag[];
  isLoading: boolean;
  searchQuery: string;
  onEdit?: (tag: Tag) => void;
  onDelete?: (tag: Tag) => void;
}

export function TagList({
  tags,
  isLoading,
  searchQuery,
  onEdit,
  onDelete,
}: TagListProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return <TableSkeleton columns={4} rows={5} />;
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
      <table className={TABLE_STYLES.table}>
        <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={TABLE_STYLES.th}>
              {t('tags.tag')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('tags.description')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('tags.created')}
            </th>
            <th className={TABLE_STYLES.th}>
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
              <td className={`${TABLE_STYLES.td} ${TABLE_STYLES.muted}`}>
                {new Date(tag.created_at).toLocaleDateString('id-ID')}
              </td>
              <td className={TABLE_STYLES.td}>
                <div className="flex items-center gap-2">
                  {onEdit && (
                    <button
                      onClick={() => onEdit(tag)}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                      title={t('tags.edit')}
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(tag)}
                      className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                      title={t('tags.delete')}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                  {!onEdit && !onDelete && (
                    <span className="text-sm text-gray-400 dark:text-gray-500">-</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TagList;
