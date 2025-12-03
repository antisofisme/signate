/**
 * Command Templates Component
 * Save and reuse command configurations
 *
 * NOTE: Uses localStorage until backend API is implemented
 */

import { useState, useEffect } from 'react'
import { Save, Trash2, Star, StarOff, Plus, Search, Edit2, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { Button, Modal } from '@/shared/components'
import type { CommandType } from '../types/commands'
import type { CommandTemplate } from '../types/commandTemplates'
import { COMMAND_TYPE_INFO } from '../types/commandTemplates'
import { renderIcon } from '@/shared/utils/iconHelper'

const STORAGE_KEY = 'command_templates'

interface CommandTemplatesProps {
  onApplyTemplate?: (template: CommandTemplate) => void
}

export function CommandTemplates({ onApplyTemplate }: CommandTemplatesProps) {
  const [templates, setTemplates] = useState<CommandTemplate[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<CommandTemplate | null>(null)

  // Load templates from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        setTemplates(JSON.parse(stored))
      } catch (error) {
        console.error('Failed to load templates:', error)
      }
    }
  }, [])

  // Save templates to localStorage
  const saveTemplates = (newTemplates: CommandTemplate[]) => {
    setTemplates(newTemplates)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newTemplates))
  }

  const handleCreate = (templateData: Partial<CommandTemplate>) => {
    const newTemplate: CommandTemplate = {
      id: Date.now(),
      name: templateData.name!,
      description: templateData.description,
      command_type: templateData.command_type!,
      command_data: templateData.command_data,
      parameters: templateData.parameters,
      priority: templateData.priority || 5,
      expires_in_minutes: templateData.expires_in_minutes || 30,
      tags: templateData.tags || [],
      is_favorite: false,
      usage_count: 0,
      organization_id: 1, // Mock
      created_at: new Date().toISOString(),
    }

    saveTemplates([...templates, newTemplate])
    toast.success('Template created successfully')
    setShowCreateModal(false)
  }

  const handleUpdate = (id: number, updates: Partial<CommandTemplate>) => {
    const updated = templates.map((t) => (t.id === id ? { ...t, ...updates, updated_at: new Date().toISOString() } : t))
    saveTemplates(updated)
    toast.success('Template updated successfully')
    setEditingTemplate(null)
  }

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this template?')) {
      saveTemplates(templates.filter((t) => t.id !== id))
      toast.success('Template deleted')
    }
  }

  const handleToggleFavorite = (id: number) => {
    const updated = templates.map((t) => (t.id === id ? { ...t, is_favorite: !t.is_favorite } : t))
    saveTemplates(updated)
  }

  const handleApply = (template: CommandTemplate) => {
    const updated = templates.map((t) => (t.id === template.id ? { ...t, usage_count: (t.usage_count || 0) + 1 } : t))
    saveTemplates(updated)
    onApplyTemplate?.(template)
    toast.success(`Applied template: ${template.name}`)
  }

  const handleDuplicate = (template: CommandTemplate) => {
    const duplicate: CommandTemplate = {
      ...template,
      id: Date.now(),
      name: `${template.name} (Copy)`,
      is_favorite: false,
      usage_count: 0,
      created_at: new Date().toISOString(),
    }
    saveTemplates([...templates, duplicate])
    toast.success('Template duplicated')
  }

  // Filter templates
  const filteredTemplates = templates.filter((t) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      t.name.toLowerCase().includes(query) ||
      t.description?.toLowerCase().includes(query) ||
      t.command_type.toLowerCase().includes(query) ||
      t.tags?.some((tag) => tag.toLowerCase().includes(query))
    )
  })

  // Sort: favorites first, then by usage count
  const sortedTemplates = [...filteredTemplates].sort((a, b) => {
    if (a.is_favorite && !b.is_favorite) return -1
    if (!a.is_favorite && b.is_favorite) return 1
    return (b.usage_count || 0) - (a.usage_count || 0)
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Command Templates
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Save and reuse common command configurations
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          New Template
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search templates..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        />
      </div>

      {/* Templates Grid */}
      {sortedTemplates.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Save className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">
            {searchQuery ? 'No templates match your search' : 'No templates saved yet'}
          </p>
          <Button
            variant="outline"
            onClick={() => setShowCreateModal(true)}
            className="mt-4"
          >
            Create your first template
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedTemplates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onApply={handleApply}
              onEdit={() => setEditingTemplate(template)}
              onDelete={handleDelete}
              onToggleFavorite={handleToggleFavorite}
              onDuplicate={handleDuplicate}
            />
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingTemplate) && (
        <TemplateModal
          template={editingTemplate}
          onSave={editingTemplate ? (data) => handleUpdate(editingTemplate.id, data) : handleCreate}
          onClose={() => {
            setShowCreateModal(false)
            setEditingTemplate(null)
          }}
        />
      )}
    </div>
  )
}

// Template Card Component
function TemplateCard({
  template,
  onApply,
  onEdit,
  onDelete,
  onToggleFavorite,
  onDuplicate,
}: {
  template: CommandTemplate
  onApply: (template: CommandTemplate) => void
  onEdit: () => void
  onDelete: (id: number) => void
  onToggleFavorite: (id: number) => void
  onDuplicate: (template: CommandTemplate) => void
}) {
  const commandInfo = COMMAND_TYPE_INFO[template.command_type]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex-shrink-0">
            {renderIcon(commandInfo?.icon || 'FileText', { className: 'w-6 h-6 text-gray-600 dark:text-gray-400' })}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{template.name}</h3>
            {template.description && (
              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mt-0.5">
                {template.description}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={() => onToggleFavorite(template.id)}
          className="text-yellow-500 hover:scale-110 transition-transform"
        >
          {template.is_favorite ? <Star className="w-5 h-5 fill-current" /> : <StarOff className="w-5 h-5" />}
        </button>
      </div>

      <div className="space-y-2 mb-4">
        <div className="text-xs text-gray-600 dark:text-gray-400">
          <span className="font-medium">Command:</span> {commandInfo?.label}
        </div>
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {template.tags.map((tag, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Used {template.usage_count || 0} time{template.usage_count !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={() => onApply(template)}
          className="flex-1"
        >
          Apply
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={onEdit}
          title="Edit"
        >
          <Edit2 className="w-4 h-4" />
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onDuplicate(template)}
          title="Duplicate"
        >
          <Copy className="w-4 h-4" />
        </Button>
        <Button
          variant="danger"
          size="sm"
          onClick={() => onDelete(template.id)}
          title="Delete"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}

// Template Modal Component
function TemplateModal({
  template,
  onSave,
  onClose,
}: {
  template: CommandTemplate | null
  onSave: (data: Partial<CommandTemplate>) => void
  onClose: () => void
}) {
  const [name, setName] = useState(template?.name || '')
  const [description, setDescription] = useState(template?.description || '')
  const [commandType, setCommandType] = useState<CommandType>(template?.command_type || 'refresh_content')
  const [parameters, setParameters] = useState(JSON.stringify(template?.command_data || {}, null, 2))
  const [priority, setPriority] = useState(template?.priority || 5)
  const [expiresIn, setExpiresIn] = useState(template?.expires_in_minutes || 30)
  const [tags, setTags] = useState(template?.tags?.join(', ') || '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      toast.error('Template name is required')
      return
    }

    let commandData = {}
    try {
      commandData = JSON.parse(parameters)
    } catch {
      toast.error('Invalid JSON in parameters')
      return
    }

    onSave({
      name: name.trim(),
      description: description.trim(),
      command_type: commandType,
      command_data: commandData,
      priority,
      expires_in_minutes: expiresIn,
      tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
    })
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={template ? 'Edit Template' : 'Create Template'}
      maxWidth="2xl"
      footer={
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button type="submit" form="template-form">
            {template ? 'Update Template' : 'Create Template'}
          </Button>
        </div>
      }
    >
      <form id="template-form" onSubmit={handleSubmit} className="p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Template Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Morning Refresh"
            required
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What does this template do?"
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Command Type *
          </label>
          <select
            value={commandType}
            onChange={(e) => setCommandType(e.target.value as CommandType)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            {Object.values(COMMAND_TYPE_INFO).map((cmd) => (
              <option key={cmd.type} value={cmd.type}>
                {cmd.icon} {cmd.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Parameters (JSON)
          </label>
          <textarea
            value={parameters}
            onChange={(e) => setParameters(e.target.value)}
            placeholder="{}"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Priority (1-10)
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Expires In (minutes)
            </label>
            <input
              type="number"
              min="5"
              max="1440"
              value={expiresIn}
              onChange={(e) => setExpiresIn(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Tags (comma-separated)
          </label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g., maintenance, daily, high-priority"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>
      </form>
    </Modal>
  )
}

export default CommandTemplates
