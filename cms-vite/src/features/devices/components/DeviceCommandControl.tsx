/**
 * Device Command Control Component
 *
 * LAYER 1: PRESENTATION
 * Remote command sending and history for devices
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  RefreshCw,
  Power,
  Settings,
  Trash2,
  Camera,
  List as ListIcon,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { toast } from '@/shared/utils/toast';
import { formatDistanceToNow } from 'date-fns';
import { getApiErrorMessage } from '@/shared/utils/types';
import { Modal, Button } from '@/shared/components';
import { deviceCommandApi } from '../api/commands';
import type { DeviceCommand, CommandType, SendCommandRequest } from '../types/commands';

interface DeviceCommandControlProps {
  deviceId: number;
  deviceName: string;
}

export function DeviceCommandControl({
  deviceId,
  deviceName,
}: DeviceCommandControlProps) {
  const [showHistory, setShowHistory] = useState(false);
  const [confirmCommand, setConfirmCommand] = useState<CommandType | null>(null);
  const queryClient = useQueryClient();

  // Fetch command history
  const { data: commandHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['device-commands', deviceId],
    queryFn: () => deviceCommandApi.getCommands(deviceId, { limit: 20 }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Send command mutation
  const sendCommandMutation = useMutation({
    mutationFn: (request: SendCommandRequest) =>
      deviceCommandApi.sendCommand(deviceId, request),
    onSuccess: (data) => {
      toast.success(`Command "${data.command_type}" sent successfully`);
      queryClient.invalidateQueries({ queryKey: ['device-commands', deviceId] });
      setConfirmCommand(null);
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to send command. Please try again.'));
    },
  });

  const handleSendCommand = (commandType: CommandType, needsConfirmation: boolean) => {
    if (needsConfirmation) {
      setConfirmCommand(commandType);
      return;
    }

    sendCommandMutation.mutate({
      command_type: commandType,
      priority: 5,
      expires_in_minutes: 60,
    });
  };

  const handleConfirmCommand = () => {
    if (confirmCommand) {
      sendCommandMutation.mutate({
        command_type: confirmCommand,
        priority: 8, // Higher priority for confirmed commands
        expires_in_minutes: 60,
      });
    }
  };

  // Command button configs
  const commandButtons: Array<{
    type: CommandType;
    label: string;
    icon: React.ReactNode;
    color: string;
    needsConfirmation: boolean;
    description: string;
  }> = [
    {
      type: 'refresh_content',
      label: 'Refresh Content',
      icon: <RefreshCw className="w-4 h-4" />,
      color: 'bg-blue-600 hover:bg-blue-700',
      needsConfirmation: false,
      description: 'Reload content without restarting player',
    },
    {
      type: 'update_playlist',
      label: 'Update Playlist',
      icon: <ListIcon className="w-4 h-4" />,
      color: 'bg-green-600 hover:bg-green-700',
      needsConfirmation: false,
      description: 'Fetch latest playlist from server',
    },
    {
      type: 'clear_cache',
      label: 'Clear Cache',
      icon: <Trash2 className="w-4 h-4" />,
      color: 'bg-yellow-600 hover:bg-yellow-700',
      needsConfirmation: false,
      description: 'Clear browser cache',
    },
    {
      type: 'screenshot',
      label: 'Screenshot',
      icon: <Camera className="w-4 h-4" />,
      color: 'bg-purple-600 hover:bg-purple-700',
      needsConfirmation: false,
      description: 'Capture current screen',
    },
    {
      type: 'update_settings',
      label: 'Update Settings',
      icon: <Settings className="w-4 h-4" />,
      color: 'bg-indigo-600 hover:bg-indigo-700',
      needsConfirmation: false,
      description: 'Apply latest device settings',
    },
    {
      type: 'reboot',
      label: 'Reboot',
      icon: <Power className="w-4 h-4" />,
      color: 'bg-red-600 hover:bg-red-700',
      needsConfirmation: true,
      description: 'Restart device (requires confirmation)',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'executed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'pending':
      case 'sent':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'expired':
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'executed':
        return 'text-green-600 bg-green-100 dark:bg-green-900/30';
      case 'failed':
        return 'text-red-600 bg-red-100 dark:bg-red-900/30';
      case 'pending':
      case 'sent':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
      case 'expired':
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Command Buttons */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Remote Commands
          </h3>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2"
          >
            <ListIcon className="w-4 h-4" />
            {showHistory ? 'Hide History' : 'Show History'}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {commandButtons.map((btn) => (
            <button
              key={btn.type}
              onClick={() => handleSendCommand(btn.type, btn.needsConfirmation)}
              disabled={sendCommandMutation.isPending}
              className={`${btn.color} text-white p-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex flex-col items-center gap-2`}
              title={btn.description}
            >
              {btn.icon}
              <span className="text-xs font-medium text-center">{btn.label}</span>
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
          Commands are queued and executed by the device during next heartbeat (within 30
          seconds).
        </p>
      </div>

      {/* Confirmation Dialog */}
      {confirmCommand && (
        <Modal
          isOpen={true}
          onClose={() => setConfirmCommand(null)}
          title="Confirm Command"
          maxWidth="md"
          closeOnBackdropClick={!sendCommandMutation.isPending}
          footer={
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <Button
                variant="secondary"
                onClick={() => setConfirmCommand(null)}
                disabled={sendCommandMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmCommand}
                disabled={sendCommandMutation.isPending}
                loading={sendCommandMutation.isPending}
                leftIcon={<Send className="w-4 h-4" />}
              >
                {sendCommandMutation.isPending ? 'Sending...' : 'Send Command'}
              </Button>
            </div>
          }
        >
          <div className="p-6">
            <p className="text-gray-700 dark:text-gray-300 mb-2">
              Are you sure you want to send <strong>{confirmCommand}</strong> command to:
            </p>
            <p className="text-gray-900 dark:text-white font-semibold mb-6">
              {deviceName}
            </p>
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              This action may interrupt content playback temporarily.
            </p>
          </div>
        </Modal>
      )}

      {/* Command History */}
      {showHistory && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Command History
          </h3>

          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : commandHistory && commandHistory.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Command
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Created
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Executed
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {commandHistory.items.map((cmd: DeviceCommand) => (
                    <tr
                      key={cmd.id}
                      className="border-b border-gray-100 dark:border-gray-700 last:border-0"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {cmd.command_type}
                          </span>
                          {cmd.reason && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              ({cmd.reason})
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(cmd.status)}
                          <span
                            className={`text-xs font-medium px-2 py-1 rounded ${getStatusColor(
                              cmd.status
                            )}`}
                          >
                            {cmd.status}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                        {formatDistanceToNow(new Date(cmd.created_at))} ago
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                        {cmd.executed_at
                          ? formatDistanceToNow(new Date(cmd.executed_at)) + ' ago'
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
              No commands sent yet
            </p>
          )}
        </div>
      )}
    </div>
  );
}
