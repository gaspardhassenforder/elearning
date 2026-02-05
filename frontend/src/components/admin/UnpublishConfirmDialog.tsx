'use client';

/**
 * Unpublish Confirmation Dialog (Story 3.6, Task 6)
 *
 * Displays warning about learner impact when admin wants to edit a published module.
 * Confirms unpublish action before reverting module to draft status.
 */

import { useTranslation } from '@/lib/hooks/use-translation';
import { useUnpublishModule } from '@/lib/hooks/use-modules';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';

interface UnpublishConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  moduleId: string;
  moduleName: string;
}

export function UnpublishConfirmDialog({
  open,
  onOpenChange,
  moduleId,
  moduleName,
}: UnpublishConfirmDialogProps) {
  const { t } = useTranslation();
  const unpublishModule = useUnpublishModule();

  const handleConfirm = async () => {
    try {
      await unpublishModule.mutateAsync(moduleId);
      onOpenChange(false);
    } catch (error) {
      // Error already handled by mutation hook with toast
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t.modules.unpublishConfirmTitle}</AlertDialogTitle>
          <AlertDialogDescription>
            {t.modules.unpublishConfirmMessage}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* Warning Alert */}
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {t.modules.unpublishConfirmWarning}
          </AlertDescription>
        </Alert>

        <div className="text-sm text-muted-foreground">
          <strong>{t.common.warning}:</strong> {moduleName}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={unpublishModule.isPending}>
            {t.common.cancel}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={unpublishModule.isPending}
            className="bg-destructive hover:bg-destructive/90"
          >
            {unpublishModule.isPending ? t.common.processing : t.modules.unpublishButton}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
