/**
 * Send Command Modal Component
 *
 * Send remote commands to devices
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { Send, Loader2, Zap, RotateCw, Camera, Volume2, Sun } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useSendCommand } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

interface SendCommandModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
  onSuccess?: () => void;
}

const COMMAND_OPTIONS = [
  {
    type: 'reboot' as const,
    label: 'Reboot Device',
    description: 'Restart the device completely',
    icon: RotateCw,
    color: 'orange',
    params: [],
  },
  {
    type: 'refresh' as const,
    label: 'Refresh Content',
    description: 'Reload current content without restarting',
    icon: Zap,
    color: 'blue',
    params: [],
  },
  {
    type: 'screenshot' as const,
    label: 'Take Screenshot',
    description: 'Capture current display',
    icon: Camera,
    color: 'purple',
    params: [],
  },
  {
    type: 'volume' as const,
    label: 'Set Volume',
    description: 'Adjust audio volume level',
    icon: Volume2,
    color: 'green',
    params: [{ name: 'level', type: 'number', min: 0, max: 100, default: 50 }],
  },
  {
    type: 'brightness' as const,
    label: 'Set Brightness',
    description: 'Adjust screen brightness',
    icon: Sun,
    color: 'yellow',
    params: [{ name: 'level', type: 'number', min: 0, max: 100, default: 100 }],
  },
];

export function SendCommandModal({
  isOpen,
  device,
  onClose,
  onSuccess,
}: SendCommandModalProps) {
  const [selectedCommand, setSelectedCommand] = useState<
    'reboot' | 'screenshot' | 'volume' | 'brightness' | 'refresh' | null
  >(null);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  const sendCommand = useSendCommand();

  if (!device) return null;

  const selectedOption = COMMAND_OPTIONS.find((cmd) => cmd.type === selectedCommand);

  // Check if device is online
  const isOnline = device.last_seen_at
    ? new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000
    : false;

  // Handle close
  const handleClose = () => {
    if (!sendCommand.isPending) {
      setSelectedCommand(null);
      setParameters({});
      setError(null);
      onClose();
    }
  };

  // Handle send command
  const handleSend = async () => {
    if (!selectedCommand) return;

    setError(null);

    try {
      await sendCommand.mutateAsync({
        id: device.id,
        commandData: {
          command_type: selectedCommand,
          parameters: Object.keys(parameters).length > 0 ? parameters : undefined,
        },
      });

      onSuccess?.();
      handleClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to send command');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Send Command"
      subtitle={device.device_name}
      maxWidth="md"
      footer={
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={handleClose}
            disabled={sendCommand.isPending}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSend}
            disabled={sendCommand.isPending || !selectedCommand}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {sendCommand.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Send Command
              </>
            )}
          </button>
        </div>
      }
    >
      {/* Content */}
      <div className="p-6 space-y-4">
        {/* Offline Warning */}
        {!isOnline && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              <strong>Warning:</strong> Device appears to be offline. Commands will be
              queued and executed when device comes online.
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Command Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Select Command
          </label>
          <div className="space-y-2">
            {COMMAND_OPTIONS.map((command) => {
              const Icon = command.icon;
              const isSelected = selectedCommand === command.type;

              return (
                <button
                  key={command.type}
                  onClick={() => {
                    setSelectedCommand(command.type);
                    // Reset parameters when changing command
                    const defaultParams: Record<string, any> = {};
                    command.params.forEach((param) => {
                      defaultParams[param.name] = param.default;
                    });
                    setParameters(defaultParams);
                    setError(null);
                  }}
                  className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                    isSelected
                      ? 'border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        command.color === 'orange'
                          ? 'bg-orange-100 dark:bg-orange-900'
                          : command.color === 'blue'
                          ? 'bg-blue-100 dark:bg-blue-900'
                          : command.color === 'purple'
                          ? 'bg-purple-100 dark:bg-purple-900'
                          : command.color === 'green'
                          ? 'bg-green-100 dark:bg-green-900'
                          : 'bg-yellow-100 dark:bg-yellow-900'
                      }`}
                    >
                      <Icon
                        className={`w-5 h-5 ${
                          command.color === 'orange'
                            ? 'text-orange-600 dark:text-orange-400'
                            : command.color === 'blue'
                            ? 'text-blue-600 dark:text-blue-400'
                            : command.color === 'purple'
                            ? 'text-purple-600 dark:text-purple-400'
                            : command.color === 'green'
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-yellow-600 dark:text-yellow-400'
                        }`}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {command.label}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                        {command.description}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Parameters */}
        {selectedOption && selectedOption.params.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Parameters
            </label>
            <div className="space-y-3">
              {selectedOption.params.map((param) => (
                <div key={param.name}>
                  <label className="block text-sm text-gray-700 dark:text-gray-300 mb-2 capitalize">
                    {param.name}
                  </label>
                  <input
                    type={param.type}
                    min={param.min}
                    max={param.max}
                    value={parameters[param.name] || param.default}
                    onChange={(e) =>
                      setParameters((prev) => ({
                        ...prev,
                        [param.name]:
                          param.type === 'number'
                            ? parseInt(e.target.value)
                            : e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  {param.min !== undefined && param.max !== undefined && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Range: {param.min} - {param.max}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
