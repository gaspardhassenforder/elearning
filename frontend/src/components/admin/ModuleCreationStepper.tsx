'use client';

/**
 * Module Creation Pipeline Stepper (Story 3.1, Task 6)
 *
 * Horizontal stepper showing 5-step module creation pipeline:
 * 1. Create - Module details
 * 2. Upload - Documents
 * 3. Generate - Artifacts (quizzes, podcasts)
 * 4. Configure - Learning objectives, AI prompts
 * 5. Publish - Make available to learners
 */

import { Check } from 'lucide-react';
import { useTranslation } from '@/lib/hooks/use-translation';
import { useModuleCreationStore } from '@/lib/stores/module-creation-store';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const STEPS = [
  { id: 'create', label: 'stepCreate' },
  { id: 'upload', label: 'stepUpload' },
  { id: 'generate', label: 'stepGenerate' },
  { id: 'configure', label: 'stepConfigure' },
  { id: 'publish', label: 'stepPublish' },
] as const;

interface ModuleCreationStepperProps {
  /**
   * Optional validation function to check if the current step can proceed to next
   * Returns true if step is valid and can advance, false otherwise
   */
  canProceed?: boolean;
}

export function ModuleCreationStepper({ canProceed = true }: ModuleCreationStepperProps) {
  const { t } = useTranslation();
  const { activeStep, setActiveStep } = useModuleCreationStore();

  const currentStepIndex = STEPS.findIndex((step) => step.id === activeStep);

  const handleStepClick = (stepId: string) => {
    // Allow navigation to completed steps or next step
    const clickedIndex = STEPS.findIndex((s) => s.id === stepId);
    if (clickedIndex <= currentStepIndex + 1) {
      setActiveStep(stepId as any);
    }
  };

  const handleNext = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < STEPS.length) {
      setActiveStep(STEPS[nextIndex].id);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setActiveStep(STEPS[prevIndex].id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Stepper */}
      <div className="relative">
        {/* Progress Bar */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-muted -z-10">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{
              width: `${(currentStepIndex / (STEPS.length - 1)) * 100}%`,
            }}
          />
        </div>

        {/* Steps */}
        <div className="flex justify-between">
          {STEPS.map((step, index) => {
            const isActive = index === currentStepIndex;
            const isCompleted = index < currentStepIndex;
            const isAccessible = index <= currentStepIndex + 1;

            return (
              <button
                key={step.id}
                onClick={() => handleStepClick(step.id)}
                disabled={!isAccessible}
                className={cn(
                  'flex flex-col items-center gap-2 transition-opacity',
                  !isAccessible && 'opacity-40 cursor-not-allowed'
                )}
              >
                {/* Step Circle */}
                <div
                  className={cn(
                    'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                    isCompleted &&
                      'bg-primary border-primary text-primary-foreground',
                    isActive &&
                      !isCompleted &&
                      'border-primary text-primary bg-background',
                    !isActive &&
                      !isCompleted &&
                      'border-muted-foreground/25 text-muted-foreground bg-background'
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>

                {/* Step Label */}
                <span
                  className={cn(
                    'text-sm font-medium',
                    isActive ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {t.modules[step.label as keyof typeof t.modules]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-muted-foreground">
          {t.modules.pipelineProgress
            .replace('{current}', String(currentStepIndex + 1))
            .replace('{total}', String(STEPS.length))}
        </div>

        <div className="flex gap-2">
          {currentStepIndex > 0 && (
            <Button variant="outline" onClick={handleBack}>
              {t.modules.previousStep}
            </Button>
          )}

          {currentStepIndex < STEPS.length - 1 && (
            <Button onClick={handleNext} disabled={!canProceed}>
              {t.modules.nextStep}
            </Button>
          )}

          {/* Publish button will be implemented in Story 3.5 */}
          {currentStepIndex === STEPS.length - 1 && (
            <Button disabled>
              {t.modules.finishSetup}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
