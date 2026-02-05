/**
 * Learning Objectives Editor Component (Story 3.3, Task 4)
 *
 * Drag-and-drop editor for managing learning objectives with:
 * - Auto-generation from module content
 * - Inline text editing
 * - Add/delete operations
 * - Visual indicators for auto-generated vs manual
 * - Validation warning when 0 objectives exist
 */

'use client'

import { useState } from 'react'
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd'
import { GripVertical, Trash2, Plus, Sparkles, Loader2 } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import {
  useLearningObjectives,
  useGenerateLearningObjectives,
  useCreateLearningObjective,
  useUpdateLearningObjective,
  useDeleteLearningObjective,
  useReorderLearningObjectives,
} from '@/lib/hooks/use-learning-objectives'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
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

interface LearningObjectivesEditorProps {
  moduleId: string
}

export function LearningObjectivesEditor({ moduleId }: LearningObjectivesEditorProps) {
  const { t } = useTranslation()

  // Query and mutations
  const { data: objectives = [], isLoading, error } = useLearningObjectives(moduleId)
  const generateMutation = useGenerateLearningObjectives(moduleId)
  const createMutation = useCreateLearningObjective(moduleId)
  const updateMutation = useUpdateLearningObjective(moduleId)
  const deleteMutation = useDeleteLearningObjective(moduleId)
  const reorderMutation = useReorderLearningObjectives(moduleId)

  // Local state
  const [newObjectiveText, setNewObjectiveText] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingText, setEditingText] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  // Auto-save when text editing is complete
  const handleAutoSave = (objectiveId: string, text: string) => {
    if (text.trim() && text !== objectives.find((o) => o.id === objectiveId)?.text) {
      updateMutation.mutate({ objectiveId, data: { text } })
      setEditingId(null)
    }
  }

  // Handle drag end for reordering
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const sourceIndex = result.source.index
    const destinationIndex = result.destination.index

    if (sourceIndex === destinationIndex) return

    // Reorder array
    const reordered = Array.from(objectives)
    const [removed] = reordered.splice(sourceIndex, 1)
    reordered.splice(destinationIndex, 0, removed)

    // Update order field for all affected objectives
    const updates = reordered.map((obj, index) => ({
      id: obj.id,
      order: index,
    }))

    reorderMutation.mutate({ objectives: updates })
  }

  // Handle generate objectives
  const handleGenerate = () => {
    generateMutation.mutate()
  }

  // Handle add manual objective
  const handleAddObjective = () => {
    if (!newObjectiveText.trim()) return

    createMutation.mutate(
      { text: newObjectiveText.trim() },
      {
        onSuccess: () => {
          setNewObjectiveText('')
        },
      }
    )
  }

  // Handle edit start
  const handleEditStart = (objectiveId: string, text: string) => {
    setEditingId(objectiveId)
    setEditingText(text)
  }

  // Handle edit blur
  const handleEditBlur = (objectiveId: string) => {
    handleAutoSave(objectiveId, editingText)
  }

  // Handle delete
  const handleDelete = (objectiveId: string) => {
    deleteMutation.mutate(objectiveId, {
      onSuccess: () => {
        setDeleteConfirmId(null)
      },
    })
  }

  // Loading state
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

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <Alert variant="destructive">
            <AlertDescription>
              {t.learningObjectives.loadError}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  // Empty state: Show generate button
  const showEmptyState = objectives.length === 0 && !generateMutation.isPending

  return (
    <div className="space-y-4">
      {/* Validation warning */}
      {objectives.length === 0 && (
        <Alert>
          <AlertDescription>
            {t.learningObjectives.validationRequired}
          </AlertDescription>
        </Alert>
      )}

      {/* Empty state with generate button */}
      {showEmptyState && (
        <Card>
          <CardContent className="py-8">
            <div className="text-center space-y-4">
              <Sparkles className="h-12 w-12 mx-auto text-muted-foreground" />
              <div>
                <h3 className="font-semibold mb-1">
                  {t.learningObjectives.emptyTitle}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {t.learningObjectives.emptyDescription}
                </p>
                <Button onClick={handleGenerate} disabled={generateMutation.isPending}>
                  {generateMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {t.learningObjectives.generating}
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      {t.learningObjectives.generateButton}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generation in progress */}
      {generateMutation.isPending && objectives.length === 0 && (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-muted-foreground">
                {t.learningObjectives.generating}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Objectives list with drag-and-drop */}
      {objectives.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">
              {t.learningObjectives.listDescription}
            </p>
            {objectives.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    {t.learningObjectives.regenerating}
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-3 w-3" />
                    {t.learningObjectives.regenerateButton}
                  </>
                )}
              </Button>
            )}
          </div>

          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="objectives-list">
              {(provided, snapshot) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className={cn(
                    'space-y-2',
                    snapshot.isDraggingOver && 'bg-muted/50 rounded-md p-2'
                  )}
                >
                  {objectives.map((objective, index) => (
                    <Draggable
                      key={objective.id}
                      draggableId={objective.id}
                      index={index}
                    >
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
                                className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground"
                              >
                                <GripVertical className="h-5 w-5" />
                              </div>

                              {/* Order number */}
                              <div className="flex-shrink-0 w-6 text-sm font-medium text-muted-foreground">
                                {index + 1}.
                              </div>

                              {/* Editable text */}
                              <div className="flex-1">
                                {editingId === objective.id ? (
                                  <Input
                                    value={editingText}
                                    onChange={(e) => setEditingText(e.target.value)}
                                    onBlur={() => handleEditBlur(objective.id)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter') {
                                        handleAutoSave(objective.id, editingText)
                                      }
                                      if (e.key === 'Escape') {
                                        setEditingId(null)
                                        setEditingText('')
                                      }
                                    }}
                                    autoFocus
                                    className="h-8"
                                  />
                                ) : (
                                  <button
                                    onClick={() =>
                                      handleEditStart(objective.id, objective.text)
                                    }
                                    className="text-left w-full hover:text-primary transition-colors"
                                  >
                                    {objective.text}
                                  </button>
                                )}
                              </div>

                              {/* Auto-generated badge */}
                              {objective.auto_generated && (
                                <Badge variant="secondary" className="text-xs">
                                  <Sparkles className="mr-1 h-3 w-3" />
                                  {t.common.aiGenerated}
                                </Badge>
                              )}

                              {/* Delete button */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeleteConfirmId(objective.id)}
                                disabled={deleteMutation.isPending}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </>
      )}

      {/* Add new objective */}
      <Card>
        <CardContent className="py-4">
          <div className="flex gap-2">
            <Input
              placeholder={t.learningObjectives.addPlaceholder}
              value={newObjectiveText}
              onChange={(e) => setNewObjectiveText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleAddObjective()
                }
              }}
              disabled={createMutation.isPending}
            />
            <Button
              onClick={handleAddObjective}
              disabled={!newObjectiveText.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  {t.common.add}
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Delete confirmation dialog */}
      <AlertDialog
        open={deleteConfirmId !== null}
        onOpenChange={(open) => !open && setDeleteConfirmId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.learningObjectives.deleteTitle}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.learningObjectives.deleteConfirm}
            </AlertDialogDescription>
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
