'use client';

/**
 * Artifact Preview Modal Component (Story 3.2, Task 5)
 *
 * Modal wrapper for artifact previews with type-specific rendering.
 */

import { useState } from 'react';
import { X, RotateCcw, Loader2 } from 'lucide-react';
import { useArtifactPreview, useRegenerateArtifact } from '@/lib/hooks/use-artifacts';
import { useTranslation } from '@/lib/hooks/use-translation';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import { QuizPreview } from './QuizPreview';
import { PodcastPreview } from './PodcastPreview';
import { SummaryPreview } from './SummaryPreview';
import { TransformationPreview } from './TransformationPreview';

interface ArtifactPreviewModalProps {
  artifactId: string | null;
  onClose: () => void;
}

export function ArtifactPreviewModal({ artifactId, onClose }: ArtifactPreviewModalProps) {
  const { t } = useTranslation();
  const { data: preview, isLoading, error } = useArtifactPreview(artifactId || undefined);
  const regenerateMutation = useRegenerateArtifact();

  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);

  const handleRegenerate = () => {
    setShowRegenerateDialog(true);
  };

  const handleConfirmRegenerate = async () => {
    if (artifactId) {
      await regenerateMutation.mutateAsync(artifactId);
      setShowRegenerateDialog(false);
      onClose();
    }
  };

  const renderPreview = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-12">
          <p className="text-destructive">
            {t.artifacts?.previewError || 'Failed to load preview'}
          </p>
        </div>
      );
    }

    if (!preview) {
      return null;
    }

    switch (preview.artifact_type) {
      case 'quiz':
        return <QuizPreview preview={preview} />;
      case 'podcast':
        return <PodcastPreview preview={preview} />;
      case 'summary':
        return <SummaryPreview preview={preview} />;
      case 'transformation':
        return <TransformationPreview preview={preview} />;
      default:
        return (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              {t.artifacts?.unsupportedType || 'Unsupported artifact type'}
            </p>
          </div>
        );
    }
  };

  return (
    <>
      <Dialog open={!!artifactId} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>
                {t.artifacts?.previewTitle || 'Artifact Preview'}
              </DialogTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRegenerate}
                  disabled={regenerateMutation.isPending || isLoading}
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  {t.artifacts?.regenerate || 'Regenerate'}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </DialogHeader>

          <div className="mt-4">{renderPreview()}</div>
        </DialogContent>
      </Dialog>

      {/* Regenerate Confirmation Dialog */}
      <AlertDialog open={showRegenerateDialog} onOpenChange={setShowRegenerateDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t.artifacts?.regenerateConfirmTitle || 'Regenerate Artifact?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t.artifacts?.regenerateConfirmDescription ||
                'This will delete the current artifact and generate a new one. This action cannot be undone.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common?.cancel || 'Cancel'}</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmRegenerate}>
              {t.artifacts?.regenerate || 'Regenerate'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
