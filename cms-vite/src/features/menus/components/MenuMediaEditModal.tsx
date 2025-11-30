/**
 * Menu Media Edit Modal Component
 */

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm } from 'react-hook-form';
import { X, Loader2 } from 'lucide-react';
import { Button } from '@/shared/components';
import { useUpdateMenuMedia } from '../hooks/useMenuMedia';
import type { MenuMedia } from '../types/menu';

interface MenuMediaEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  media: MenuMedia | null;
}

interface FormData {
  title: string;
  alt_text: string;
}

export function MenuMediaEditModal({ isOpen, onClose, media }: MenuMediaEditModalProps) {
  const { t } = useTranslation();
  const updateMutation = useUpdateMenuMedia();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      title: '',
      alt_text: '',
    },
  });

  // Reset form when media changes
  useEffect(() => {
    if (media) {
      reset({
        title: media.title || '',
        alt_text: media.alt_text || '',
      });
    }
  }, [media, reset]);

  const onSubmit = async (data: FormData) => {
    if (!media) return;

    await updateMutation.mutateAsync({
      id: media.id,
      data: {
        title: data.title || undefined,
        alt_text: data.alt_text || undefined,
      },
    });
    onClose();
  };

  if (!isOpen || !media) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Image Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="p-6 space-y-4">
            {/* Preview */}
            <div className="flex items-center gap-4">
              <img
                src={media.url}
                alt={media.alt_text || media.original_filename}
                className="w-20 h-20 rounded-lg object-cover"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {media.original_filename}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {media.width}x{media.height} - {media.mime_type}
                </p>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Title
              </label>
              <input
                {...register('title')}
                type="text"
                placeholder="Enter a title for this image"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Alt Text */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Alt Text
              </label>
              <textarea
                {...register('alt_text')}
                rows={3}
                placeholder="Describe this image for accessibility"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Alt text helps users who use screen readers understand the image content.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <Button variant="secondary" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={updateMutation.isPending}
              leftIcon={updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
