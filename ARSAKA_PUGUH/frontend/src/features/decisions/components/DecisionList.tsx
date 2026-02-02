/**
 * Decision List Component - Phase A+
 * Simple table showing all decisions (no pagination)
 */

import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table'
import { useState } from 'react'
import { useDecisions } from '../hooks/useDecisions'
import type { Decision } from '../types/Decision'

const columnHelper = createColumnHelper<Decision>()

export function DecisionList() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useDecisions()
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'created_at', desc: true } // Default: newest first
  ])

  // Define columns
  const columns = useMemo(
    () => [
      columnHelper.accessor('decision_id', {
        header: 'Decision ID',
        cell: (info) => {
          const id = info.getValue()
          // Truncate UUID for display
          return (
            <span className="font-mono text-sm text-blue-600">
              {id.slice(0, 8)}...
            </span>
          )
        },
      }),
      columnHelper.accessor('decision_type', {
        header: 'Type',
        cell: (info) => (
          <span className="font-medium">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('context', {
        header: 'Amount',
        cell: (info) => {
          const context = info.getValue()
          const amount = context?.amount
          return amount ? (
            <span className="font-semibold">${amount.toLocaleString()}</span>
          ) : (
            <span className="text-gray-400">-</span>
          )
        },
      }),
      columnHelper.accessor('outcome_label', {
        header: 'Outcome',
        cell: (info) => {
          const outcome = info.row.original.outcome
          const label = info.getValue()

          const colors = {
            ALLOWED: 'bg-green-100 text-green-800',
            DENIED: 'bg-red-100 text-red-800',
            REQUIRE_APPROVAL: 'bg-yellow-100 text-yellow-800',
          }

          return (
            <span
              className={`px-2 py-1 rounded text-xs font-semibold ${
                colors[outcome] || 'bg-gray-100 text-gray-800'
              }`}
            >
              {label}
            </span>
          )
        },
      }),
      columnHelper.accessor('approval_workflow_id', {
        header: 'Status',
        cell: (info) => {
          const workflowId = info.getValue()
          return workflowId ? (
            <span className="text-xs text-gray-600">Pending Approval</span>
          ) : (
            <span className="text-xs text-gray-600">Completed</span>
          )
        },
      }),
      columnHelper.accessor('created_at', {
        header: 'Created At',
        cell: (info) => {
          const date = new Date(info.getValue())
          return (
            <span className="text-sm text-gray-600">
              {date.toLocaleString()}
            </span>
          )
        },
      }),
    ],
    []
  )

  // Create table instance
  const table = useReactTable({
    data: data?.decisions || [],
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading decisions...</div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-800 font-semibold">Error loading decisions</div>
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
          <h1 className="text-2xl font-bold text-gray-900">Decisions</h1>
          <p className="text-sm text-gray-600 mt-1">
            {data?.total || 0} decision(s) total
          </p>
        </div>
        <button
          onClick={() => navigate('/decisions/new')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-semibold"
        >
          Create Decision
        </button>
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
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      {header.column.getIsSorted() && (
                        <span>
                          {header.column.getIsSorted() === 'desc' ? '↓' : '↑'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => navigate(`/app/decisions/${row.original.decision_id}`)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3 text-sm">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        {/* Empty state */}
        {table.getRowModel().rows.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No decisions found. Create your first decision to get started.
          </div>
        )}
      </div>

      {/* Phase A+ Note */}
      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
        <strong>Phase A+ Visibility Mode:</strong> No pagination, advanced filters, or bulk
        actions. All decisions shown in simple list.
      </div>
    </div>
  )
}
