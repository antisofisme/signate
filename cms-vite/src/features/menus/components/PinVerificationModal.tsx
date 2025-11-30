/**
 * PIN Verification Modal
 * Modal for verifying organization PIN before sensitive operations like menu deletion
 */

import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AlertTriangle, Loader2, ShieldCheck, Lock } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { menuApi } from '../api/menuApi';
import { cn } from '@/lib/utils';

interface PinVerificationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVerified: () => void;
  title?: string;
  description?: string;
  menuName?: string;
}

export function PinVerificationModal({
  open,
  onOpenChange,
  onVerified,
  title = 'PIN Verification Required',
  description = 'Please enter your organization PIN to confirm this action.',
  menuName,
}: PinVerificationModalProps) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (open) {
      setPin('');
      setError(null);
      // Focus input after modal animation
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  const verifyMutation = useMutation({
    mutationFn: (pinValue: string) => menuApi.verifyPIN(pinValue),
    onSuccess: (data) => {
      if (data.verified) {
        onVerified();
        onOpenChange(false);
      } else {
        setError('Invalid PIN. Please try again.');
        setPin('');
        inputRef.current?.focus();
      }
    },
    onError: () => {
      setError('Failed to verify PIN. Please try again.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pin.length < 6) {
      setError('PIN must be at least 6 characters');
      return;
    }
    setError(null);
    verifyMutation.mutate(pin);
  };

  const handleClose = () => {
    if (!verifyMutation.isPending) {
      onOpenChange(false);
    }
  };

  // Custom header with lock icon
  const customHeader = (
    <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-full bg-yellow-100 dark:bg-yellow-900/30">
          <Lock className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {description}
            {menuName && (
              <span className="block mt-1 font-medium text-gray-900 dark:text-white">
                Menu: "{menuName}"
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={open}
      onClose={handleClose}
      maxWidth="sm"
      showHeader={false}
      customHeader={customHeader}
      closeOnBackdropClick={!verifyMutation.isPending}
    >
      <form onSubmit={handleSubmit}>
        <div className="px-6 py-4 space-y-4">
          {/* PIN Input */}
          <div className="space-y-2">
            <label htmlFor="pin" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Organization PIN
            </label>
            <input
              ref={inputRef}
              id="pin"
              type="password"
              placeholder="Enter 6-digit PIN"
              value={pin}
              onChange={(e) => {
                setPin(e.target.value);
                setError(null);
              }}
              maxLength={8}
              className={cn(
                'w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center text-lg tracking-widest font-mono',
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                error
                  ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 dark:border-gray-600'
              )}
              disabled={verifyMutation.isPending}
            />
            {error && (
              <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {error}
              </div>
            )}
          </div>

          {/* Warning Box */}
          <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-amber-800 dark:text-amber-200">
                <p className="font-medium">Warning</p>
                <p>This action cannot be undone. The menu and all its items will be permanently deleted.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={verifyMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="danger"
            disabled={pin.length < 6 || verifyMutation.isPending}
          >
            {verifyMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <ShieldCheck className="mr-2 h-4 w-4" />
                Verify & Delete
              </>
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
