/**
 * ConfirmDialog Component
 * Confirmation dialog for destructive/important actions
 */
import { useTranslation } from 'react-i18next';
import { AlertTriangle, Trash2, Info } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import Button from '../common/Button';

type ConfirmVariant = 'danger' | 'warning' | 'info';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel?: () => void;
  isLoading?: boolean;
  variant?: ConfirmVariant;
}

const variantConfig = {
  danger: {
    icon: Trash2,
    iconClass: 'text-red-500 bg-red-100 dark:bg-red-900/20',
    buttonVariant: 'danger' as const,
  },
  warning: {
    icon: AlertTriangle,
    iconClass: 'text-amber-500 bg-amber-100 dark:bg-amber-900/20',
    buttonVariant: 'warning' as const,
  },
  info: {
    icon: Info,
    iconClass: 'text-blue-500 bg-blue-100 dark:bg-blue-900/20',
    buttonVariant: 'primary' as const,
  },
};

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  isLoading = false,
  variant = 'danger',
}: ConfirmDialogProps) {
  const { t } = useTranslation();
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };

  const handleConfirm = () => {
    onConfirm();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader onClose={handleCancel}>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="flex items-start gap-4">
            <div
              className={cn(
                'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                config.iconClass
              )}
            >
              <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <DialogDescription className="mt-0 text-gray-600 dark:text-gray-400">
                {description}
              </DialogDescription>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            onClick={handleCancel}
            disabled={isLoading}
          >
            {cancelLabel || t('common.cancel', 'Cancel')}
          </Button>
          <Button
            type="button"
            variant={config.buttonVariant}
            onClick={handleConfirm}
            disabled={isLoading}
            loading={isLoading}
          >
            {confirmLabel || t('common.confirm', 'Confirm')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
