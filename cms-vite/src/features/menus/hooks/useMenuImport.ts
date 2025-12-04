/**
 * React Query Hooks for Menu Excel Import/Export
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/shared/utils/toast';
import { menuApi } from '../api/menuApi';
import { menuKeys } from './useMenus';
import { getApiErrorMessage } from '@/shared/utils/types';

// ========== Import History Query ==========

/**
 * Hook to get import history
 */
export const useMenuImportHistory = (menuId: number) => {
  return useQuery({
    queryKey: menuKeys.importHistory(menuId),
    queryFn: () => menuApi.getImportHistory(menuId),
    enabled: !!menuId,
  });
};

// ========== Import/Export Mutations ==========

/**
 * Hook to import menu items from Excel
 */
export const useImportMenuItems = (menuId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, replaceExisting }: { file: File; replaceExisting: boolean }) =>
      menuApi.importExcel(menuId, file, replaceExisting),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: menuKeys.items(menuId) });
      queryClient.invalidateQueries({ queryKey: menuKeys.detail(menuId) });
      queryClient.invalidateQueries({ queryKey: menuKeys.importHistory(menuId) });

      if (result.status === 'success') {
        toast.success(`Successfully imported ${result.rows_success} items`);
      } else if (result.status === 'partial') {
        toast.warning(
          `Imported ${result.rows_success} items, ${result.rows_failed} failed`
        );
      } else {
        toast.error('Import failed. Please check the file format.');
      }
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to import Excel file'));
    },
  });
};

/**
 * Hook to download Excel template
 */
export const useDownloadTemplate = () => {
  return useMutation({
    mutationFn: () => menuApi.downloadTemplate(),
    onSuccess: (blob) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'menu_template.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('Template downloaded successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to download template'));
    },
  });
};

/**
 * Hook to export menu to Excel
 */
export const useExportMenu = () => {
  return useMutation({
    mutationFn: ({ menuId, menuName }: { menuId: number; menuName: string }) =>
      menuApi.exportMenu(menuId).then((blob) => ({ blob, menuName })),
    onSuccess: ({ blob, menuName }) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${menuName.toLowerCase().replace(/\s+/g, '_')}_export.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('Menu exported successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to export menu'));
    },
  });
};

/**
 * Hook to download QR code
 */
export const useDownloadQRCode = () => {
  return useMutation({
    mutationFn: ({ menuId, menuName }: { menuId: number; menuName: string }) =>
      menuApi.downloadQRCode(menuId).then((blob) => ({ blob, menuName })),
    onSuccess: ({ blob, menuName }) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${menuName.toLowerCase().replace(/\s+/g, '_')}_qr.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('QR code downloaded successfully');
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to download QR code'));
    },
  });
};
