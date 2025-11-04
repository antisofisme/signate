/**
 * Select Organization Page
 *
 * LAYER 1: PRESENTATION
 * Allows users with multiple organizations to select which one to use
 * Updated to use OrgSelector component
 */

import { Building2 } from 'lucide-react';
import { OrgSelector } from '@/features/auth/components/OrgSelector';
import { ThemeSwitcher, LanguageSwitcher } from '@/shared/components';

export default function SelectOrganizationPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700 dark:from-gray-900 dark:to-gray-800">
      {/* Theme & Language Switchers - Top Right */}
      <div className="absolute top-4 right-4 flex flex-col items-end gap-2 z-10">
        <LanguageSwitcher />
        <ThemeSwitcher />
      </div>

      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-2xl w-full max-w-3xl">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
            Pilih Organisasi
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Pilih organisasi yang ingin Anda kelola
          </p>
        </div>

        {/* Organization Selector Component */}
        <OrgSelector />
      </div>
    </div>
  );
}
