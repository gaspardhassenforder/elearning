'use client';

/**
 * Individual Module Page with Pipeline (Story 3.1, Tasks 5-6)
 *
 * Displays module details and document upload interface.
 * Shows pipeline stepper for multi-step creation workflow.
 */

import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useModule } from '@/lib/hooks/use-modules';
import { useTranslation } from '@/lib/hooks/use-translation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { DocumentUploader } from '@/components/admin/DocumentUploader';
import { ModuleCreationStepper } from '@/components/admin/ModuleCreationStepper';
import { ArtifactGenerationPanel } from '@/components/admin/ArtifactGenerationPanel';
import { LearningObjectivesEditor } from '@/components/admin/LearningObjectivesEditor';
import { ModulePromptEditor } from '@/components/admin/ModulePromptEditor';
import { AdminAssistantChat } from '@/components/admin/AdminAssistantChat';
import { UnpublishConfirmDialog } from '@/components/admin/UnpublishConfirmDialog';
import { useModuleCreationStore } from '@/lib/stores/module-creation-store';
import { useArtifacts } from '@/lib/hooks/use-artifacts';
import { useLearningObjectives } from '@/lib/hooks/use-learning-objectives';
import { useState } from 'react';
import { Edit } from 'lucide-react';

export default function ModulePage() {
  const { t } = useTranslation();
  const params = useParams();
  const moduleId = params.id as string;

  const { data: module, isLoading, error } = useModule(moduleId);
  const { activeStep, setActiveStep, isEditMode } = useModuleCreationStore();
  const { data: artifacts } = useArtifacts(moduleId);
  const { data: objectives = [] } = useLearningObjectives(moduleId);

  // Configure step has two sub-pages: objectives and prompt
  const [configureSubStep, setConfigureSubStep] = useState<'objectives' | 'prompt'>('objectives');

  // Unpublish confirmation dialog (Story 3.6, Task 6)
  const [showUnpublishDialog, setShowUnpublishDialog] = useState(false);

  // Step validation logic
  const canProceedFromGenerate =
    activeStep !== 'generate' ||
    (artifacts && artifacts.some((artifact) => artifact.status === 'completed'));

  // Step validation: For 'configure' step, require at least one learning objective
  const canProceedFromConfigure =
    activeStep !== 'configure' || objectives.length >= 1;

  // Combined validation for stepper
  const canProceed = canProceedFromGenerate && canProceedFromConfigure;

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <p className="text-destructive">{t.modules.loadError}</p>
          <Link href="/modules">
            <Button variant="outline" className="mt-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              {t.common.back}
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!module) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <p className="text-muted-foreground">{t.modules.noModules}</p>
          <Link href="/modules">
            <Button variant="outline" className="mt-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              {t.common.back}
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Back Navigation */}
      <Link href="/modules">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t.common.back}
        </Button>
      </Link>

      {/* Module Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h1 className="text-3xl font-bold tracking-tight">{module.name}</h1>
          {!module.published && !isEditMode && (
            <Badge variant="secondary">{t.assignments.draft}</Badge>
          )}
          {/* Edit mode indicator (Story 3.6, Task 7) */}
          {isEditMode && (
            <Badge variant="outline" className="border-primary text-primary">
              {t.modules.editingMode || 'Editing'}
            </Badge>
          )}
          {/* Edit button for published modules (Story 3.6, Task 6) */}
          {module.published && !isEditMode && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowUnpublishDialog(true)}
              className="ml-auto"
            >
              <Edit className="mr-2 h-4 w-4" />
              {t.modules.editModule}
            </Button>
          )}
        </div>
        {module.description && (
          <p className="text-muted-foreground">{module.description}</p>
        )}
      </div>

      {/* Pipeline Stepper */}
      <ModuleCreationStepper canProceed={canProceed} />

      {/* Main Content - Step-based rendering */}
      {activeStep === 'upload' && (
        <Card>
          <CardHeader>
            <CardTitle>{t.modules.uploadDocuments}</CardTitle>
            <CardDescription>{t.modules.uploadDocumentsDesc}</CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentUploader moduleId={moduleId} />
          </CardContent>
        </Card>
      )}

      {activeStep === 'generate' && (
        <ArtifactGenerationPanel
          moduleId={moduleId}
          onComplete={() => setActiveStep('configure')}
        />
      )}

      {activeStep === 'configure' && (
        <div className="space-y-6">
          {configureSubStep === 'objectives' && (
            <Card>
              <CardHeader>
                <CardTitle>{t.learningObjectives.title}</CardTitle>
                <CardDescription>{t.learningObjectives.subtitle}</CardDescription>
              </CardHeader>
              <CardContent>
                <LearningObjectivesEditor moduleId={moduleId} />
                <div className="mt-6 flex justify-end">
                  <Button
                    onClick={() => setConfigureSubStep('prompt')}
                    disabled={objectives.length < 1}
                  >
                    {t.common.next}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {configureSubStep === 'prompt' && (
            <Card>
              <CardHeader>
                <CardTitle>{t.modulePrompt.title}</CardTitle>
                <CardDescription>{t.modulePrompt.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ModulePromptEditor
                  moduleId={moduleId}
                  onNext={() => setActiveStep('publish')}
                  onBack={() => setConfigureSubStep('objectives')}
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Module Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              {t.sources.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{module.source_count}</div>
            <p className="text-xs text-muted-foreground">
              {t.modules.sources.replace('{count}', String(module.source_count))}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              {t.common.notes}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{module.note_count}</div>
            <p className="text-xs text-muted-foreground">
              {t.modules.notes.replace('{count}', String(module.note_count))}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              {t.common.updated_label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">{new Date(module.updated).toLocaleDateString()}</div>
            <p className="text-xs text-muted-foreground">
              {new Date(module.updated).toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Admin Assistant Chat - Floating Button Available Across All Steps */}
      <AdminAssistantChat moduleId={moduleId} />

      {/* Unpublish Confirmation Dialog (Story 3.6, Task 6) */}
      <UnpublishConfirmDialog
        open={showUnpublishDialog}
        onOpenChange={setShowUnpublishDialog}
        moduleId={moduleId}
        moduleName={module.name}
      />
    </div>
  );
}
