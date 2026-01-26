/**
 * Approval Inbox Component - Phase A+
 * Shows pending approval requests
 */

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table'
import { useWorkflows } from '../hooks/useWorkflows'
import type { WorkflowListItem } from '../types/Workflow'

const columnHelper = createColumnHelper<WorkflowListItem>()

export function ApprovalInbox() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useWorkflows('pending')
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'created_at', desc: true }, // Default: oldest first (FIFO)
  ])

  // Define columns
  const columns = useMemo(
    () => [
      columnHelper.accessor('decision_id', {
        header: 'Decision ID',
        cell: (info) => {
          const id = info.getValue()
          return (
            <span className="font-mono text-sm text-blue-600">
              {id.slice(0, 8)}...
            </span>
          )
        },
      }),
      columnHelper.accessor((row) => row.decision?.decision_type, {
        id: 'decision_type',
        header: 'Type',
        cell: (info) => <span className="font-medium">{info.getValue()}</span>,
      }),
      columnHelper.accessor((row) => row.decision?.context, {
        id: 'decision_context',
        header: 'Details',
        cell: (info) => {
          const context = info.getValue()
          const type = info.row.original.decision?.decision_type

          // Financial decisions - show amount
          if (context?.amount) {
            return <span className="font-semibold">${context.amount.toLocaleString()}</span>
          }

          // Leave request - show days
          if (type === 'leave_request' && context?.days) {
            return <span className="text-gray-700">{context.days} days</span>
          }

          // Access request - show resource
          if (type === 'access_request' && context?.resource) {
            return <span className="text-gray-700">{context.resource}</span>
          }

          // Policy change - show policy name
          if (type === 'policy_change' && context?.policy_name) {
            return <span className="text-gray-700">{context.policy_name}</span>
          }

          // Default - show dash
          return <span className="text-gray-400">-</span>
        },
      }),
      columnHelper.accessor('current_state_label', {
        header: 'State',
        cell: (info) => (
          <span className="px-2 py-1 rounded text-xs font-semibold bg-yellow-100 text-yellow-800">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor('approver_role', {
        header: 'Requires',
        cell: (info) => (
          <span className="text-sm text-gray-700">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('created_at', {
        header: 'Created At',
        cell: (info) => {
          const date = new Date(info.getValue())
          return <span className="text-sm text-gray-600">{date.toLocaleString()}</span>
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: () => (
          <div className="flex gap-2">
            <button
              disabled
              className="px-3 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold cursor-not-allowed opacity-50"
              title="Phase A+ - View only"
            >
              Approve
            </button>
            <button
              disabled
              className="px-3 py-1 bg-red-100 text-red-700 rounded text-xs font-semibold cursor-not-allowed opacity-50"
              title="Phase A+ - View only"
            >
              Deny
            </button>
          </div>
        ),
      }),
    ],
    []
  )

  // Create table instance
  const table = useReactTable({
    data: data?.workflows || [],
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
        <div className="text-gray-500">Loading approval inbox...</div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-800 font-semibold">Error loading workflows</div>
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
          <h1 className="text-2xl font-bold text-gray-900">Approval Inbox</h1>
          <p className="text-sm text-gray-600 mt-1">
            {data?.total || 0} pending approval(s)
          </p>
        </div>
        <button
          onClick={() => navigate('/decisions')}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-semibold"
        >
          View All Decisions
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
                onClick={() => navigate(`/decisions/${row.original.decision_id}`)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-4 py-3 text-sm"
                    onClick={(e) => {
                      // Prevent navigation when clicking action buttons
                      if (
                        cell.column.id === 'actions' &&
                        (e.target as HTMLElement).tagName === 'BUTTON'
                      ) {
                        e.stopPropagation()
                      }
                    }}
                  >
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
            <div className="text-lg font-semibold mb-2">No pending approvals</div>
            <p className="text-sm">
              All workflows have been completed or there are no decisions requiring approval.
            </p>
          </div>
        )}
      </div>

      {/* Phase A+ Note */}
      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
        <strong>Phase A+ Visibility Mode:</strong> Approve/Deny buttons are disabled. This view
        shows pending workflows for visibility only. Click a row to see decision details.
      </div>
    </div>
  )
}
