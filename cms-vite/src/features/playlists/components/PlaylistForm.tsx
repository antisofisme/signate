/**
 * Playlist Form Component
 * Form for creating/editing playlists
 */

import { useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { Loader2 } from 'lucide-react';
import { FormInput, FormTextarea, FormSwitch } from '@/shared/components';
import type { Playlist, CreatePlaylistRequest, UpdatePlaylistRequest } from '../types/playlist';

// Zod validation schema
const playlistSchema = z.object({
  name: z.string().min(1, 'Playlist name is required').max(200, 'Name is too long'),
  description: z.string().optional(),
  is_active: z.boolean().default(true),
  priority: z.number().int().min(0).max(100).default(0),
});

type PlaylistFormData = z.infer<typeof playlistSchema>;

interface PlaylistFormProps {
  playlist?: Playlist;
  onClose: () => void;
  onSubmit: (data: CreatePlaylistRequest | UpdatePlaylistRequest) => void;
  isLoading: boolean;
}

export function PlaylistForm({ playlist, onClose, onSubmit, isLoading }: PlaylistFormProps) {
  const { t } = useTranslation();

  const methods = useForm<PlaylistFormData>({
    resolver: zodResolver(playlistSchema),
    defaultValues: {
      name: playlist?.name || '',
      description: playlist?.description || '',
      is_active: playlist?.is_active ?? true,
      priority: playlist?.priority || 0,
    },
  });

  const { handleSubmit, reset } = methods;

  // Reset form when playlist changes
  useEffect(() => {
    if (playlist) {
      reset({
        name: playlist.name,
        description: playlist.description || '',
        is_active: playlist.is_active,
        priority: playlist.priority,
      });
    }
  }, [playlist, reset]);

  const onFormSubmit = (data: PlaylistFormData) => {
    onSubmit(data);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            {playlist ? t('playlists.editPlaylist') : t('playlists.createPlaylist')}
          </h3>

          <FormProvider {...methods}>
            <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
              {/* Name */}
              <FormInput
                name="name"
                label={t('playlists.playlistName')}
                placeholder={t('playlists.placeholders.name')}
                required
              />

              {/* Description */}
              <FormTextarea
                name="description"
                label={t('playlists.description')}
                placeholder={t('playlists.placeholders.description')}
                rows={3}
              />

              {/* Priority */}
              <FormInput
                name="priority"
                type="number"
                label={t('playlists.priority')}
                placeholder="0"
                min={0}
                max={100}
              />

              {/* Active Status */}
              <FormSwitch
                name="is_active"
                label={t('playlists.active')}
              />

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isLoading}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
                >
                  {t('playlists.buttons.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      {t('playlists.buttons.saving')}
                    </>
                  ) : (
                    <>
                      {playlist ? t('playlists.buttons.update') : t('playlists.buttons.create')}
                    </>
                  )}
                </button>
              </div>
            </form>
          </FormProvider>
        </div>
      </div>
    </div>
  );
}

export default PlaylistForm;
