/**
 * Activation Code Modal Component
 *
 * Displays the 6-digit activation code after TV registration
 * Uses centralized Modal component
 */

import { Check, Copy, Tv } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import { Modal } from '@/shared/components';
import type { Device } from '../../types/device';

interface ActivationCodeModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function ActivationCodeModal({
  isOpen,
  device,
  onClose,
}: ActivationCodeModalProps) {
  const [copied, setCopied] = useState(false);

  if (!device) return null;

  const activationCode = device.unique_code;
  const expiresAt = device.code_expires_at
    ? new Date(device.code_expires_at)
    : null;

  const timeRemaining = expiresAt
    ? Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000))
    : 0;

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;

  // Copy code to clipboard
  const handleCopy = async () => {
    if (!activationCode) return;

    try {
      await navigator.clipboard.writeText(activationCode);
      setCopied(true);
      toast.success('Activation code copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy code');
    }
  };

  // Custom header with success icon
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
          <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            TV Registered Successfully
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {device.device_name}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="md"
      customHeader={customHeader}
    >
      <div className="p-6">
        {/* Activation Code Display */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-xl p-6 mb-6">
          <div className="text-center">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Activation Code
            </p>
            <div className="flex items-center justify-center gap-3 mb-4">
              {/* Code Display */}
              <div className="font-mono text-4xl font-bold text-gray-900 dark:text-white tracking-[0.3em] select-all">
                {activationCode || '------'}
              </div>
              {/* Copy Button */}
              <button
                onClick={handleCopy}
                className="p-2 hover:bg-blue-100 dark:hover:bg-blue-800 rounded-lg transition-colors"
                title="Copy code"
              >
                {copied ? (
                  <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
                ) : (
                  <Copy className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                )}
              </button>
            </div>

            {/* Timer */}
            {timeRemaining > 0 && (
              <div className="flex items-center justify-center gap-2 text-sm">
                <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />
                <span className="text-orange-600 dark:text-orange-400 font-medium">
                  Expires in {minutes}:{seconds.toString().padStart(2, '0')}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="space-y-4 mb-6">
          <div className="flex items-start gap-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <Tv className="w-3 h-3 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                Complete Setup on Your TV
              </h4>
              <ol className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-decimal list-inside">
                <li>Open the app on your TV</li>
                <li>Enter the 6-digit code above when prompted</li>
                <li>Wait for activation to complete</li>
              </ol>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              <strong>Important:</strong> This code will expire in 10 minutes. Complete
              the activation on your TV before it expires.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Got it
          </button>
        </div>
      </div>
    </Modal>
  );
}
