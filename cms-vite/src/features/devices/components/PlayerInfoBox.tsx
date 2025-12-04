/**
 * Player Info Box Component
 * Displays the player URL for device registration
 */

import { useState } from 'react';
import { Monitor, Copy, Check, ExternalLink, Info } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { toast } from '@/shared/utils/toast';

// Get player URL from environment
const PLAYER_URL = import.meta.env.VITE_PLAYER_URL || 'https://player.zhmhotels.online';

export function PlayerInfoBox() {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(PLAYER_URL);
      setCopied(true);
      toast.success(t('devices.player.copied', 'Link player berhasil disalin!'));
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error(t('devices.player.copyFailed', 'Gagal menyalin link'));
    }
  };

  const handleOpenPlayer = () => {
    window.open(PLAYER_URL, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 p-2 bg-purple-100 dark:bg-purple-800 rounded-lg">
          <Monitor className="w-5 h-5 text-purple-600 dark:text-purple-300" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-100">
              {t('devices.player.title', 'Player / Viewer URL')}
            </h3>
            <div className="group relative">
              <Info className="w-4 h-4 text-purple-400 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 w-72 p-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                {t('devices.player.tooltip', 'Buka URL ini di perangkat (TV/Monitor) untuk mendaftarkan perangkat baru. Setelah dibuka, perangkat akan menampilkan kode aktivasi 6 digit yang perlu dimasukkan di halaman Perangkat.')}
              </div>
            </div>
          </div>

          <p className="text-xs text-purple-700 dark:text-purple-300 mb-3">
            {t('devices.player.description', 'Akses URL ini dari TV/Monitor untuk registrasi perangkat baru')}
          </p>

          {/* URL Display */}
          <div className="flex items-center gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-purple-200 dark:border-purple-700 rounded-md px-3 py-2">
                <input
                  type="text"
                  value={PLAYER_URL}
                  readOnly
                  className="flex-1 min-w-0 bg-transparent text-sm text-gray-700 dark:text-gray-200 focus:outline-none truncate"
                />
              </div>
            </div>

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="flex-shrink-0 p-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors"
              title={t('devices.player.copy', 'Salin link')}
            >
              {copied ? (
                <Check className="w-4 h-4" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>

            {/* Open in New Tab */}
            <button
              onClick={handleOpenPlayer}
              className="flex-shrink-0 p-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md transition-colors"
              title={t('devices.player.open', 'Buka player')}
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Steps */}
          <div className="mt-3 text-xs text-purple-600 dark:text-purple-400">
            <p className="font-medium mb-1">{t('devices.player.steps.title', 'Langkah registrasi:')}</p>
            <ol className="list-decimal list-inside space-y-0.5 text-purple-500 dark:text-purple-400">
              <li>{t('devices.player.steps.step1', 'Buka URL di atas pada TV/Monitor')}</li>
              <li>{t('devices.player.steps.step2', 'Catat kode aktivasi 6 digit yang muncul')}</li>
              <li>{t('devices.player.steps.step3', 'Masukkan kode di halaman Perangkat > Daftarkan TV/Monitor')}</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
