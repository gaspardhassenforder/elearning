'use client';

/**
 * Artifact Generation Panel Component (Story 3.2, Task 4)
 *
 * Batch artifact generation with status tracking per artifact type.
 * Polls backend for completion and displays inline errors with retry.
 *
 * Extended in Story 3.6, Task 9 to support individual artifact regeneration in edit mode.
 */

import { useState, useEffect } from 'react';
import { Sparkles, Check, AlertCircle, Loader2, FileText, Mic, BookOpen, RotateCw } from 'lucide-react';
import { useGenerateAllArtifacts, useArtifacts } from '@/lib/hooks/use-artifacts';
import { useModuleCreationStore } from '@/lib/stores/module-creation-store';
import { useTranslation } from '@/lib/hooks/use-translation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
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
import { cn } from '@/lib/utils';

interface ArtifactGenerationPanelProps {
  moduleId: string;
  onComplete?: () => void;
}

interface ArtifactStatus {
  type: 'quiz' | 'summary' | 'podcast';
  label: string;
  icon: typeof FileText;
  status: 'pending' | 'generating' | 'completed' | 'error';
  error?: string;
  id?: string;
}

export function ArtifactGenerationPanel({ moduleId, onComplete }: ArtifactGenerationPanelProps) {
  const { t } = useTranslation();
  const generateMutation = useGenerateAllArtifacts(moduleId);
  const { data: artifacts } = useArtifacts(moduleId, { pollingInterval: 2000 });
  const { isEditMode } = useModuleCreationStore();

  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [artifactStatuses, setArtifactStatuses] = useState<ArtifactStatus[]>([
    { type: 'quiz', label: 'Quiz', icon: FileText, status: 'pending' },
    { type: 'summary', label: 'Summary', icon: BookOpen, status: 'pending' },
    { type: 'podcast', label: 'Podcast', icon: Mic, status: 'pending' },
  ]);

  // Regenerate individual artifact dialog state (Story 3.6, Task 9)
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);
  const [artifactToRegenerate, setArtifactToRegenerate] = useState<ArtifactStatus | null>(null);

  // Update statuses from generation response
  useEffect(() => {
    if (generateMutation.data) {
      const data = generateMutation.data;

      setArtifactStatuses((prev) =>
        prev.map((artifact) => {
          if (artifact.type === 'quiz') {
            return {
              ...artifact,
              status: data.quiz.status as any,
              error: data.quiz.error,
              id: data.quiz.id,
            };
          }
          if (artifact.type === 'summary') {
            return {
              ...artifact,
              status: data.summary.status as any,
              error: data.summary.error,
              id: data.summary.id,
            };
          }
          if (artifact.type === 'podcast') {
            return {
              ...artifact,
              status: data.podcast.status as any,
              error: data.podcast.error,
            };
          }
          return artifact;
        })
      );
    }
  }, [generateMutation.data]);

  // Update statuses from polling artifacts list
  useEffect(() => {
    if (artifacts && artifacts.length > 0) {
      setArtifactStatuses((prev) =>
        prev.map((artifact) => {
          const found = artifacts.find((a) => a.artifact_type === artifact.type);
          if (found && artifact.status === 'generating') {
            // Check if processing is complete
            if (artifact.type === 'podcast') {
              // Podcast is async - check if command_id has been replaced with actual artifact_id
              const isPending = found.artifact_id.startsWith('command:');
              return {
                ...artifact,
                status: isPending ? 'generating' : 'completed',
                id: found.artifact_id,
              };
            } else {
              // Quiz and summary are sync - if they exist, they're complete
              return {
                ...artifact,
                status: 'completed',
                id: found.artifact_id,
              };
            }
          }
          return artifact;
        })
      );
    }
  }, [artifacts]);

  const handleGenerateClick = () => {
    setShowConfirmDialog(true);
  };

  const handleConfirmGenerate = async () => {
    setShowConfirmDialog(false);

    // Reset statuses to generating
    setArtifactStatuses((prev) =>
      prev.map((artifact) => ({
        ...artifact,
        status: 'generating',
        error: undefined,
      }))
    );

    // Trigger generation
    generateMutation.mutate();
  };

  const handleRetry = () => {
    handleConfirmGenerate();
  };

  // Handle individual artifact regeneration (Story 3.6, Task 9)
  const handleRegenerateClick = (artifact: ArtifactStatus) => {
    setArtifactToRegenerate(artifact);
    setShowRegenerateDialog(true);
  };

  const handleConfirmRegenerate = async () => {
    setShowRegenerateDialog(false);

    if (!artifactToRegenerate) return;

    // Set only this artifact to generating status
    setArtifactStatuses((prev) =>
      prev.map((a) =>
        a.type === artifactToRegenerate.type
          ? { ...a, status: 'generating', error: undefined }
          : a
      )
    );

    // Trigger generation (same endpoint generates all, but only this one will update)
    generateMutation.mutate();
  };

  const isGenerating = artifactStatuses.some((a) => a.status === 'generating');
  const hasErrors = artifactStatuses.some((a) => a.status === 'error');
  const allCompleted = artifactStatuses.every((a) => a.status === 'completed');

  // Notify parent when all complete
  useEffect(() => {
    if (allCompleted && onComplete) {
      onComplete();
    }
  }, [allCompleted, onComplete]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {t.artifacts?.generateTitle || 'Generate Learning Artifacts'}
          </CardTitle>
          <CardDescription>
            {t.artifacts?.generateDescription ||
              'Generate quizzes, summaries, and podcasts from your uploaded documents'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Generate Button */}
          <div className="flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              {t.artifacts?.generateHint ||
                'This will create AI-powered learning materials based on your documents'}
            </p>
            <Button
              onClick={handleGenerateClick}
              disabled={isGenerating || allCompleted}
              size="lg"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              {isGenerating
                ? t.artifacts?.generating || 'Generating...'
                : allCompleted
                  ? t.artifacts?.generated || 'Generated'
                  : t.artifacts?.generateAll || 'Generate All'}
            </Button>
          </div>

          {/* Artifact Status List */}
          <div className="space-y-4">
            {artifactStatuses.map((artifact) => (
              <ArtifactStatusItem
                key={artifact.type}
                artifact={artifact}
                isEditMode={isEditMode}
                onRegenerate={() => handleRegenerateClick(artifact)}
              />
            ))}
          </div>

          {/* Error Summary */}
          {hasErrors && !isGenerating && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {t.artifacts?.generateError ||
                  'Some artifacts failed to generate. Click Retry to try again.'}
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-4"
                  onClick={handleRetry}
                >
                  {t.common?.retry || 'Retry'}
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Success Message */}
          {allCompleted && (
            <Alert>
              <Check className="h-4 w-4" />
              <AlertDescription>
                {t.artifacts?.generateComplete ||
                  'All artifacts generated successfully! You can now preview them or continue to the next step.'}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t.artifacts?.generateConfirmTitle || 'Generate Artifacts?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t.artifacts?.generateConfirmDescription ||
                'This will generate quizzes, summaries, and podcasts from your documents. This may take 1-2 minutes.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common?.cancel || 'Cancel'}</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmGenerate}>
              {t.common?.continue || 'Continue'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Regenerate Individual Artifact Dialog (Story 3.6, Task 9) */}
      {artifactToRegenerate && (
        <AlertDialog open={showRegenerateDialog} onOpenChange={setShowRegenerateDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {t.artifacts?.regenerateConfirmTitle || 'Regenerate Artifact?'}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {t.artifacts?.regenerateConfirmDescription ||
                  'This will regenerate the artifact and replace the existing one.'}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {t.artifacts?.regenerateWarning ||
                  'The existing artifact will be permanently replaced. This action cannot be undone.'}
              </AlertDescription>
            </Alert>
            <div className="text-sm text-muted-foreground">
              <strong>{t.common?.type || 'Type'}:</strong> {artifactToRegenerate.label}
            </div>
            <AlertDialogFooter>
              <AlertDialogCancel>{t.common?.cancel || 'Cancel'}</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmRegenerate}
                className="bg-primary hover:bg-primary/90"
              >
                {t.artifacts?.regenerateButton || 'Regenerate'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
}

interface ArtifactStatusItemProps {
  artifact: ArtifactStatus;
  isEditMode?: boolean;
  onRegenerate?: () => void;
}

function ArtifactStatusItem({ artifact, isEditMode, onRegenerate }: ArtifactStatusItemProps) {
  const { t } = useTranslation();
  const Icon = artifact.icon;

  return (
    <div
      className={cn(
        'flex items-center justify-between p-4 rounded-lg border transition-colors',
        artifact.status === 'completed' && 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950',
        artifact.status === 'error' && 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950',
        artifact.status === 'generating' && 'border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950'
      )}
    >
      <div className="flex items-center gap-3 flex-1">
        <Icon className="h-5 w-5" />
        <div className="flex-1">
          <div className="font-medium">{artifact.label}</div>
          {artifact.status === 'generating' && (
            <div className="text-sm text-muted-foreground mt-1">
              {artifact.type === 'podcast' ? 'Processing (2-5 min)...' : 'Generating...'}
            </div>
          )}
          {artifact.status === 'error' && artifact.error && (
            <div className="text-sm text-red-600 dark:text-red-400 mt-1">
              {artifact.error}
            </div>
          )}
        </div>
      </div>

      {/* Status Indicator and Actions */}
      <div className="flex items-center gap-2">
        {artifact.status === 'pending' && (
          <div className="h-6 w-6 rounded-full border-2 border-muted" />
        )}
        {artifact.status === 'generating' && (
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        )}
        {artifact.status === 'completed' && (
          <>
            <div className="h-6 w-6 rounded-full bg-green-600 flex items-center justify-center">
              <Check className="h-4 w-4 text-white" />
            </div>
            {/* Regenerate button in edit mode (Story 3.6, Task 9) */}
            {isEditMode && onRegenerate && (
              <Button
                size="sm"
                variant="outline"
                onClick={onRegenerate}
                className="ml-2"
                title={t.artifacts?.regenerate || 'Regenerate'}
              >
                <RotateCw className="h-3 w-3 mr-1" />
                {t.artifacts?.regenerate || 'Regenerate'}
              </Button>
            )}
          </>
        )}
        {artifact.status === 'error' && (
          <div className="h-6 w-6 rounded-full bg-red-600 flex items-center justify-center">
            <AlertCircle className="h-4 w-4 text-white" />
          </div>
        )}
      </div>
    </div>
  );
}
