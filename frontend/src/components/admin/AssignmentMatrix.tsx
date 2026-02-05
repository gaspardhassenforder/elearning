'use client'

import { useState } from 'react'
import { useTranslation } from '@/lib/hooks/use-translation'
import {
  useAssignmentMatrix,
  useToggleAssignment,
  useToggleModuleLock,
} from '@/lib/hooks/use-assignments'
import { useToast } from '@/lib/hooks/use-toast'
import { NotebookSummary } from '@/lib/types/api'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Building2, BookOpen, Loader2, Lock, LockOpen } from 'lucide-react'

export function AssignmentMatrix() {
  const { t } = useTranslation()
  const { data: matrix, isLoading, error } = useAssignmentMatrix()
  const toggleMutation = useToggleAssignment()
  const lockMutation = useToggleModuleLock()
  const { toast } = useToast()
  const [activeToggle, setActiveToggle] = useState<string | null>(null)
  const [activeLockToggle, setActiveLockToggle] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t.common.error}
      </div>
    )
  }

  if (!matrix?.companies.length) {
    return (
      <div className="text-center py-12 border rounded-lg">
        <Building2 className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium">{t.assignments.noCompanies}</h3>
      </div>
    )
  }

  if (!matrix?.notebooks.length) {
    return (
      <div className="text-center py-12 border rounded-lg">
        <BookOpen className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium">{t.assignments.noModules}</h3>
      </div>
    )
  }

  const handleToggle = async (
    companyId: string,
    notebookId: string,
    notebook: NotebookSummary
  ) => {
    const toggleKey = `${companyId}:${notebookId}`
    const cell = matrix.assignments[companyId]?.[notebookId]
    const wasAssigned = cell?.is_assigned ?? false

    // Show warning for unpublished modules when assigning
    if (!wasAssigned && !notebook.published) {
      toast({
        title: t.common.warning,
        description: t.assignments.unpublishedWarning,
        variant: 'default',
      })
    }

    setActiveToggle(toggleKey)
    try {
      await toggleMutation.mutateAsync({ companyId, notebookId })
    } catch (error) {
      toast({
        title: t.common.error,
        description: error instanceof Error ? error.message : t.common.unknownError,
        variant: 'destructive',
      })
    } finally {
      setActiveToggle(null)
    }
  }

  const handleLockToggle = async (
    companyId: string,
    notebookId: string,
    currentLockStatus: boolean
  ) => {
    const lockKey = `lock:${companyId}:${notebookId}`
    const newLockStatus = !currentLockStatus

    setActiveLockToggle(lockKey)
    try {
      await lockMutation.mutateAsync({
        companyId,
        notebookId,
        isLocked: newLockStatus,
      })
    } catch (error) {
      toast({
        title: t.common.error,
        description: error instanceof Error ? error.message : t.common.unknownError,
        variant: 'destructive',
      })
    } finally {
      setActiveLockToggle(null)
    }
  }

  return (
    <div className="border rounded-lg overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky left-0 bg-background z-10 min-w-[150px]">
              {t.assignments.companies}
            </TableHead>
            {matrix.notebooks.map((notebook) => (
              <TableHead key={notebook.id} className="text-center min-w-[120px]">
                <div className="flex flex-col items-center gap-1">
                  <span
                    className={
                      notebook.published ? '' : 'text-muted-foreground'
                    }
                  >
                    {notebook.name}
                  </span>
                  {!notebook.published && (
                    <Badge variant="secondary" className="text-xs">
                      {t.assignments.draft}
                    </Badge>
                  )}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {matrix.companies.map((company) => (
            <TableRow key={company.id}>
              <TableCell className="sticky left-0 bg-background z-10 font-medium">
                {company.name}
              </TableCell>
              {matrix.notebooks.map((notebook) => {
                const cell = matrix.assignments[company.id]?.[notebook.id]
                const isAssigned = cell?.is_assigned ?? false
                const isLocked = cell?.is_locked ?? false
                const toggleKey = `${company.id}:${notebook.id}`
                const lockKey = `lock:${company.id}:${notebook.id}`
                const isThisToggleActive = activeToggle === toggleKey
                const isThisLockToggleActive = activeLockToggle === lockKey

                return (
                  <TableCell key={notebook.id} className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      {isThisToggleActive ? (
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      ) : (
                        <Checkbox
                          checked={isAssigned}
                          onCheckedChange={() =>
                            handleToggle(company.id, notebook.id, notebook)
                          }
                          disabled={activeToggle !== null || activeLockToggle !== null}
                          aria-label={t.assignments.toggleAssignment}
                        />
                      )}
                      {isAssigned && (
                        <>
                          {isThisLockToggleActive ? (
                            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                          ) : (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      handleLockToggle(company.id, notebook.id, isLocked)
                                    }}
                                    disabled={activeToggle !== null || activeLockToggle !== null}
                                    aria-label={
                                      isLocked
                                        ? t.assignments.unlockModule
                                        : t.assignments.lockModule
                                    }
                                  >
                                    {isLocked ? (
                                      <Lock className="h-4 w-4 text-amber-600" />
                                    ) : (
                                      <LockOpen className="h-4 w-4 text-muted-foreground" />
                                    )}
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>
                                    {isLocked
                                      ? t.assignments.unlockModule
                                      : t.assignments.lockModule}
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </>
                      )}
                    </div>
                  </TableCell>
                )
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
