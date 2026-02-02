/**
 * Rule List Component - Phase A+
 */

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table'
import { useRules } from '../hooks/useRules'
import { useFunctionalAreas } from '../../configuration/hooks/useConfig'
import type { Rule } from '../types/Rule'

const columnHelper = createColumnHelper<Rule>()

export function RuleList() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useRules()
  const { data: functionalAreasData } = useFunctionalAreas(true) // Fetch functional areas for display/filter
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'evaluation_sequence', desc: false },
  ])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])

  // Create lookup map for functional areas
  const functionalAreasMap = useMemo(() => {
    if (!functionalAreasData?.functional_areas) return {}
    return Object.fromEntries(
      functionalAreasData.functional_areas.map(area => [area.functional_area_id, area])
    )
  }, [functionalAreasData])

  const columns = useMemo(
    () => [
      columnHelper.accessor('rule_name', {
        header: 'Rule Name',
        cell: (info) => <span className="font-semibold">{info.getValue()}</span>,
      }),
      columnHelper.accessor('decision_type', {
        header: 'Decision Type',
        cell: (info) => <span className="font-mono text-sm">{info.getValue()}</span>,
      }),
      columnHelper.accessor('functional_area_id', {
        id: 'functional_area_id',
        header: 'Functional Area',
        cell: (info) => {
          const areaId = info.getValue()
          if (!areaId) return <span className="text-sm text-gray-400">-</span>
          const area = functionalAreasMap[areaId]
          return area ? (
            <span className="text-sm text-gray-700">{area.name}</span>
          ) : (
            <span className="text-sm text-gray-400">Unknown</span>
          )
        },
      }),
      columnHelper.accessor('conditions', {
        header: 'Conditions',
        cell: (info) => {
          const conditions = info.getValue()
          const key = Object.keys(conditions)[0]
          const value = conditions[key]
          return (
            <span className="text-sm text-gray-600">
              {key} {value.operator} {value.value || `${value.min}-${value.max}`}
            </span>
          )
        },
      }),
      columnHelper.accessor('action', {
        header: 'Action',
        cell: (info) => {
          const action = info.getValue()
          const outcomeColors = {
            ALLOWED: 'bg-green-100 text-green-800',
            DENIED: 'bg-red-100 text-red-800',
            REQUIRE_APPROVAL: 'bg-yellow-100 text-yellow-800',
          }
          return (
            <div className="flex flex-col gap-1">
              <span className={`px-2 py-1 rounded text-xs font-semibold inline-block w-fit ${outcomeColors[action.outcome]}`}>
                {action.outcome}
              </span>
              {action.approver_role && (
                <span className="text-xs text-gray-600">→ {action.approver_role}</span>
              )}
            </div>
          )
        },
      }),
      columnHelper.accessor('status', {
        header: 'Status',
        cell: (info) => {
          const status = info.getValue()
          const statusColors = {
            ACTIVE: 'bg-green-100 text-green-800',
            DRAFT: 'bg-gray-100 text-gray-800',
            DEPRECATED: 'bg-orange-100 text-orange-800',
            DELETED: 'bg-red-100 text-red-800',
          }
          return (
            <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[status]}`}>
              {status}
            </span>
          )
        },
      }),
      columnHelper.accessor('evaluation_sequence', {
        header: 'Seq',
        cell: (info) => (
          <span className="font-mono text-sm text-gray-600">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('created_at', {
        header: 'Created',
        cell: (info) => {
          const date = new Date(info.getValue())
          return <span className="text-sm text-gray-600">{date.toLocaleDateString()}</span>
        },
      }),
    ],
    [functionalAreasMap]
  )

  const table = useReactTable({
    data: data?.rules || [],
    columns,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading rules...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-800 font-semibold">Error loading rules</div>
        <div className="text-red-600 text-sm mt-1">
          {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Decision Rules</h1>
          <p className="text-sm text-gray-600 mt-1">
            {data?.total || 0} rule(s) configured
          </p>
        </div>
        <button
          onClick={() => navigate('/rules/create')}
          disabled
          className="bg-blue-600 text-white px-4 py-2 rounded font-semibold opacity-50 cursor-not-allowed"
          title="Phase A+ - View only"
        >
          + Create Rule
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white border rounded p-4">
        <div className="flex gap-4 items-center">
          <label className="text-sm font-medium text-gray-700">Filter by Functional Area:</label>
          <select
            value={columnFilters.find(f => f.id === 'functional_area_id')?.value as string || ''}
            onChange={(e) => {
              const value = e.target.value
              setColumnFilters(prev => {
                if (value === '') {
                  return prev.filter(f => f.id !== 'functional_area_id')
                }
                const existing = prev.find(f => f.id === 'functional_area_id')
                if (existing) {
                  return prev.map(f => f.id === 'functional_area_id' ? { id: 'functional_area_id', value } : f)
                }
                return [...prev, { id: 'functional_area_id', value }]
              })
            }}
            className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Areas</option>
            {functionalAreasData?.functional_areas.map(area => (
              <option key={area.functional_area_id} value={area.functional_area_id}>
                {area.name}
              </option>
            ))}
          </select>
          {columnFilters.length > 0 && (
            <button
              onClick={() => setColumnFilters([])}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border rounded overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-2">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() && (
                        <span>{header.column.getIsSorted() === 'desc' ? '↓' : '↑'}</span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3 text-sm">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        {table.getRowModel().rows.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg font-semibold mb-2">No rules configured</div>
            <p className="text-sm">Create your first rule to get started.</p>
          </div>
        )}
      </div>

      {/* Phase A+ Note */}
      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
        <strong>Phase A+ Visibility Mode:</strong> Rule creation/editing is disabled.
        This view shows configured rules for visibility only.
      </div>
    </div>
  )
}
