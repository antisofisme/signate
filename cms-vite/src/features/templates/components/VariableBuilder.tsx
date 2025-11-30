/**
 * Variable Builder Component
 * Manage template variables with extraction
 */

import { useState } from 'react'
import { toast } from 'sonner'
import type { VariableType } from '../types/template.types'

interface Variable {
  name: string
  type: VariableType
  default_value?: string
}

interface VariableBuilderProps {
  variables: Record<string, string>
  onChange: (variables: Record<string, string>) => void
  onExtract?: () => void
  disabled?: boolean
  extractedVariables?: string[]
}

export const VariableBuilder = ({
  variables,
  onChange,
  onExtract,
  disabled = false,
  extractedVariables = []
}: VariableBuilderProps) => {
  const [newVarName, setNewVarName] = useState('')
  const [newVarType, setNewVarType] = useState<VariableType>('string')

  const variablesList = Object.entries(variables).map(([name, type]) => ({
    name,
    type: type as VariableType
  }))

  const handleAddVariable = () => {
    if (!newVarName.trim()) return
    if (variables[newVarName]) {
      toast.warning('Variable already exists')
      return
    }

    onChange({
      ...variables,
      [newVarName]: newVarType
    })

    setNewVarName('')
    setNewVarType('string')
  }

  const handleRemoveVariable = (name: string) => {
    const newVars = { ...variables }
    delete newVars[name]
    onChange(newVars)
  }

  const handleUpdateType = (name: string, type: VariableType) => {
    onChange({
      ...variables,
      [name]: type
    })
  }

  const handleApplyExtracted = () => {
    const newVars = { ...variables }
    extractedVariables.forEach(varName => {
      if (!newVars[varName]) {
        newVars[varName] = 'string'
      }
    })
    onChange(newVars)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">Variables</label>
        {onExtract && (
          <button
            type="button"
            onClick={onExtract}
            disabled={disabled}
            className="text-xs px-3 py-1.5 bg-purple-50 text-purple-700 rounded hover:bg-purple-100 disabled:opacity-50"
          >
            🔍 Extract from Content
          </button>
        )}
      </div>

      {/* Extracted variables notification */}
      {extractedVariables.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-green-800">
              Found {extractedVariables.length} variable(s) in template:
            </p>
            <button
              type="button"
              onClick={handleApplyExtracted}
              className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Add All
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {extractedVariables.map(varName => (
              <span key={varName} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                {'{{'}{varName}{'}}'}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Variables list */}
      {variablesList.length > 0 ? (
        <div className="border border-gray-300 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-300">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-700">Variable Name</th>
                <th className="px-4 py-2 text-left font-medium text-gray-700">Type</th>
                <th className="px-4 py-2 text-right font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {variablesList.map((variable) => (
                <tr key={variable.name} className="border-b border-gray-200 last:border-0">
                  <td className="px-4 py-3">
                    <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                      {'{{'}{variable.name}{'}}'}
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={variable.type}
                      onChange={(e) => handleUpdateType(variable.name, e.target.value as VariableType)}
                      disabled={disabled}
                      className="text-sm border border-gray-300 rounded px-2 py-1"
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean</option>
                      <option value="date">Date</option>
                    </select>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => handleRemoveVariable(variable.name)}
                      disabled={disabled}
                      className="text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      🗑️ Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <p className="text-sm text-gray-600">No variables defined yet</p>
          <p className="text-xs text-gray-500 mt-1">Add variables below or extract from template</p>
        </div>
      )}

      {/* Add variable form */}
      <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Add Variable</h4>
        <div className="flex gap-2">
          <input
            type="text"
            value={newVarName}
            onChange={(e) => setNewVarName(e.target.value.replace(/[^a-z0-9_]/gi, ''))}
            placeholder="variable_name"
            disabled={disabled}
            className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm font-mono"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleAddVariable()
              }
            }}
          />
          <select
            value={newVarType}
            onChange={(e) => setNewVarType(e.target.value as VariableType)}
            disabled={disabled}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="string">String</option>
            <option value="number">Number</option>
            <option value="boolean">Boolean</option>
            <option value="date">Date</option>
          </select>
          <button
            type="button"
            onClick={handleAddVariable}
            disabled={disabled || !newVarName.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            ➕ Add
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Variable names can only contain letters, numbers, and underscores
        </p>
      </div>
    </div>
  )
}

export default VariableBuilder
