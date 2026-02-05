'use client';

/**
 * Admin Module Management Page (Story 3.1, Task 4)
 *
 * Lists all modules with create/edit/delete actions.
 * Entry point for module creation pipeline.
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, FileText, BookOpen, Trash2, Settings } from 'lucide-react';
import { useModules, useDeleteModule } from '@/lib/hooks/use-modules';
import { useTranslation } from '@/lib/hooks/use-translation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
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
import { Badge } from '@/components/ui/badge';
import { ModuleForm } from '@/components/admin/ModuleForm';

export default function ModulesPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data: modules, isLoading, error } = useModules();
  const deleteModule = useDeleteModule();

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [moduleToDelete, setModuleToDelete] = useState<string | null>(null);

  const handleCreateClick = () => {
    setIsCreateDialogOpen(true);
  };

  const handleModuleClick = (moduleId: string) => {
    router.push(`/modules/${moduleId}`);
  };

  const handleDeleteClick = (moduleId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setModuleToDelete(moduleId);
  };

  const handleDeleteConfirm = async () => {
    if (moduleToDelete) {
      await deleteModule.mutateAsync(moduleToDelete);
      setModuleToDelete(null);
    }
  };

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <p className="text-destructive">{t.modules.loadError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t.modules.adminTitle}</h1>
          <p className="text-muted-foreground">{t.modules.adminSubtitle}</p>
        </div>
        <Button onClick={handleCreateClick}>
          <Plus className="mr-2 h-4 w-4" />
          {t.modules.createModule}
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!modules || modules.length === 0) && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">{t.modules.noModules}</h3>
            <p className="text-sm text-muted-foreground mb-4">
              {t.modules.adminSubtitle}
            </p>
            <Button onClick={handleCreateClick}>
              <Plus className="mr-2 h-4 w-4" />
              {t.modules.createModule}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Module Grid */}
      {!isLoading && modules && modules.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {modules.map((module) => (
            <Card
              key={module.id}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleModuleClick(module.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="flex items-center gap-2">
                      {module.name}
                      {!module.published && (
                        <Badge variant="secondary" className="text-xs">
                          {t.assignments.draft}
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      {module.description || t.notebooks.noDescription}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => handleDeleteClick(module.id, e)}
                    className="h-8 w-8"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    <span>{module.source_count} {t.sources.title.toLowerCase()}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <BookOpen className="h-4 w-4" />
                    <span>{module.note_count} {t.common.notes.toLowerCase()}</span>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs text-muted-foreground">
                    {t.common.updated.replace('{time}', new Date(module.updated).toLocaleDateString())}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Module Dialog */}
      <ModuleForm
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!moduleToDelete} onOpenChange={() => setModuleToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.modules.confirmDelete}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.modules.deleteWarning}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {t.common.delete}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
