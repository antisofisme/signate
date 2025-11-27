/**
 * Tag List Component
 * Table display of tags with actions
 */

import { Pencil, Trash2, Tag as TagIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState } from '@/shared/components';
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
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('tags.tag')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('tags.description')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('tags.created')}
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('tags.actions')}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {tags.map((tag) => (
            <tr key={tag.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td className="px-6 py-4 whitespace-nowrap">
                <TagBadge tag={tag} />
              </td>
              <td className="px-6 py-4 text-gray-700 dark:text-gray-300">
                {tag.description || '-'}
              </td>
              <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                {new Date(tag.created_at).toLocaleDateString('id-ID')}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="flex items-center justify-end gap-2">
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
