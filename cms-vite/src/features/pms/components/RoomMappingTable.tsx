/**
 * Room Mapping Table Component
 *
 * Table to map PMS rooms to devices
 */

import { useState } from 'react'
import { Link2, Link2Off, Monitor, CheckCircle } from 'lucide-react'
import { usePMSRooms, useMapRoomToDevice, useUnmapRoomFromDevice } from '../hooks/usePMS'
import type { PMSRoom } from '../types/pms.types'

interface RoomMappingTableProps {
  availableDevices: Array<{ id: number; name: string; status: string }>
}

export function RoomMappingTable({ availableDevices }: RoomMappingTableProps) {
  const { data: roomsData, isLoading } = usePMSRooms()
  const mapRoomToDevice = useMapRoomToDevice()
  const unmapRoom = useUnmapRoomFromDevice()
  const [selectedRoom, setSelectedRoom] = useState<number | null>(null)
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null)

  const handleMap = () => {
    if (selectedRoom && selectedDevice) {
      mapRoomToDevice.mutate(
        { room_id: selectedRoom, device_id: selectedDevice },
        {
          onSuccess: () => {
            setSelectedRoom(null)
            setSelectedDevice(null)
          },
        }
      )
    }
  }

  const handleUnmap = (roomId: number) => {
    if (confirm('Are you sure you want to unmap this room from its device?')) {
      unmapRoom.mutate(roomId)
    }
  }

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading rooms...</div>
  }

  const rooms = roomsData?.rooms || []

  return (
    <div className="space-y-4">
      {/* Mapping Form */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 dark:text-white mb-3">Map Room to Device</h4>
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Room
            </label>
            <select
              value={selectedRoom || ''}
              onChange={(e) => setSelectedRoom(Number(e.target.value) || null)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="">Select room...</option>
              {rooms
                .filter((r) => !r.device_id)
                .map((room) => (
                  <option key={room.id} value={room.id}>
                    Room {room.room_number} {room.room_type && `(${room.room_type})`}
                  </option>
                ))}
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Device
            </label>
            <select
              value={selectedDevice || ''}
              onChange={(e) => setSelectedDevice(Number(e.target.value) || null)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="">Select device...</option>
              {availableDevices
                .filter((d) => d.status === 'online')
                .map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.name}
                  </option>
                ))}
            </select>
          </div>

          <button
            onClick={handleMap}
            disabled={!selectedRoom || !selectedDevice || mapRoomToDevice.isPending}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Link2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Rooms Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Room
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Floor
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Mapped Device
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {rooms.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  No rooms found. Sync rooms from PMS first.
                </td>
              </tr>
            ) : (
              rooms.map((room) => (
                <tr key={room.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {room.room_number}
                    </div>
                    {room.building && (
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {room.building}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                    {room.room_type || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                    {room.floor !== undefined ? `Floor ${room.floor}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded ${
                        room.status === 'occupied'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300'
                          : room.status === 'vacant'
                          ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                          : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300'
                      }`}
                    >
                      {room.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {room.device ? (
                      <div className="flex items-center gap-2">
                        <Monitor className="w-4 h-4 text-blue-500" />
                        <span className="text-sm text-gray-900 dark:text-white">
                          {room.device.name}
                        </span>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400 dark:text-gray-500">Not mapped</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    {room.device_id && (
                      <button
                        onClick={() => handleUnmap(room.id)}
                        disabled={unmapRoom.isPending}
                        className="inline-flex items-center gap-1 px-3 py-1 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors disabled:opacity-50"
                      >
                        <Link2Off className="w-4 h-4" />
                        Unmap
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
