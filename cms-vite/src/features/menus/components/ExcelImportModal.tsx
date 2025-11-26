/**
 * Excel Import Modal Component
 * Upload Excel file to import menu items
 */

import { useState } from 'react';
import { X, Upload, Download, CheckCircle, AlertCircle } from 'lucide-react';
import { useImportMenuItems, useDownloadTemplate } from '../hooks/useMenuImport';
import type { MenuImportResult } from '../types/menu';

interface ExcelImportModalProps {
  menuId: number;
  menuName: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ExcelImportModal = ({
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">Import Menu Items</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Menu Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Menu:</strong> {menuName}
            </p>
          </div>

          {/* Download Template */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">Step 1: Download Template</h3>
            <p className="text-sm text-gray-600 mb-3">
              Download the Excel template and fill in your menu items following the format.
            </p>
            <button
              onClick={handleDownloadTemplate}
              disabled={downloadTemplateMutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>
                {downloadTemplateMutation.isPending ? 'Downloading...' : 'Download Template'}
              </span>
            </button>
          </div>

          {/* Upload File */}
          <div className="space-y-3">
            <h3 className="font-medium text-gray-900">Step 2: Upload Filled Excel</h3>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
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
                <Upload className="w-8 h-8 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {selectedFile ? selectedFile.name : 'Click to select Excel file'}
                </span>
                <span className="text-xs text-gray-500">Supports .xlsx and .xls files</span>
              </label>
            </div>

            {/* Replace Existing Option */}
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={replaceExisting}
                onChange={(e) => setReplaceExisting(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-gray-700">
                Replace existing items (delete all current items before import)
              </span>
            </label>
          </div>

          {/* Import Result */}
          {importResult && (
            <div
              className={`rounded-lg p-4 ${
                importResult.status === 'success'
                  ? 'bg-green-50 border border-green-200'
                  : importResult.status === 'partial'
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-start space-x-3">
                {importResult.status === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                )}
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-2">Import Results</h4>
                  <div className="text-sm space-y-1">
                    <p>
                      <strong>Total rows:</strong> {importResult.rows_total}
                    </p>
                    <p className="text-green-700">
                      <strong>Success:</strong> {importResult.rows_success}
                    </p>
                    {importResult.rows_failed > 0 && (
                      <p className="text-red-700">
                        <strong>Failed:</strong> {importResult.rows_failed}
                      </p>
                    )}
                  </div>

                  {/* Error Details */}
                  {importResult.errors && importResult.errors.length > 0 && (
                    <div className="mt-3 max-h-40 overflow-y-auto">
                      <p className="font-medium text-sm text-gray-900 mb-1">Errors:</p>
                      <ul className="text-sm space-y-1">
                        {importResult.errors.slice(0, 10).map((error, idx) => (
                          <li key={idx} className="text-red-700">
                            Row {error.row}: {error.error}
                          </li>
                        ))}
                        {importResult.errors.length > 10 && (
                          <li className="text-gray-600 italic">
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

        {/* Actions */}
        <div className="flex justify-end space-x-3 p-6 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            {importResult ? 'Close' : 'Cancel'}
          </button>
          {!importResult && (
            <button
              onClick={handleImport}
              disabled={!selectedFile || importMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {importMutation.isPending ? 'Importing...' : 'Import Items'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
