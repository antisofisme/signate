/**
 * Bulk Import Modal Component
 * CSV file upload with preview and validation
 */

import React, { useState, useCallback } from 'react';
import Modal from '../shared/Modal';
import translationsApi, { BulkImportResponse } from '../../services/api/translations';
import { getLanguageByCode } from '../../types/translation';
import { showToast } from '../../utils/toast';

interface BulkImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  contentId: string;
  onImportComplete: () => void;
}

interface ParsedRow {
  row: number;
  language: string;
  title: string;
  description: string;
  is_primary: boolean;
  isValid: boolean;
  errors: string[];
}

const BulkImportModal: React.FC<BulkImportModalProps> = ({
  isOpen,
  onClose,
  contentId,
  onImportComplete,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ParsedRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [importResult, setImportResult] = useState<BulkImportResponse | null>(null);

  const handleDownloadTemplate = () => {
    translationsApi.downloadTemplate();
    showToast('Template downloaded successfully', 'success');
  };

  const parseCSV = (text: string): ParsedRow[] => {
    const lines = text.split('\n').filter((line) => line.trim());
    const rows: ParsedRow[] = [];

    // Skip header
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Simple CSV parser (handles basic cases)
      const parts = line.split(',');
      if (parts.length < 4) {
        rows.push({
          row: i + 1,
          language: '',
          title: '',
          description: '',
          is_primary: false,
          isValid: false,
          errors: ['Invalid CSV format: expected 4 columns'],
        });
        continue;
      }

      const language = parts[0].trim();
      const title = parts[1].trim();
      const description = parts[2].trim();
      const isPrimary = parts[3].trim().toLowerCase() === 'true';

      const errors: string[] = [];
      if (!language) errors.push('Language code is required');
      if (!getLanguageByCode(language)) errors.push(`Invalid language code: ${language}`);
      if (!title) errors.push('Title is required');
      if (!description) errors.push('Description is required');

      rows.push({
        row: i + 1,
        language,
        title,
        description,
        is_primary: isPrimary,
        isValid: errors.length === 0,
        errors,
      });
    }

    return rows;
  };

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (!selectedFile) return;

      if (!selectedFile.name.endsWith('.csv')) {
        showToast('Please select a CSV file', 'error');
        return;
      }

      setFile(selectedFile);
      setIsPreviewing(true);

      try {
        const text = await selectedFile.text();
        const parsed = parseCSV(text);
        setPreviewData(parsed);
      } catch (error) {
        console.error('Failed to parse CSV:', error);
        showToast('Failed to parse CSV file', 'error');
        setPreviewData([]);
      } finally {
        setIsPreviewing(false);
      }
    },
    []
  );

  const handleImport = async () => {
    if (!file) return;

    setIsLoading(true);
    try {
      const result = await translationsApi.bulkImport(contentId, file);
      setImportResult(result);

      if (result.errors.length === 0) {
        showToast(
          `Successfully imported ${result.imported} translations`,
          'success'
        );
        onImportComplete();
        setTimeout(() => {
          handleClose();
        }, 2000);
      } else {
        showToast(
          `Imported ${result.imported} translations with ${result.errors.length} errors`,
          'warning'
        );
      }
    } catch (error: any) {
      console.error('Failed to import translations:', error);
      showToast(
        error.response?.data?.detail || 'Failed to import translations',
        'error'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setPreviewData([]);
    setImportResult(null);
    onClose();
  };

  const validRowCount = previewData.filter((row) => row.isValid).length;
  const invalidRowCount = previewData.length - validRowCount;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Bulk Import Translations">
      <div className="space-y-6">
        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex gap-3">
            <svg
              className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h4 className="font-semibold text-blue-900 mb-1">
                How to import translations
              </h4>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Download the CSV template</li>
                <li>Fill in translations for each language</li>
                <li>Upload the completed CSV file</li>
                <li>Review the preview and click Import</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Download Template */}
        <div className="flex justify-center">
          <button
            type="button"
            onClick={handleDownloadTemplate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <svg
              className="w-5 h-5 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download CSV Template
          </button>
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload CSV File
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              id="csv-upload"
              disabled={isLoading}
            />
            <label htmlFor="csv-upload" className="cursor-pointer">
              <svg
                className="w-12 h-12 mx-auto mb-3 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              {file ? (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                  <button
                    type="button"
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Choose different file
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-gray-600">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-gray-500 mt-1">CSV files only</p>
                </div>
              )}
            </label>
          </div>
        </div>

        {/* Preview */}
        {isPreviewing && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Parsing CSV...</span>
          </div>
        )}

        {previewData.length > 0 && !isPreviewing && (
          <div className="space-y-3">
            {/* Summary */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-green-600">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="font-medium">{validRowCount} valid</span>
              </div>
              {invalidRowCount > 0 && (
                <div className="flex items-center gap-2 text-red-600">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="font-medium">{invalidRowCount} errors</span>
                </div>
              )}
            </div>

            {/* Preview Table */}
            <div className="border border-gray-300 rounded-lg overflow-hidden max-h-96 overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Row
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Language
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Title
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Description
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Primary
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {previewData.map((row) => {
                    const language = getLanguageByCode(row.language);
                    return (
                      <tr
                        key={row.row}
                        className={row.isValid ? '' : 'bg-red-50'}
                      >
                        <td className="px-3 py-2 text-sm text-gray-500">
                          {row.row}
                        </td>
                        <td className="px-3 py-2 text-sm">
                          {language ? (
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{language.flag}</span>
                              <span>{language.name}</span>
                            </div>
                          ) : (
                            <span className="text-red-600">{row.language}</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-sm truncate max-w-xs">
                          {row.title}
                        </td>
                        <td className="px-3 py-2 text-sm truncate max-w-xs">
                          {row.description}
                        </td>
                        <td className="px-3 py-2 text-sm">
                          {row.is_primary ? (
                            <span className="text-yellow-600">★</span>
                          ) : (
                            <span className="text-gray-300">☆</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-sm">
                          {row.isValid ? (
                            <span className="text-green-600">✓</span>
                          ) : (
                            <div className="text-red-600">
                              <span>✗</span>
                              {row.errors.length > 0 && (
                                <div className="text-xs mt-1">
                                  {row.errors.join(', ')}
                                </div>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Import Result */}
        {importResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <h4 className="font-semibold text-green-900 mb-1">
                  Import Complete
                </h4>
                <p className="text-sm text-green-800">
                  {importResult.imported} translations imported successfully
                  {importResult.updated > 0 && `, ${importResult.updated} updated`}
                </p>
                {importResult.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-red-800 mb-1">
                      Errors:
                    </p>
                    <ul className="text-sm text-red-700 space-y-1">
                      {importResult.errors.map((error, index) => (
                        <li key={index}>
                          Row {error.row}: {error.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={handleClose}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            {importResult ? 'Close' : 'Cancel'}
          </button>
          {!importResult && (
            <button
              type="button"
              onClick={handleImport}
              disabled={!file || validRowCount === 0 || isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              Import {validRowCount > 0 && `(${validRowCount})`}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default BulkImportModal;
