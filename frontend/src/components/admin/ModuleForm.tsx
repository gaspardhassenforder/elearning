'use client';

/**
 * Module Creation/Edit Form (Story 3.1, Task 4)
 *
 * Dialog form for creating or editing a module.
 * Validates input and submits via TanStack Query mutation.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCreateModule, useUpdateModule } from '@/lib/hooks/use-modules';
import { useTranslation } from '@/lib/hooks/use-translation';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Module } from '@/lib/api/modules';

interface ModuleFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  module?: Module;
}

export function ModuleForm({ open, onOpenChange, module }: ModuleFormProps) {
  const { t } = useTranslation();
  const router = useRouter();
  const createModule = useCreateModule();
  const updateModule = useUpdateModule(module?.id || '');

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<{ name?: string }>({});

  // Load existing module data when editing
  useEffect(() => {
    if (module) {
      setName(module.name);
      setDescription(module.description);
    } else {
      setName('');
      setDescription('');
    }
  }, [module, open]);

  const validate = () => {
    const newErrors: { name?: string } = {};

    if (!name.trim()) {
      newErrors.name = t.common.nameRequired;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      if (module) {
        // Update existing module
        await updateModule.mutateAsync({
          name: name.trim(),
          description: description.trim(),
        });
        onOpenChange(false);
      } else {
        // Create new module
        const newModule = await createModule.mutateAsync({
          name: name.trim(),
          description: description.trim(),
        });

        // Close dialog and navigate to module page for document upload
        onOpenChange(false);
        router.push(`/admin/modules/${newModule.id}`);
      }
    } catch (error) {
      // Error already handled by mutation hook with toast
    }
  };

  const handleCancel = () => {
    setName('');
    setDescription('');
    setErrors({});
    onOpenChange(false);
  };

  const isSubmitting = createModule.isPending || updateModule.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {module ? t.common.edit : t.modules.createModuleTitle}
            </DialogTitle>
            <DialogDescription>
              {module ? t.notebooks.updateSuccess : t.modules.createModuleDesc}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Module Name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-right">
                {t.modules.moduleName} *
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (errors.name) {
                    setErrors({ ...errors, name: undefined });
                  }
                }}
                placeholder={t.modules.moduleNamePlaceholder}
                disabled={isSubmitting}
                className={errors.name ? 'border-destructive' : ''}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>

            {/* Module Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-right">
                {t.modules.moduleDescription}
              </Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t.modules.moduleDescriptionPlaceholder}
                disabled={isSubmitting}
                rows={4}
              />
              <p className="text-xs text-muted-foreground">
                {t.common.optional}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              {t.common.cancel}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? t.modules.creating
                : module
                ? t.common.saveChanges
                : t.common.create}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
