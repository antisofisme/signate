/**
 * Project Selector Component
 *
 * Dropdown to select and switch between projects within a tenant.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjects } from '../hooks'
import type { Project, ProjectEnvironment } from '../types'

interface ProjectSelectorProps {
  tenantId: string
  tenantSlug: string
  currentProjectId?: string
  onProjectChange?: (project: Project) => void
  showCreateButton?: boolean
}

const ENVIRONMENT_COLORS: Record<ProjectEnvironment, string> = {
  production: 'bg-green-100 text-green-800',
  staging: 'bg-yellow-100 text-yellow-800',
  development: 'bg-blue-100 text-blue-800',
  testing: 'bg-purple-100 text-purple-800',
}

const ENVIRONMENT_LABELS: Record<ProjectEnvironment, string> = {
  production: 'PROD',
  staging: 'STG',
  development: 'DEV',
  testing: 'TEST',
}

export function ProjectSelector({
  tenantId,
  tenantSlug,
  currentProjectId,
  onProjectChange,
  showCreateButton = true,
}: ProjectSelectorProps) {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  const { data, isLoading, error } = useProjects(tenantId)

  const projects = data?.projects || []
  const currentProject = projects.find((p) => p.project_id === currentProjectId)

  const handleSelect = (project: Project) => {
    setIsOpen(false)
    if (onProjectChange) {
      onProjectChange(project)
    }
    // Navigate to the project dashboard
    navigate(`/app/${tenantSlug}/${project.slug}/dashboard`)
  }

  const handleCreateNew = () => {
    setIsOpen(false)
    navigate(`/app/${tenantSlug}/projects/new`)
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">
        Failed to load projects
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading}
      >
        {isLoading ? (
          <span className="text-gray-500">Loading...</span>
        ) : currentProject ? (
          <>
            <span className="font-medium truncate max-w-[150px]">
              {currentProject.name}
            </span>
            <span
              className={`px-1.5 py-0.5 text-xs font-medium rounded ${ENVIRONMENT_COLORS[currentProject.environment]}`}
            >
              {ENVIRONMENT_LABELS[currentProject.environment]}
            </span>
          </>
        ) : (
          <span className="text-gray-500">Select project</span>
        )}
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute left-0 z-20 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
            <div className="p-2 border-b border-gray-100">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide px-2">
                Projects ({projects.length})
              </div>
            </div>

            <div className="max-h-64 overflow-y-auto p-2">
              {projects.length === 0 ? (
                <div className="px-2 py-4 text-sm text-center text-gray-500">
                  No projects yet
                </div>
              ) : (
                projects.map((project) => (
                  <button
                    key={project.project_id}
                    onClick={() => handleSelect(project)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-md hover:bg-gray-100 ${
                      project.project_id === currentProjectId
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700'
                    }`}
                  >
                    <div className="flex flex-col items-start">
                      <span className="font-medium truncate max-w-[140px]">
                        {project.name}
                      </span>
                      {project.description && (
                        <span className="text-xs text-gray-500 truncate max-w-[140px]">
                          {project.description}
                        </span>
                      )}
                    </div>
                    <span
                      className={`px-1.5 py-0.5 text-xs font-medium rounded ${ENVIRONMENT_COLORS[project.environment]}`}
                    >
                      {ENVIRONMENT_LABELS[project.environment]}
                    </span>
                  </button>
                ))
              )}
            </div>

            {showCreateButton && (
              <div className="p-2 border-t border-gray-100">
                <button
                  onClick={handleCreateNew}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 rounded-md hover:bg-blue-50"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  Create New Project
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
