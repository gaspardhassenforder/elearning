'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useLearnerModules } from '@/lib/hooks/use-learner-modules'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useRouter } from 'next/navigation'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { BookOpen, GraduationCap, FileText, ArrowRight, Lock } from 'lucide-react'
import { LearnerModule } from '@/lib/types/api'

/**
 * Module Selection Page (Learner Home)
 *
 * Displays assigned modules for learners filtered by company assignment and lock status.
 * Shows locked modules with reduced opacity and lock indicator.
 * Only unlocked modules are clickable.
 */
export default function ModulesPage() {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const router = useRouter()
  const { data: modules, isLoading, error } = useLearnerModules()

  const handleOpenModule = (notebookId: string, isLocked: boolean) => {
    // Prevent navigation if module is locked
    if (isLocked) return
    router.push(`/modules/${notebookId}`)
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          {t.modules.welcome.replace('{name}', user?.username || 'Learner')}
        </h1>
        <p className="text-muted-foreground mt-2">
          {t.modules.subtitle}
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-10 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{t.modules.loadError}</p>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!modules || modules.length === 0) && (
        <Card className="border-dashed">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <GraduationCap className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>{t.assignments.moduleSelection}</CardTitle>
            <CardDescription>
              {t.modules.noModulesDescription}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center pb-6">
            <div className="flex flex-col items-center gap-4 py-6">
              <BookOpen className="h-16 w-16 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">
                {t.modules.noModules}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Module Grid */}
      {!isLoading && !error && modules && modules.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((module: LearnerModule) => (
            <ModuleCard
              key={module.id}
              module={module}
              onOpen={() => handleOpenModule(module.id, module.is_locked)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface ModuleCardProps {
  module: LearnerModule
  onOpen: () => void
}

/**
 * ModuleCard Component (Task 11)
 *
 * Displays a single module with lock status indicators.
 * Locked modules: 60% opacity, lock icon, pointer-events-none
 * Unlocked modules: clickable, navigates to learning interface
 */
function ModuleCard({ module, onOpen }: ModuleCardProps) {
  const { t } = useTranslation()
  const isLocked = module.is_locked

  return (
    <Card
      className={`group transition-all ${
        isLocked
          ? 'opacity-60 cursor-not-allowed'
          : 'hover:shadow-md cursor-pointer'
      }`}
      onClick={isLocked ? undefined : onOpen}
      style={isLocked ? { pointerEvents: 'none' } : undefined}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <BookOpen className="h-5 w-5 text-primary" />
          </div>
          {isLocked && (
            <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-200">
              <Lock className="h-3 w-3 mr-1" />
              {t.assignments.locked}
            </Badge>
          )}
        </div>
        <CardTitle className="mt-4 line-clamp-2">{module.name}</CardTitle>
        {module.description && (
          <CardDescription className="line-clamp-2">
            {module.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            <span>{t.modules.sources.replace('{count}', String(module.source_count))}</span>
          </div>
        </div>
        <Button
          className="w-full group-hover:bg-primary/90"
          variant="default"
          disabled={isLocked}
        >
          {isLocked ? t.assignments.locked : t.modules.startLearning}
          {!isLocked && <ArrowRight className="ml-2 h-4 w-4" />}
        </Button>
      </CardContent>
    </Card>
  )
}
