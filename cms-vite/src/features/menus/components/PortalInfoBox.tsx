/**
 * Portal Info Box Component
 * Displays the unified menu portal URL for the current organization
 */

import { useState } from 'react';
import { Link2, Copy, Check, ExternalLink, Info, Download, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import QRCode from 'qrcode';
import { useCurrentOrganization } from '@/features/auth/hooks/useAuth';
import { generatePortalSlug } from '@/features/auth/types/auth';

// Get player URL from environment
const PLAYER_URL = import.meta.env.VITE_PLAYER_URL || 'https://player.zhmhotels.online';

export function PortalInfoBox() {
  const { t } = useTranslation();
  const organization = useCurrentOrganization();
  const [copied, setCopied] = useState(false);
  const [isDownloadingQR, setIsDownloadingQR] = useState(false);

  if (!organization) {
    return null;
  }

  // Generate portal slug (use from backend if available, otherwise generate)
  const portalSlug = organization.portal_slug || generatePortalSlug(organization.name, organization.id);
  const portalUrl = `${PLAYER_URL}/portal/${portalSlug}`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(portalUrl);
      setCopied(true);
      toast.success(t('menus.portal.copied', 'Link portal berhasil disalin!'));
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error(t('menus.portal.copyFailed', 'Gagal menyalin link'));
    }
  };

  const handleOpenPortal = () => {
    window.open(portalUrl, '_blank', 'noopener,noreferrer');
  };

  const handleDownloadQR = async () => {
    try {
      setIsDownloadingQR(true);

      // Generate QR code as data URL
      const dataUrl = await QRCode.toDataURL(portalUrl, {
        width: 512,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      });

      // Create download link
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `portal_${portalSlug}_qr.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast.success(t('menus.portal.qrDownloaded', 'QR Code berhasil diunduh!'));
    } catch (error) {
      console.error('Failed to generate QR code:', error);
      toast.error(t('menus.portal.qrFailed', 'Gagal mengunduh QR Code'));
    } finally {
      setIsDownloadingQR(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 p-2 bg-blue-100 dark:bg-blue-800 rounded-lg">
          <Link2 className="w-5 h-5 text-blue-600 dark:text-blue-300" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100">
              {t('menus.portal.title', 'Menu Portal')}
            </h3>
            <div className="group relative">
              <Info className="w-4 h-4 text-blue-400 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                {t('menus.portal.tooltip', 'Bagikan link ini agar pelanggan dapat melihat semua menu Anda dalam satu halaman dengan navigasi tab.')}
              </div>
            </div>
          </div>

          <p className="text-xs text-blue-700 dark:text-blue-300 mb-3">
            {t('menus.portal.description', 'Satu link untuk semua menu organisasi Anda')}
          </p>

          {/* URL Display */}
          <div className="flex items-center gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded-md px-3 py-2">
                <input
                  type="text"
                  value={portalUrl}
                  readOnly
                  className="flex-1 min-w-0 bg-transparent text-sm text-gray-700 dark:text-gray-200 focus:outline-none truncate"
                />
              </div>
            </div>

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="flex-shrink-0 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              title={t('menus.portal.copy', 'Salin link')}
            >
              {copied ? (
                <Check className="w-4 h-4" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>

            {/* Open in New Tab */}
            <button
              onClick={handleOpenPortal}
              className="flex-shrink-0 p-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md transition-colors"
              title={t('menus.portal.open', 'Buka portal')}
            >
              <ExternalLink className="w-4 h-4" />
            </button>

            {/* Download QR Code */}
            <button
              onClick={handleDownloadQR}
              disabled={isDownloadingQR}
              className="flex-shrink-0 p-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={t('menus.portal.downloadQR', 'Download QR Code')}
            >
              {isDownloadingQR ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
