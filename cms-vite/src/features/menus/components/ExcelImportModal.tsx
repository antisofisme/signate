/**
 * Excel Import Modal Component
 * Upload Excel file to import menu items
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title)
 * - Fixed footer (action buttons)
 * - Scrollable content (download template, upload, results)
 * - Click outside to close (disabled during import)
 */

import { useState } from 'react';
import { Upload, Download, CheckCircle, AlertCircle } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useImportMenuItems, useDownloadTemplate } from '../hooks/useMenuImport';
import type { MenuImportResult } from '../types/menu';

interface ExcelImportModalProps {
  isOpen: boolean;
  menuId: number;
  menuName: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ExcelImportModal = ({
  isOpen,
  menuId,
  menuName,
  onClose,
  onSuccess,
}: ExcelImportModalProps) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [importResult, setImportResult] = useState<MenuImportResult | null>(null);

  const importMutation = useImportMenuItems(menuId);
  const downloadTemplateMutation = useDownloadTemplate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (
        !file.name.endsWith('.xlsx') &&
        !file.name.endsWith('.xls')
      ) {
        alert('Please select an Excel file (.xlsx or .xls)');
        return;
      }
      setSelectedFile(file);
      setImportResult(null);
    }
  };

  const handleDownloadTemplate = () => {
    downloadTemplateMutation.mutate();
  };

  const handleImport = async () => {
    if (!selectedFile) return;

    try {
      const result = await importMutation.mutateAsync({
        file: selectedFile,
        replaceExisting,
      });

      setImportResult(result);

      // Auto-close on full success after 2 seconds
      if (result.status === 'success') {
        setTimeout(() => {
          onSuccess?.();
          onClose();
        }, 2000);
      }
    } catch (error) {
      // Error handled by mutation hook
    }
  };

  const handleClose = () => {
    if (!importMutation.isPending) {
      onClose();
    }
  };

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={importMutation.isPending}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          {importResult ? 'Close' : 'Cancel'}
        </button>
        {!importResult && (
          <button
            onClick={handleImport}
            disabled={!selectedFile || importMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {importMutation.isPending ? 'Importing...' : 'Import Items'}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Import Menu Items"
      maxWidth="2xl"
      footer={footer}
      closeOnBackdropClick={!importMutation.isPending}
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Menu Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              <strong>Menu:</strong> {menuName}
            </p>
          </div>

          {/* Download Template */}
          <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">Step 1: Download Template</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Download the Excel template and fill in your menu items following the format.
            </p>
            <button
              onClick={handleDownloadTemplate}
              disabled={downloadTemplateMutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>
                {downloadTemplateMutation.isPending ? 'Downloading...' : 'Download Template'}
              </span>
            </button>
          </div>

          {/* Upload File */}
          <div className="space-y-3">
            <h3 className="font-medium text-gray-900 dark:text-white">Step 2: Upload Filled Excel</h3>

            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-blue-400 dark:hover:border-blue-500 transition-colors bg-white dark:bg-gray-800">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".xlsx,.xls"
                className="hidden"
                id="excel-upload"
              />
              <label
                htmlFor="excel-upload"
                className="cursor-pointer flex flex-col items-center space-y-2"
              >
                <Upload className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedFile ? selectedFile.name : 'Click to select Excel file'}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-500">Supports .xlsx and .xls files</span>
              </label>
            </div>

            {/* Replace Existing Option */}
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={replaceExisting}
                onChange={(e) => setReplaceExisting(e.target.checked)}
                className="rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Replace existing items (delete all current items before import)
              </span>
            </label>
          </div>

          {/* Import Result */}
          {importResult && (
            <div
              className={`rounded-lg p-4 ${
                importResult.status === 'success'
                  ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                  : importResult.status === 'partial'
                  ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                  : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
              }`}
            >
              <div className="flex items-start space-x-3">
                {importResult.status === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                )}
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">Import Results</h4>
                  <div className="text-sm space-y-1">
                    <p className="text-gray-700 dark:text-gray-300">
                      <strong>Total rows:</strong> {importResult.rows_total}
                    </p>
                    <p className="text-green-700 dark:text-green-400">
                      <strong>Success:</strong> {importResult.rows_success}
                    </p>
                    {importResult.rows_failed > 0 && (
                      <p className="text-red-700 dark:text-red-400">
                        <strong>Failed:</strong> {importResult.rows_failed}
                      </p>
                    )}
                  </div>

                  {/* Error Details */}
                  {importResult.errors && importResult.errors.length > 0 && (
                    <div className="mt-3 max-h-40 overflow-y-auto">
                      <p className="font-medium text-sm text-gray-900 dark:text-white mb-1">Errors:</p>
                      <ul className="text-sm space-y-1">
                        {importResult.errors.slice(0, 10).map((error, idx) => (
                          <li key={idx} className="text-red-700 dark:text-red-400">
                            Row {error.row}: {error.error}
                          </li>
                        ))}
                        {importResult.errors.length > 10 && (
                          <li className="text-gray-600 dark:text-gray-400 italic">
                            ... and {importResult.errors.length - 10} more errors
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
    </Modal>
  );
};
