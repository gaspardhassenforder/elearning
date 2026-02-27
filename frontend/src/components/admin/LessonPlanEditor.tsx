'use client'

/**
 * Lesson Plan Editor Component
 *
 * Drag-and-drop editor for managing lesson steps with:
 * - AI-generation from notebook sources
 * - Step type badges (watch / read / quiz / discuss)
 * - Inline title editing
 * - Linked source name display
 * - Delete operations
 * - Drag-and-drop reordering
 */

import { useState } from 'react'
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd'
import {
  GripVertical,
  Trash2,
  Sparkles,
  Loader2,
  BookOpen,
  MessageSquare,
  PlayCircle,
  HelpCircle,
} from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import {
  useLessonSteps,
  useGenerateLessonPlan,
  useUpdateLessonStep,
  useDeleteLessonStep,
  useReorderLessonSteps,
} from '@/lib/hooks/use-lesson-plan'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { cn } from '@/lib/utils'

interface LessonPlanEditorProps {
  moduleId: string
}

const STEP_TYPE_CONFIG = {
  watch: {
    icon: PlayCircle,
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  read: {
    icon: BookOpen,
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  },
  quiz: {
    icon: HelpCircle,
    className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  },
  discuss: {
    icon: MessageSquare,
    className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  },
} as const

export function LessonPlanEditor({ moduleId }: LessonPlanEditorProps) {
  const { t } = useTranslation()
  const lessonPlanT = t.lessonPlan

  const { data: steps = [], isLoading } = useLessonSteps(moduleId)
  const generateMutation = useGenerateLessonPlan(moduleId)
  const updateMutation = useUpdateLessonStep(moduleId)
  const deleteMutation = useDeleteLessonStep(moduleId)
  const reorderMutation = useReorderLessonSteps(moduleId)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingText, setEditingText] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return
    const src = result.source.index
    const dst = result.destination.index
    if (src === dst) return

    const reordered = Array.from(steps)
    const [removed] = reordered.splice(src, 1)
    reordered.splice(dst, 0, removed)

    reorderMutation.mutate(
      reordered.map((step, index) => ({ id: step.id, order: index }))
    )
  }

  const handleEditStart = (id: string, title: string) => {
    setEditingId(id)
    setEditingText(title)
  }

  const handleEditSave = (id: string) => {
    const original = steps.find((s) => s.id === id)
    if (editingText.trim() && editingText !== original?.title) {
      updateMutation.mutate({ stepId: id, data: { title: editingText.trim() } })
    }
    setEditingId(null)
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, { onSuccess: () => setDeleteConfirmId(null) })
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-muted-foreground">{t.common.loading}</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const showEmptyState = steps.length === 0 && !generateMutation.isPending

  return (
    <div className="space-y-4">
      {/* Empty state */}
      {showEmptyState && (
        <Card>
          <CardContent className="py-8">
            <div className="text-center space-y-4">
              <Sparkles className="h-12 w-12 mx-auto text-muted-foreground" />
              <div>
                <h3 className="font-semibold mb-1">{lessonPlanT.noSteps}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {lessonPlanT.emptyDescription}
                </p>
                <Button
                  onClick={() => generateMutation.mutate()}
                  disabled={generateMutation.isPending}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  {lessonPlanT.generate}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generation in progress */}
      {generateMutation.isPending && steps.length === 0 && (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-muted-foreground">{lessonPlanT.generating}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Steps list */}
      {steps.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">
              {lessonPlanT.stepsCount.replace('{count}', String(steps.length))}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  {lessonPlanT.generating}
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-3 w-3" />
                  {lessonPlanT.regenerate}
                </>
              )}
            </Button>
          </div>

          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="lesson-steps-list">
              {(provided, snapshot) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className={cn(
                    'space-y-2',
                    snapshot.isDraggingOver && 'bg-muted/50 rounded-md p-2'
                  )}
                >
                  {steps.map((step, index) => {
                    const config = STEP_TYPE_CONFIG[step.step_type] || STEP_TYPE_CONFIG.read
                    const Icon = config.icon

                    return (
                      <Draggable key={step.id} draggableId={step.id} index={index}>
                        {(provided, snapshot) => (
                          <Card
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className={cn(
                              'transition-shadow',
                              snapshot.isDragging && 'shadow-lg'
                            )}
                          >
                            <CardContent className="py-3 px-4">
                              <div className="flex items-center gap-3">
                                {/* Drag handle */}
                                <div
                                  {...provided.dragHandleProps}
                                  className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground flex-shrink-0"
                                >
                                  <GripVertical className="h-5 w-5" />
                                </div>

                                {/* Step number */}
                                <div className="flex-shrink-0 w-6 text-sm font-medium text-muted-foreground">
                                  {index + 1}.
                                </div>

                                {/* Step type badge */}
                                <Badge
                                  variant="outline"
                                  className={cn('flex-shrink-0 gap-1 text-xs', config.className)}
                                >
                                  <Icon className="h-3 w-3" />
                                  {lessonPlanT.stepTypes[step.step_type] || step.step_type}
                                </Badge>

                                {/* Editable title + source info */}
                                <div className="flex-1 min-w-0">
                                  {editingId === step.id ? (
                                    <Input
                                      value={editingText}
                                      onChange={(e) => setEditingText(e.target.value)}
                                      onBlur={() => handleEditSave(step.id)}
                                      onKeyDown={(e) => {
                                        if (e.key === 'Enter') handleEditSave(step.id)
                                        if (e.key === 'Escape') setEditingId(null)
                                      }}
                                      autoFocus
                                      className="h-8"
                                    />
                                  ) : (
                                    <div>
                                      <button
                                        onClick={() => handleEditStart(step.id, step.title)}
                                        className="text-left w-full hover:text-primary transition-colors truncate block"
                                      >
                                        {step.title}
                                      </button>
                                      {step.source_title && (
                                        <p className="text-xs text-muted-foreground truncate mt-0.5">
                                          {step.source_title}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                </div>

                                {/* AI generated badge */}
                                {step.auto_generated && (
                                  <Badge variant="secondary" className="text-xs flex-shrink-0">
                                    <Sparkles className="mr-1 h-3 w-3" />
                                    {t.common.aiGenerated}
                                  </Badge>
                                )}

                                {/* Delete button */}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setDeleteConfirmId(step.id)}
                                  disabled={deleteMutation.isPending}
                                  className="flex-shrink-0"
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </Draggable>
                    )
                  })}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </>
      )}

      {/* Delete confirmation */}
      <AlertDialog
        open={deleteConfirmId !== null}
        onOpenChange={(open) => !open && setDeleteConfirmId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{lessonPlanT.deleteTitle}</AlertDialogTitle>
            <AlertDialogDescription>{lessonPlanT.deleteConfirm}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {t.common.delete}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
