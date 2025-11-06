import { useState, useEffect, useRef } from 'react';
import { Save, X, AlertTriangle, CheckCircle, Eye, Code } from 'lucide-react';
import VariablePicker from './VariablePicker';
import TemplatePreview from './TemplatePreview';
import templatesAPI from '../../services/api/templates';
import type { Template, CreateTemplateRequest, UpdateTemplateRequest, TemplateCategory } from '../../types/template';

interface TemplateEditorProps {
  template?: Template;
  onSave: (template: Template) => void;
  onCancel: () => void;
}

type ViewMode = 'split' | 'editor' | 'preview';

export default function TemplateEditor({ template, onSave, onCancel }: TemplateEditorProps) {
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [content, setContent] = useState(template?.content || '');
  const [category, setCategory] = useState<TemplateCategory>(template?.category || 'text');
  const [isActive, setIsActive] = useState(template?.is_active ?? true);
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Validate content on change (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (content) {
        validateContent();
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [content]);

  const validateContent = async () => {
    setValidating(true);
    try {
      const result = await templatesAPI.validate({ content });
      setValidation(result);
    } catch (err) {
      console.error('Validation error:', err);
    } finally {
      setValidating(false);
    }
  };

  const handleVariableSelect = (variable: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const newContent = content.substring(0, start) + variable + content.substring(end);

    setContent(newContent);

    // Move cursor after inserted variable
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + variable.length, start + variable.length);
    }, 0);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Template name is required');
      return;
    }

    if (!content.trim()) {
      setError('Template content is required');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      let result: Template;

      if (template) {
        // Update existing template
        const updateData: UpdateTemplateRequest = {
          name,
          description: description || undefined,
          content,
          category,
          is_active: isActive,
        };
        result = await templatesAPI.update(template.id, updateData);
      } else {
        // Create new template
        const createData: CreateTemplateRequest = {
          name,
          description: description || undefined,
          content,
          category,
          is_active: isActive,
        };
        result = await templatesAPI.create(createData);
      }

      onSave(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const getViewModeClasses = () => {
    switch (viewMode) {
      case 'editor':
        return 'grid-cols-[300px,1fr]';
      case 'preview':
        return 'grid-cols-[300px,1fr]';
      case 'split':
      default:
        return 'grid-cols-[300px,1fr,1fr]';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              {template ? 'Edit Template' : 'Create Template'}
            </h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Template Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Weather Widget Template"
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as TemplateCategory)}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                >
                  <option value="text">Text</option>
                  <option value="weather">Weather</option>
                  <option value="firebird">Firebird</option>
                  <option value="system">System</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Template description"
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                />
              </div>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="ml-4 p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* View Mode Selector */}
        <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('editor')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                viewMode === 'editor'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Code className="w-4 h-4 inline mr-1" />
              Editor Only
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                viewMode === 'split'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Split View
            </button>
            <button
              onClick={() => setViewMode('preview')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                viewMode === 'preview'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Eye className="w-4 h-4 inline mr-1" />
              Preview Only
            </button>
          </div>

          {/* Validation Status */}
          {validating && (
            <div className="text-xs text-gray-500 dark:text-gray-400">Validating...</div>
          )}
          {validation && !validating && (
            <div className="flex items-center gap-2">
              {validation.valid ? (
                <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4" />
                  Valid syntax
                </div>
              ) : (
                <div className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
                  <AlertTriangle className="w-4 h-4" />
                  {validation.errors?.length || 0} errors
                </div>
              )}
              {validation.security_issues && validation.security_issues.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-orange-600 dark:text-orange-400">
                  <AlertTriangle className="w-4 h-4" />
                  {validation.security_issues.length} security warnings
                </div>
              )}
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-6 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Main Content */}
        <div className={`flex-1 grid ${getViewModeClasses()} overflow-hidden`}>
          {/* Variable Picker */}
          <VariablePicker onVariableSelect={handleVariableSelect} />

          {/* Editor */}
          {(viewMode === 'editor' || viewMode === 'split') && (
            <div className="flex flex-col border-r border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                  Template Content
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Use Jinja2 syntax. Click variables to insert.
                </p>
              </div>
              <div className="flex-1 p-4 overflow-hidden">
                <textarea
                  ref={textareaRef}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Enter template content here...&#10;&#10;Example:&#10;<h1>Hello {{ device.name }}!</h1>&#10;<p>Temperature: {{ weather.temperature }}°C</p>"
                  className="w-full h-full px-4 py-3 font-mono text-sm bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white resize-none"
                  style={{ fontFamily: 'Consolas, Monaco, "Courier New", monospace' }}
                />
              </div>

              {/* Validation Messages */}
              {validation && !validation.valid && (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-red-50 dark:bg-red-900/20 max-h-32 overflow-y-auto">
                  <h4 className="text-xs font-semibold text-red-800 dark:text-red-400 mb-2">
                    Validation Errors:
                  </h4>
                  <ul className="list-disc list-inside space-y-1">
                    {validation.errors?.map((err: string, idx: number) => (
                      <li key={idx} className="text-xs text-red-700 dark:text-red-300">
                        {err}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {validation?.security_issues && validation.security_issues.length > 0 && (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-orange-50 dark:bg-orange-900/20 max-h-32 overflow-y-auto">
                  <h4 className="text-xs font-semibold text-orange-800 dark:text-orange-400 mb-2">
                    Security Warnings:
                  </h4>
                  <ul className="list-disc list-inside space-y-1">
                    {validation.security_issues.map((warning: string, idx: number) => (
                      <li key={idx} className="text-xs text-orange-700 dark:text-orange-300">
                        {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Preview */}
          {(viewMode === 'preview' || viewMode === 'split') && (
            <TemplatePreview
              templateId={template?.id}
              content={content}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              Active
            </label>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || (validation && !validation.valid)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Template'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
