import { useState, useEffect } from 'react';
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit2,
  Copy,
  Trash2,
  Eye,
  Power,
  FileText,
  AlertCircle,
} from 'lucide-react';
import PageHeader from '../components/shared/PageHeader';
import TemplateEditor from '../components/templates/TemplateEditor';
import templatesAPI from '../services/api/templates';
import { showToast } from '../utils/toast';
import type { Template, TemplateCategory } from '../types/template';

export default function Templates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory | 'all'>('all');
  const [showEditor, setShowEditor] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | undefined>();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [selectedCategory]);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const params = {
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
      };
      const data = await templatesAPI.list(params);
      setTemplates(data);
    } catch (error: any) {
      showToast.error('Failed to load templates');
      console.error('Load templates error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTemplate(undefined);
    setShowEditor(true);
  };

  const handleEdit = (template: Template) => {
    setEditingTemplate(template);
    setShowEditor(true);
    setActiveMenu(null);
  };

  const handleSave = (template: Template) => {
    setShowEditor(false);
    setEditingTemplate(undefined);
    loadTemplates();
    showToast.success(
      editingTemplate ? 'Template updated successfully' : 'Template created successfully'
    );
  };

  const handleDelete = async (id: string) => {
    try {
      await templatesAPI.delete(id);
      showToast.success('Template deleted successfully');
      loadTemplates();
    } catch (error: any) {
      showToast.error('Failed to delete template');
      console.error('Delete template error:', error);
    } finally {
      setShowDeleteConfirm(null);
      setActiveMenu(null);
    }
  };

  const handleDuplicate = async (template: Template) => {
    try {
      await templatesAPI.duplicate(template.id, `${template.name} (Copy)`);
      showToast.success('Template duplicated successfully');
      loadTemplates();
    } catch (error: any) {
      showToast.error('Failed to duplicate template');
      console.error('Duplicate template error:', error);
    } finally {
      setActiveMenu(null);
    }
  };

  const handleToggleActive = async (template: Template) => {
    try {
      await templatesAPI.toggleActive(template.id, !template.is_active);
      showToast.success(
        template.is_active ? 'Template deactivated' : 'Template activated'
      );
      loadTemplates();
    } catch (error: any) {
      showToast.error('Failed to update template status');
      console.error('Toggle active error:', error);
    } finally {
      setActiveMenu(null);
    }
  };

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      searchQuery === '' ||
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getCategoryBadgeClass = (category: TemplateCategory) => {
    const classes = {
      text: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      weather: 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400',
      firebird: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      system: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      custom: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    };
    return classes[category] || classes.text;
  };

  const getCategoryIcon = (category: TemplateCategory) => {
    const icons = {
      text: '📝',
      weather: '🌤️',
      firebird: '🔥',
      system: '🖥️',
      custom: '🎨',
    };
    return icons[category] || '📄';
  };

  return (
    <div className="p-6">
      <PageHeader
        title="Templates"
        subtitle="Manage content templates with dynamic variables"
        action={{
          label: 'Create Template',
          onClick: handleCreate,
          icon: Plus,
        }}
      />

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search templates..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
            />
          </div>

          {/* Category Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as TemplateCategory | 'all')}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
            >
              <option value="all">All Categories</option>
              <option value="text">Text</option>
              <option value="weather">Weather</option>
              <option value="firebird">Firebird</option>
              <option value="system">System</option>
              <option value="custom">Custom</option>
            </select>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading templates...</p>
          </div>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-12">
          <div className="text-center">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No templates found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {searchQuery
                ? 'Try adjusting your search criteria'
                : 'Get started by creating your first template'}
            </p>
            {!searchQuery && (
              <button
                onClick={handleCreate}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create Template
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
            >
              {/* Card Header */}
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getCategoryIcon(template.category)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-1">
                        {template.name}
                      </h3>
                      <span
                        className={`inline-block px-2 py-0.5 text-xs rounded-full ${getCategoryBadgeClass(
                          template.category
                        )}`}
                      >
                        {template.category}
                      </span>
                    </div>
                  </div>

                  {/* Menu */}
                  <div className="relative">
                    <button
                      onClick={() =>
                        setActiveMenu(activeMenu === template.id ? null : template.id)
                      }
                      className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                    >
                      <MoreVertical className="w-5 h-5" />
                    </button>

                    {activeMenu === template.id && (
                      <>
                        <div
                          className="fixed inset-0 z-10"
                          onClick={() => setActiveMenu(null)}
                        />
                        <div className="absolute right-0 top-8 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 py-1 z-20">
                          <button
                            onClick={() => handleEdit(template)}
                            className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2"
                          >
                            <Edit2 className="w-4 h-4" />
                            Edit
                          </button>
                          <button
                            onClick={() => handleDuplicate(template)}
                            className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2"
                          >
                            <Copy className="w-4 h-4" />
                            Duplicate
                          </button>
                          <button
                            onClick={() => handleToggleActive(template)}
                            className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2"
                          >
                            <Power className="w-4 h-4" />
                            {template.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <hr className="my-1 border-gray-200 dark:border-gray-600" />
                          <button
                            onClick={() => setShowDeleteConfirm(template.id)}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                          >
                            <Trash2 className="w-4 h-4" />
                            Delete
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {template.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {template.description}
                  </p>
                )}
              </div>

              {/* Card Content */}
              <div className="p-4">
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 mb-3">
                  <code className="text-xs text-gray-700 dark:text-gray-300 font-mono line-clamp-4 whitespace-pre-wrap break-all">
                    {template.content}
                  </code>
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-3">
                    <span className={`flex items-center gap-1 ${template.is_active ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                      <Power className="w-3 h-3" />
                      {template.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {template.usage_count !== undefined && (
                      <span>
                        <Eye className="w-3 h-3 inline mr-1" />
                        {template.usage_count} uses
                      </span>
                    )}
                  </div>
                  <span>
                    {new Date(template.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Template Editor Modal */}
      {showEditor && (
        <TemplateEditor
          template={editingTemplate}
          onSave={handleSave}
          onCancel={() => {
            setShowEditor(false);
            setEditingTemplate(undefined);
          }}
        />
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
                <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Delete Template
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Are you sure you want to delete this template? This action cannot be undone.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(showDeleteConfirm)}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
