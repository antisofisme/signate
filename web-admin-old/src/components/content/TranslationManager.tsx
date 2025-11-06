/**
 * Translation Manager Component
 * Manages content translations with tab-based interface
 */

import React, { useState, useEffect, useCallback } from 'react';
import LanguageSelector from '../translations/LanguageSelector';
import BulkImportModal from '../translations/BulkImportModal';
import translationsApi, { Translation, TranslationCreate } from '../../services/api/translations';
import { getLanguageByCode, isRTLLanguage } from '../../types/translation';
import { showToast } from '../../utils/toast';

interface TranslationManagerProps {
  contentId: string;
  className?: string;
}

interface TranslationFormData {
  id?: string;
  language: string;
  title: string;
  description: string;
  is_primary: boolean;
  isNew?: boolean;
  isDirty?: boolean;
}

const TranslationManager: React.FC<TranslationManagerProps> = ({
  contentId,
  className = '',
}) => {
  const [translations, setTranslations] = useState<TranslationFormData[]>([]);
  const [activeTab, setActiveTab] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [showAddLanguage, setShowAddLanguage] = useState(false);
  const [newLanguage, setNewLanguage] = useState('');

  // Load translations
  const loadTranslations = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await translationsApi.list(contentId);
      const formData: TranslationFormData[] = data.map((t) => ({
        id: t.id,
        language: t.language,
        title: t.title,
        description: t.description,
        is_primary: t.is_primary,
        isNew: false,
        isDirty: false,
      }));
      setTranslations(formData);

      // Set active tab to primary language or first language
      const primary = formData.find((t) => t.is_primary);
      if (primary) {
        setActiveTab(primary.language);
      } else if (formData.length > 0) {
        setActiveTab(formData[0].language);
      }
    } catch (error) {
      console.error('Failed to load translations:', error);
      showToast('Failed to load translations', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [contentId]);

  useEffect(() => {
    loadTranslations();
  }, [loadTranslations]);

  const handleAddLanguage = () => {
    if (!newLanguage) return;

    // Check if language already exists
    if (translations.some((t) => t.language === newLanguage)) {
      showToast('Translation for this language already exists', 'error');
      return;
    }

    const newTranslation: TranslationFormData = {
      language: newLanguage,
      title: '',
      description: '',
      is_primary: translations.length === 0, // First language is primary by default
      isNew: true,
      isDirty: true,
    };

    setTranslations([...translations, newTranslation]);
    setActiveTab(newLanguage);
    setShowAddLanguage(false);
    setNewLanguage('');
  };

  const handleRemoveLanguage = async (language: string) => {
    const translation = translations.find((t) => t.language === language);
    if (!translation) return;

    // Confirm deletion
    if (!confirm(`Remove ${getLanguageByCode(language)?.name} translation?`)) {
      return;
    }

    // If it's a new translation, just remove from state
    if (translation.isNew) {
      setTranslations(translations.filter((t) => t.language !== language));
      if (activeTab === language) {
        setActiveTab(translations[0]?.language || '');
      }
      return;
    }

    // If it's an existing translation, delete from server
    try {
      await translationsApi.remove(contentId, language);
      setTranslations(translations.filter((t) => t.language !== language));
      if (activeTab === language) {
        setActiveTab(translations[0]?.language || '');
      }
      showToast('Translation removed successfully', 'success');
    } catch (error) {
      console.error('Failed to remove translation:', error);
      showToast('Failed to remove translation', 'error');
    }
  };

  const handleFieldChange = (
    language: string,
    field: keyof TranslationFormData,
    value: any
  ) => {
    setTranslations(
      translations.map((t) =>
        t.language === language ? { ...t, [field]: value, isDirty: true } : t
      )
    );
  };

  const handleSetPrimary = (language: string) => {
    setTranslations(
      translations.map((t) => ({
        ...t,
        is_primary: t.language === language,
        isDirty: true,
      }))
    );
  };

  const handleSave = async () => {
    const dirtyTranslations = translations.filter((t) => t.isDirty);
    if (dirtyTranslations.length === 0) {
      showToast('No changes to save', 'info');
      return;
    }

    // Validate
    for (const translation of dirtyTranslations) {
      if (!translation.title.trim()) {
        showToast(`Title is required for ${getLanguageByCode(translation.language)?.name}`, 'error');
        return;
      }
      if (!translation.description.trim()) {
        showToast(`Description is required for ${getLanguageByCode(translation.language)?.name}`, 'error');
        return;
      }
    }

    setIsSaving(true);
    try {
      for (const translation of dirtyTranslations) {
        if (translation.isNew) {
          // Create new translation
          const data: TranslationCreate = {
            language: translation.language,
            title: translation.title,
            description: translation.description,
            is_primary: translation.is_primary,
          };
          await translationsApi.create(contentId, data);
        } else {
          // Update existing translation
          await translationsApi.update(contentId, translation.language, {
            title: translation.title,
            description: translation.description,
            is_primary: translation.is_primary,
          });
        }
      }

      showToast('Translations saved successfully', 'success');
      loadTranslations(); // Reload to get fresh data
    } catch (error: any) {
      console.error('Failed to save translations:', error);
      showToast(
        error.response?.data?.detail || 'Failed to save translations',
        'error'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await translationsApi.exportCSV(contentId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `translations_${contentId}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      showToast('Translations exported successfully', 'success');
    } catch (error) {
      console.error('Failed to export translations:', error);
      showToast('Failed to export translations', 'error');
    }
  };

  const activeTranslation = translations.find((t) => t.language === activeTab);
  const usedLanguages = translations.map((t) => t.language);
  const isDirty = translations.some((t) => t.isDirty);

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading translations...</span>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900">Translations</h3>
          <span className="px-2 py-1 text-sm bg-blue-100 text-blue-700 rounded">
            {translations.length} {translations.length === 1 ? 'language' : 'languages'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExport}
            disabled={translations.length === 0}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </button>
          <button
            type="button"
            onClick={() => setShowBulkImport(true)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Bulk Import
          </button>
          <button
            type="button"
            onClick={() => setShowAddLanguage(true)}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Language
          </button>
        </div>
      </div>

      {/* Language Tabs */}
      {translations.length > 0 ? (
        <>
          <div className="border-b border-gray-200 mb-4">
            <div className="flex gap-2 overflow-x-auto">
              {translations.map((translation) => {
                const language = getLanguageByCode(translation.language);
                if (!language) return null;

                return (
                  <button
                    key={translation.language}
                    type="button"
                    onClick={() => setActiveTab(translation.language)}
                    className={`
                      flex items-center gap-2 px-4 py-2 border-b-2 transition-colors whitespace-nowrap
                      ${
                        activeTab === translation.language
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-600 hover:text-gray-900'
                      }
                    `}
                  >
                    <span className="text-xl">{language.flag}</span>
                    <span className="font-medium">{language.name}</span>
                    {translation.is_primary && (
                      <span className="text-yellow-500" title="Primary language">
                        ★
                      </span>
                    )}
                    {translation.isDirty && (
                      <span className="w-2 h-2 bg-orange-500 rounded-full" title="Unsaved changes" />
                    )}
                    {language.isRTL && (
                      <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                        RTL
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Translation Form */}
          {activeTranslation && (
            <div className="space-y-4">
              {/* Language Info */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">
                    {getLanguageByCode(activeTranslation.language)?.flag}
                  </span>
                  <div>
                    <div className="font-medium text-gray-900">
                      {getLanguageByCode(activeTranslation.language)?.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {getLanguageByCode(activeTranslation.language)?.nativeName}
                    </div>
                  </div>
                  {isRTLLanguage(activeTranslation.language) && (
                    <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded">
                      Right-to-Left (RTL)
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveLanguage(activeTranslation.language)}
                  className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  Remove Language
                </button>
              </div>

              {/* Primary Language Checkbox */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id={`primary-${activeTranslation.language}`}
                  checked={activeTranslation.is_primary}
                  onChange={(e) =>
                    e.target.checked && handleSetPrimary(activeTranslation.language)
                  }
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label
                  htmlFor={`primary-${activeTranslation.language}`}
                  className="text-sm font-medium text-gray-700 flex items-center gap-2"
                >
                  Set as Primary Language
                  <span className="text-yellow-500">★</span>
                </label>
                <div className="ml-auto text-xs text-gray-500">
                  {activeTranslation.is_primary && (
                    <span className="text-green-600">This is the primary language</span>
                  )}
                </div>
              </div>

              {/* Title Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  type="text"
                  value={activeTranslation.title}
                  onChange={(e) =>
                    handleFieldChange(activeTranslation.language, 'title', e.target.value)
                  }
                  dir={isRTLLanguage(activeTranslation.language) ? 'rtl' : 'ltr'}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder={`Enter title in ${getLanguageByCode(activeTranslation.language)?.name}`}
                />
              </div>

              {/* Description Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <textarea
                  value={activeTranslation.description}
                  onChange={(e) =>
                    handleFieldChange(activeTranslation.language, 'description', e.target.value)
                  }
                  dir={isRTLLanguage(activeTranslation.language) ? 'rtl' : 'ltr'}
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder={`Enter description in ${getLanguageByCode(activeTranslation.language)?.name}`}
                />
              </div>

              {/* Fallback Info */}
              {!activeTranslation.is_primary && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <svg
                      className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <div className="text-sm text-yellow-800">
                      <p className="font-medium mb-1">Fallback Behavior</p>
                      <p>
                        If this translation is not available, the system will use the{' '}
                        <span className="font-semibold">
                          {translations.find((t) => t.is_primary)
                            ? getLanguageByCode(translations.find((t) => t.is_primary)!.language)?.name
                            : 'primary language'}
                        </span>{' '}
                        translation instead.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Save Button */}
          {isDirty && (
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 mt-6">
              <button
                type="button"
                onClick={loadTranslations}
                disabled={isSaving}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isSaving && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                )}
                Save Translations
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <svg
            className="w-16 h-16 mx-auto mb-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
            />
          </svg>
          <h4 className="text-lg font-medium text-gray-900 mb-2">
            No translations yet
          </h4>
          <p className="text-gray-600 mb-4">
            Add a language to start translating this content
          </p>
          <button
            type="button"
            onClick={() => setShowAddLanguage(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add First Language
          </button>
        </div>
      )}

      {/* Add Language Modal */}
      {showAddLanguage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Add Language</h3>
              <LanguageSelector
                value={newLanguage}
                onChange={setNewLanguage}
                excludeLanguages={usedLanguages}
                placeholder="Select a language to add"
              />
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddLanguage(false);
                    setNewLanguage('');
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAddLanguage}
                  disabled={!newLanguage}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add Language
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Import Modal */}
      <BulkImportModal
        isOpen={showBulkImport}
        onClose={() => setShowBulkImport(false)}
        contentId={contentId}
        onImportComplete={loadTranslations}
      />
    </div>
  );
};

export default TranslationManager;
