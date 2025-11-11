/**
 * Translation API Service
 * Handles content translation operations
 */

import api from './index';

export interface Translation {
  id: string;
  content_id: string;
  language: string;
  title: string;
  description: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface TranslationCreate {
  language: string;
  title: string;
  description: string;
  is_primary?: boolean;
}

export interface TranslationUpdate {
  title?: string;
  description?: string;
  is_primary?: boolean;
}

export interface BulkImportResponse {
  imported: number;
  updated: number;
  errors: Array<{
    row: number;
    message: string;
  }>;
}

export interface AvailableLanguage {
  code: string;
  name: string;
  has_translation: boolean;
}

/**
 * Get all translations for a specific content
 */
export const list = async (contentId: string): Promise<Translation[]> => {
  const response = await api.get(`/content/${contentId}/translations`);
  return response.data?.data?.translations || [];
};

/**
 * Create a new translation for content
 */
export const create = async (
  contentId: string,
  data: TranslationCreate
): Promise<Translation> => {
  const response = await api.post(`/content/${contentId}/translations`, data);
  return response.data?.data;
};

/**
 * Update an existing translation
 */
export const update = async (
  contentId: string,
  language: string,
  data: TranslationUpdate
): Promise<Translation> => {
  const response = await api.patch(`/content/${contentId}/translations/${language}`, data);
  return response.data?.data;
};

/**
 * Delete a translation
 */
export const remove = async (contentId: string, language: string): Promise<void> => {
  await api.delete(`/content/${contentId}/translations/${language}`);
};

/**
 * Bulk import translations from CSV file
 */
export const bulkImport = async (
  contentId: string,
  file: File
): Promise<BulkImportResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post(
    `/translations/bulk-import?content_id=${contentId}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data?.data || { imported: 0, updated: 0, errors: [] };
};

/**
 * Export translations to CSV file
 */
export const exportCSV = async (contentId: string): Promise<Blob> => {
  const response = await api.get(`/translations/export?content_ids=${contentId}&format=csv`, {
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Get available languages for content
 */
export const getAvailableLanguages = async (
  contentId: string
): Promise<AvailableLanguage[]> => {
  const response = await api.get(`/content/languages`);
  return response.data?.data?.languages || [];
};

/**
 * Download CSV template
 */
export const downloadTemplate = (): void => {
  const csvContent = `language,title,description,is_primary
en,Title in English,Description in English,true
id,Judul dalam Bahasa Indonesia,Deskripsi dalam Bahasa Indonesia,false`;

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', 'translation_template.csv');
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const translationsApi = {
  list,
  create,
  update,
  remove,
  bulkImport,
  exportCSV,
  getAvailableLanguages,
  downloadTemplate,
};

export default translationsApi;
