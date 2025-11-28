/**
 * Playlist Form Component
 * Form for creating/editing playlists using shared Modal and React Hook Form
 */

import { useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { Loader2, Save, Plus } from 'lucide-react';
import { Modal, Button, FormInput, FormTextarea, FormSwitch } from '@/shared/components';
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
  const isEditing = !!playlist;

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

  const handleClose = () => {
    methods.reset();
    onClose();
  };

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title={isEditing ? t('playlists.editPlaylist') : t('playlists.createPlaylist')}
      maxWidth="lg"
    >
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onFormSubmit)} className="p-6 space-y-4">
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
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={isLoading}
            >
              {t('playlists.buttons.cancel')}
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('playlists.buttons.saving')}
                </>
              ) : isEditing ? (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  {t('playlists.buttons.update')}
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  {t('playlists.buttons.create')}
                </>
              )}
            </Button>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}

export default PlaylistForm;
