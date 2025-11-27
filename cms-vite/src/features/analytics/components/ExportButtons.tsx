/**
 * ExportButtons Component
 * Export analytics data to PDF or Excel
 */

import { FileDown, FileSpreadsheet, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ExportButtonsProps {
  onExportPDF?: () => void;
  onExportExcel?: () => void;
  isExporting?: boolean;
  className?: string;
}

export function ExportButtons({
  onExportPDF,
  onExportExcel,
  isExporting = false,
  className = '',
}: ExportButtonsProps) {
  const { t } = useTranslation();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm text-gray-500 dark:text-gray-400 mr-1">
        {t('analytics.export', 'Export')}:
      </span>
      <button
        onClick={onExportPDF}
        disabled={isExporting || !onExportPDF}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title={t('analytics.exportPDF', 'Export as PDF')}
      >
        <FileText className="h-4 w-4" />
        PDF
      </button>
      <button
        onClick={onExportExcel}
        disabled={isExporting || !onExportExcel}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title={t('analytics.exportExcel', 'Export as Excel')}
      >
        <FileSpreadsheet className="h-4 w-4" />
        Excel
      </button>
    </div>
  );
}
