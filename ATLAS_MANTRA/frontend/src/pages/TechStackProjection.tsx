import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../shared/api'
import { TAG_LABELS, TAG_COLORS, AREA_TAGS } from '../shared/constants'
import { SkeletonPage } from '../components/ui/skeleton'

/**
 * Tech Stack Projection
 * Per MANTRA-L1-PROJECTION-CATALOG-001 §8
 *
 * Displays:
 * - Area tags (FE, BE, DB, INFRA, CICD, API, SECURITY, DEVOPS)
 * - Tech stack (React, FastAPI, PostgreSQL, etc.)
 *
 * Does NOT display:
 * - Preference or recommendation
 * - Technology evaluation
 */

interface Decision {
  decision_id: string
  decision_code: string | null
  statement: string
  group_id: string
  feature_id: string
  tags: string[]
  tech_stack: string[]
}

export default function TechStackProjection() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filterTag = searchParams.get('tag') || ''

  const { data, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: () => api.get('/api/v1/decisions').then(r => r.data),
  })

  if (isLoading) {
    return <SkeletonPage />
  }

  const allDecisions: Decision[] = data?.decisions || []

  // Filter decisions by tag if filter is active
  const decisions: Decision[] = filterTag
    ? allDecisions.filter(d => d.tags?.includes(filterTag))
    : allDecisions

  // Clear filter handler
  const clearFilter = () => {
    setSearchParams({})
  }

  // Group by tags
  const byTag: Record<string, Decision[]> = {}
  AREA_TAGS.forEach(tag => {
    byTag[tag] = []
  })
  byTag['UNTAGGED'] = []

  decisions.forEach(decision => {
    const tags = decision.tags || []
    if (tags.length === 0) {
      byTag['UNTAGGED'].push(decision)
    } else {
      tags.forEach(tag => {
        if (byTag[tag]) {
          byTag[tag].push(decision)
        }
      })
    }
  })

  // Aggregate tech stack across all decisions
  const techStackCount: Record<string, number> = {}
  decisions.forEach(decision => {
    (decision.tech_stack || []).forEach(tech => {
      techStackCount[tech] = (techStackCount[tech] || 0) + 1
    })
  })

  // Sort tech stack by count
  const sortedTechStack = Object.entries(techStackCount)
    .sort((a, b) => b[1] - a[1])

  // Group tech stack by category
  const techCategories: Record<string, string[]> = {
    'Frontend': ['React', 'Vue', 'Angular', 'TypeScript', 'JavaScript', 'Tailwind CSS', 'Vite'],
    'Backend': ['FastAPI', 'Django', 'Flask', 'Node.js', 'Express', 'NestJS', 'Python'],
    'Database': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite', 'TimescaleDB'],
    'Infrastructure': ['Docker', 'Kubernetes', 'Nomad', 'Terraform', 'AWS', 'GCP', 'Azure'],
    'CI/CD': ['GitHub Actions', 'GitLab CI', 'Jenkins', 'ArgoCD'],
  }

  const categorizeTech = (tech: string): string => {
    for (const [category, techs] of Object.entries(techCategories)) {
      if (techs.includes(tech)) return category
    }
    return 'Other'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tech Stack Projection</h1>
        <p className="mt-2 text-gray-600">
          Area tags and technology distribution (no preference judgment)
        </p>
        {filterTag && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm text-gray-600">Filtered by:</span>
            <span className={`px-2 py-1 rounded text-sm font-medium ${TAG_COLORS[filterTag] || 'bg-gray-100 text-gray-700'}`}>
              {TAG_LABELS[filterTag] || filterTag}
            </span>
            <button
              onClick={clearFilter}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Clear filter
            </button>
          </div>
        )}
      </div>

      {/* Area Tags Distribution */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Decisions by Area Tag</h3>
        <div className="grid grid-cols-4 gap-4">
          {AREA_TAGS.map(tag => (
            <div key={tag} className="text-center">
              <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-2 ${TAG_COLORS[tag]}`}>
                {tag}
              </div>
              <div className="text-2xl font-bold text-gray-900">{byTag[tag].length}</div>
              <div className="text-xs text-gray-500">{TAG_LABELS[tag]}</div>
            </div>
          ))}
        </div>
        {byTag['UNTAGGED'].length > 0 && (
          <div className="mt-4 pt-4 border-t text-center">
            <span className="text-gray-400 text-sm">
              {byTag['UNTAGGED'].length} decision(s) without tags
            </span>
          </div>
        )}
      </div>

      {/* Decisions by Tag */}
      <div className="grid grid-cols-2 gap-4">
        {AREA_TAGS.filter(tag => byTag[tag].length > 0).map(tag => (
          <div key={tag} className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${TAG_COLORS[tag]}`}>
                {tag}
              </span>
              <span className="text-sm text-gray-600">{TAG_LABELS[tag]}</span>
              <span className="text-xs text-gray-400 ml-auto">
                {byTag[tag].length} decision(s)
              </span>
            </div>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {byTag[tag].slice(0, 5).map(decision => (
                <Link
                  key={decision.decision_id}
                  to={`/decisions/${decision.decision_id}`}
                  className="block p-2 bg-gray-50 rounded hover:bg-gray-100 text-xs"
                >
                  <div className="font-mono text-indigo-600 font-medium">
                    {decision.decision_code || decision.decision_id.slice(0, 8)}
                  </div>
                  <div className="text-gray-600 truncate">{decision.statement}</div>
                </Link>
              ))}
              {byTag[tag].length > 5 && (
                <div className="text-xs text-gray-400 text-center">
                  +{byTag[tag].length - 5} more
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Tech Stack Overview */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Technology Stack Distribution</h3>
        {sortedTechStack.length > 0 ? (
          <div className="space-y-4">
            {/* Tech Stack Bar Chart */}
            <div className="space-y-2">
              {sortedTechStack.slice(0, 15).map(([tech, count]) => {
                const maxCount = sortedTechStack[0][1]
                const percentage = (count / maxCount) * 100
                const category = categorizeTech(tech)
                const categoryColors: Record<string, string> = {
                  'Frontend': 'bg-blue-500',
                  'Backend': 'bg-green-500',
                  'Database': 'bg-amber-500',
                  'Infrastructure': 'bg-purple-500',
                  'CI/CD': 'bg-orange-500',
                  'Other': 'bg-gray-500',
                }
                return (
                  <div key={tech} className="flex items-center gap-3">
                    <div className="w-32 text-sm text-gray-700 truncate">{tech}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                      <div
                        className={`h-full ${categoryColors[category]} rounded-full`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="w-8 text-xs text-gray-500 text-right">{count}</div>
                    <div className="w-20 text-xs text-gray-400">{category}</div>
                  </div>
                )
              })}
            </div>

            {/* Tech Stack Tags */}
            <div className="pt-4 border-t">
              <div className="text-sm text-gray-600 mb-2">All Technologies:</div>
              <div className="flex flex-wrap gap-2">
                {sortedTechStack.map(([tech, count]) => (
                  <span
                    key={tech}
                    className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-700"
                  >
                    {tech} ({count})
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">
            No tech_stack data available. Add tech_stack to decisions to see distribution.
          </p>
        )}
      </div>

      {/* Tech Stack by Category */}
      {sortedTechStack.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Technologies by Category</h3>
          <div className="grid grid-cols-5 gap-4">
            {Object.entries(techCategories).map(([category, _techs]) => {
              const categoryTechs = sortedTechStack.filter(([tech]) => categorizeTech(tech) === category)
              const totalCount = categoryTechs.reduce((sum, [_, count]) => sum + count, 0)
              return (
                <div key={category} className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-sm font-medium text-gray-700">{category}</div>
                  <div className="text-2xl font-bold text-gray-900 mt-1">{totalCount}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {categoryTechs.length} tech(s)
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Projection Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-800 mb-1">Projection Note</h4>
        <p className="text-xs text-amber-700">
          This projection shows area tags and tech stack distribution factually.
          It does NOT indicate preference or technology recommendation.
          Per MANTRA-L1-PROJECTION-CATALOG-001 §8.
        </p>
      </div>
    </div>
  )
}
