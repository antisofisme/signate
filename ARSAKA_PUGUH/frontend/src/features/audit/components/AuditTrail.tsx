/**
 * Audit Trail Component - Phase A+
 * Shows system event log for visibility
 */

import { useMemo, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getExpandedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ExpandedState,
} from '@tanstack/react-table'
import { useAuditEvents } from '../hooks/useAuditEvents'
import type { AuditEvent } from '../types/AuditEvent'

const columnHelper = createColumnHelper<AuditEvent>()

export function AuditTrail() {
  const { data, isLoading, error } = useAuditEvents()
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'event_at', desc: true }, // Default: newest first
  ])
  const [expanded, setExpanded] = useState<ExpandedState>({})

  // Define columns
  const columns = useMemo(
    () => [
      columnHelper.accessor('event_id', {
        header: 'Event ID',
        cell: (info) => {
          const id = info.getValue()
          return (
            <span className="font-mono text-sm text-blue-600">
              {id.slice(0, 8)}...
            </span>
          )
        },
      }),
      columnHelper.accessor('event_type', {
        header: 'Event Type',
        cell: (info) => (
          <span className="font-medium text-gray-900">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('entity_type', {
        header: 'Entity',
        cell: (info) => (
          <span className="text-sm text-gray-700">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('entity_id', {
        header: 'Entity ID',
        cell: (info) => {
          const id = info.getValue()
          return (
            <span className="font-mono text-xs text-gray-600">
              {id.slice(0, 8)}...
            </span>
          )
        },
      }),
      columnHelper.accessor('actor_type', {
        header: 'Actor',
        cell: (info) => {
          const actorType = info.getValue()
          const actorId = info.row.original.actor_id
          return (
            <div className="text-sm">
              <div className="font-medium">{actorType}</div>
              {actorId && (
                <div className="font-mono text-xs text-gray-500">
                  {actorId.slice(0, 8)}...
                </div>
              )}
            </div>
          )
        },
      }),
      columnHelper.accessor('event_at', {
        header: 'Timestamp',
        cell: (info) => {
          const date = new Date(info.getValue())
          return <span className="text-sm text-gray-600">{date.toLocaleString()}</span>
        },
      }),
      columnHelper.display({
        id: 'expand',
        header: 'Details',
        cell: (info) => (
          <button
            onClick={() => info.row.toggleExpanded()}
            className="text-blue-600 hover:text-blue-800 text-sm font-semibold"
          >
            {info.row.getIsExpanded() ? 'Hide' : 'Show'} Data
          </button>
        ),
      }),
    ],
    []
  )

  // Create table instance
  const table = useReactTable({
    data: data?.events || [],
    columns,
    state: {
      sorting,
      expanded,
    },
    onSortingChange: setSorting,
    onExpandedChange: setExpanded,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
  })

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading audit trail...</div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-800 font-semibold">Error loading audit events</div>
        <div className="text-red-600 text-sm mt-1">
          {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Trail</h1>
        <p className="text-sm text-gray-600 mt-1">
          {data?.total || 0} event(s) recorded
        </p>
        {data?.note && (
          <div className="mt-2 bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
            <strong>Note:</strong> {data.note}
          </div>
        )}
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
              <>
                <tr key={row.id} className="hover:bg-gray-50">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-sm">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
                {/* Expanded row showing full event data */}
                {row.getIsExpanded() && (
                  <tr>
                    <td colSpan={columns.length} className="px-4 py-4 bg-gray-50">
                      <div className="space-y-2">
                        <div className="font-semibold text-sm text-gray-700">
                          Event Data:
                        </div>
                        <div className="bg-white rounded border p-3 font-mono text-xs overflow-auto max-h-96">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(row.original.event_data, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>

        {/* Empty state */}
        {table.getRowModel().rows.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg font-semibold mb-2">No audit events recorded</div>
            <p className="text-sm">
              {data?.note
                ? 'Audit logging models are not yet implemented in Phase A+.'
                : 'Audit events will appear here as system actions occur.'}
            </p>
          </div>
        )}
      </div>

      {/* Phase A+ Note */}
      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
        <strong>Phase A+ Visibility Mode:</strong> Audit trail shows system events for
        visibility only. Full audit logging will be implemented in Phase B.
      </div>
    </div>
  )
}
