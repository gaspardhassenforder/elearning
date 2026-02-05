'use client';

/**
 * Remove Document Confirmation Dialog (Story 3.6, Task 8)
 *
 * Confirms document removal from module in edit mode.
 * Warns that the source will be permanently removed from the module.
 */

import { useTranslation } from '@/lib/hooks/use-translation';
import { useRemoveDocument } from '@/lib/hooks/use-modules';
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

interface RemoveDocumentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  moduleId: string;
  documentId: string;
  documentTitle: string;
}

export function RemoveDocumentDialog({
  open,
  onOpenChange,
  moduleId,
  documentId,
  documentTitle,
}: RemoveDocumentDialogProps) {
  const { t } = useTranslation();
  const removeDocument = useRemoveDocument(moduleId);

  const handleConfirm = async () => {
    try {
      await removeDocument.mutateAsync(documentId);
      onOpenChange(false);
    } catch (error) {
      // Error already handled by mutation hook with toast
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t.modules.removeDocumentTitle}</AlertDialogTitle>
          <AlertDialogDescription>
            {t.modules.removeDocumentMessage}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* Warning Alert */}
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {t.modules.removeDocumentWarning}
          </AlertDescription>
        </Alert>

        <div className="text-sm text-muted-foreground">
          <strong>{t.common.document || 'Document'}:</strong> {documentTitle}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={removeDocument.isPending}>
            {t.common.cancel}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={removeDocument.isPending}
            className="bg-destructive hover:bg-destructive/90"
          >
            {removeDocument.isPending ? t.common.processing : t.modules.removeDocumentButton}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
