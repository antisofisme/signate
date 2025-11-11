/**
 * Entity Selector Component
 * Select entity type and specific entity to translate
 */

import { useState, useEffect } from 'react'
import { ENTITY_TYPES, type EntityType } from '../types/translation.types'
import axios from 'axios'

interface Entity {
  id: number
  name: string
  type: EntityType
}

interface EntitySelectorProps {
  selectedEntityType?: EntityType
  selectedEntityId?: number
  onEntityTypeChange: (entityType: EntityType) => void
  onEntityIdChange: (entityId: number) => void
  disabled?: boolean
}

export const EntitySelector = ({
  selectedEntityType,
  selectedEntityId,
  onEntityTypeChange,
  onEntityIdChange,
  disabled = false,
}: EntitySelectorProps) => {
  const [entities, setEntities] = useState<Entity[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Fetch entities when entity type changes
  useEffect(() => {
    if (!selectedEntityType) return

    const fetchEntities = async () => {
      setIsLoading(true)
      try {
        let endpoint = ''
        switch (selectedEntityType) {
          case 'content':
            endpoint = '/api/v1/contents'
            break
          case 'playlist':
            endpoint = '/api/v1/playlists'
            break
          case 'template':
            endpoint = '/api/v1/templates'
            break
          case 'widget':
            endpoint = '/api/v1/widgets'
            break
        }

        const response = await axios.get(endpoint)
        const data = response.data

        // Map response to Entity format
        let mappedEntities: Entity[] = []
        if (selectedEntityType === 'content') {
          mappedEntities = (data.contents || []).map((item: any) => ({
            id: item.id,
            name: item.title || item.name,
            type: selectedEntityType,
          }))
        } else if (selectedEntityType === 'playlist') {
          mappedEntities = (data.playlists || []).map((item: any) => ({
            id: item.id,
            name: item.name,
            type: selectedEntityType,
          }))
        } else if (selectedEntityType === 'template') {
          mappedEntities = (data.templates || []).map((item: any) => ({
            id: item.id,
            name: item.name,
            type: selectedEntityType,
          }))
        } else if (selectedEntityType === 'widget') {
          mappedEntities = (data.widgets || []).map((item: any) => ({
            id: item.id,
            name: item.name,
            type: selectedEntityType,
          }))
        }

        setEntities(mappedEntities)
      } catch (error) {
        console.error('Failed to fetch entities:', error)
        setEntities([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchEntities()
  }, [selectedEntityType])

  const handleEntityTypeClick = (entityType: EntityType) => {
    if (disabled) return
    onEntityTypeChange(entityType)
    onEntityIdChange(0) // Reset entity ID when type changes
  }

  const selectedEntity = entities.find((e) => e.id === selectedEntityId)

  return (
    <div className="space-y-4">
      {/* Entity Type Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Entity Type
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.values(ENTITY_TYPES).map((type) => {
            const selected = selectedEntityType === type.type

            return (
              <button
                key={type.type}
                type="button"
                onClick={() => handleEntityTypeClick(type.type)}
                disabled={disabled}
                className={`
                  p-4 rounded-lg border-2 transition-all
                  ${
                    selected
                      ? 'border-green-500 bg-green-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-green-300 hover:bg-green-50'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className="flex flex-col items-center gap-2">
                  <span className="text-3xl">{type.icon}</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {type.label}
                  </span>
                  <span className="text-xs text-gray-600 text-center">
                    {type.description}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Entity List */}
      {selectedEntityType && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select {ENTITY_TYPES[selectedEntityType].label} to Translate
          </label>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              Loading {ENTITY_TYPES[selectedEntityType].label}s...
            </div>
          ) : entities.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
              <span className="text-3xl mb-2 block">
                {ENTITY_TYPES[selectedEntityType].icon}
              </span>
              <p className="text-gray-600">
                No {ENTITY_TYPES[selectedEntityType].label}s available
              </p>
            </div>
          ) : (
            <select
              value={selectedEntityId || ''}
              onChange={(e) => onEntityIdChange(Number(e.target.value))}
              disabled={disabled}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">-- Select {ENTITY_TYPES[selectedEntityType].label} --</option>
              {entities.map((entity) => (
                <option key={entity.id} value={entity.id}>
                  {entity.name}
                </option>
              ))}
            </select>
          )}

          {/* Selected Entity Info */}
          {selectedEntity && (
            <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-xl">
                  {ENTITY_TYPES[selectedEntityType].icon}
                </span>
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    Selected: {selectedEntity.name}
                  </p>
                  <p className="text-xs text-blue-700">
                    Translatable fields:{' '}
                    {ENTITY_TYPES[selectedEntityType].translatableFields.join(', ')}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EntitySelector
