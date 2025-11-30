/**
 * UploadList Component
 *
 * Displays the list of upload items in the queue
 */

import { useTranslation } from 'react-i18next';
import { UploadItem } from './UploadItem';
import type { UploadItem as UploadItemType } from '../types/upload';

interface UploadListProps {
  items: UploadItemType[];
  maxHeight?: string;
}

export function UploadList({ items, maxHeight = '300px' }: UploadListProps) {
  const { t } = useTranslation();

  if (items.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
        {t('uploads.queue.empty', 'No uploads in queue')}
      </div>
    );
  }

  return (
    <div
      className="overflow-y-auto"
      style={{ maxHeight }}
    >
      {items.map((item) => (
        <UploadItem key={item.id} item={item} />
      ))}
    </div>
  );
}
