/**
 * Translation Form Component
 * Create/Edit translation with language and field selection
 */

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import LanguageSelector from './LanguageSelector'
import EntitySelector from './EntitySelector'
import {
  ENTITY_TYPES,
  type Translation,
  type EntityType,
  type Language,
  type CreateTranslationRequest,
  type UpdateTranslationRequest,
} from '../types/translation.types'

// Validation schema
const translationFormSchema = z.object({
  entity_type: z.enum(['content', 'playlist', 'template', 'widget']),
  entity_id: z.number().min(1, 'Please select an entity'),
  language: z.enum(['en', 'id', 'zh', 'ja', 'ko', 'th', 'vi', 'ms', 'es', 'fr']),
  field_name: z.string().min(1, 'Field name is required'),
  translated_text: z.string().min(1, 'Translation is required'),
})

type TranslationFormData = z.infer<typeof translationFormSchema>

interface TranslationFormProps {
  translation?: Translation
  onSubmit: (data: CreateTranslationRequest | UpdateTranslationRequest) => void
  onCancel: () => void
  isLoading?: boolean
}

export const TranslationForm = ({
  translation,
  onSubmit,
  onCancel,
  isLoading = false,
}: TranslationFormProps) => {
  const isEdit = !!translation

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TranslationFormData>({
    resolver: zodResolver(translationFormSchema),
    defaultValues: translation
      ? {
          entity_type: translation.entity_type,
          entity_id: translation.entity_id,
          language: translation.language,
          field_name: translation.field_name,
          translated_text: translation.translated_text,
        }
      : {
          entity_type: 'content',
          entity_id: 0,
          language: 'en',
          field_name: '',
          translated_text: '',
        },
  })

  const entityType = watch('entity_type')
  const entityId = watch('entity_id')
  const language = watch('language')

  const availableFields = entityType ? ENTITY_TYPES[entityType].translatableFields : []

  const handleFormSubmit = (data: TranslationFormData) => {
    if (isEdit) {
      // For edit, only send updated fields
      onSubmit({
        translated_text: data.translated_text,
      } as UpdateTranslationRequest)
    } else {
      // For create, send all fields
      onSubmit(data as CreateTranslationRequest)
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Entity Selection (only for create) */}
      {!isEdit && (
        <EntitySelector
          selectedEntityType={entityType}
          selectedEntityId={entityId}
          onEntityTypeChange={(type) => setValue('entity_type', type)}
          onEntityIdChange={(id) => setValue('entity_id', id)}
          disabled={isLoading}
        />
      )}

      {/* Language Selection */}
      <LanguageSelector
        selectedLanguage={language}
        onSelect={(lang) => setValue('language', lang)}
        disabled={isLoading || isEdit}
        label={isEdit ? 'Language (cannot be changed)' : 'Target Language'}
      />

      {/* Field Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Field to Translate *
        </label>
        <select
          {...register('field_name')}
          disabled={isLoading || isEdit}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">-- Select Field --</option>
          {availableFields.map((field) => (
            <option key={field} value={field}>
              {field}
            </option>
          ))}
        </select>
        {isEdit && (
          <p className="mt-1 text-xs text-gray-500">Field cannot be changed after creation</p>
        )}
        {errors.field_name && (
          <p className="mt-1 text-sm text-red-600">{errors.field_name.message}</p>
        )}
      </div>

      {/* Translation Text */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Translated Text *
        </label>
        <textarea
          {...register('translated_text')}
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
          placeholder="Enter translation here..."
          disabled={isLoading}
        />
        {errors.translated_text && (
          <p className="mt-1 text-sm text-red-600">{errors.translated_text.message}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          💡 Tip: For template content, maintain the same {`{{variable}}`} placeholders
        </p>
      </div>

      {/* Translation Info */}
      {isEdit && translation && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Translation Info</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-gray-600">Status:</span>
              <span className={`ml-2 px-2 py-0.5 rounded ${
                translation.status === 'approved'
                  ? 'bg-green-100 text-green-700'
                  : translation.status === 'rejected'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {translation.status}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Created:</span>
              <span className="ml-2 text-gray-900">
                {new Date(translation.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading && (
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
          {isEdit ? 'Update Translation' : 'Create Translation'}
        </button>
      </div>
    </form>
  )
}

export default TranslationForm
