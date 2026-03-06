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
  ChevronDown,
  ChevronUp,
  Headphones,
  Languages,
  Palette,
} from 'lucide-react'
import { toast } from 'sonner'
import { useTranslation } from '@/lib/hooks/use-translation'
import {
  useLessonSteps,
  useGenerateLessonPlan,
  useUpdateLessonStep,
  useDeleteLessonStep,
  useDeleteAllLessonSteps,
  useReorderLessonSteps,
  useRefineLessonPlan,
  useTriggerPodcastGeneration,
} from '@/lib/hooks/use-lesson-plan'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useEpisodeProfiles } from '@/lib/hooks/use-podcasts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

interface LessonPlanEditorProps {
  moduleId: string
}

const STEP_TYPE_CONFIG = {
  watch: {
    icon: PlayCircle,
    className: 'bg-blue-500 text-white border-transparent dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800',
  },
  read: {
    icon: BookOpen,
    className: 'bg-green-500 text-white border-transparent dark:bg-green-900/30 dark:text-green-400 dark:border-green-800',
  },
  quiz: {
    icon: HelpCircle,
    className: 'bg-amber-500 text-white border-transparent dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
  },
  discuss: {
    icon: MessageSquare,
    className: 'bg-purple-500 text-white border-transparent dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800',
  },
  podcast: {
    icon: Headphones,
    className: 'bg-orange-500 text-white border-transparent dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800',
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
  const triggerPodcastMutation = useTriggerPodcastGeneration(moduleId)
  const { sources } = useNotebookSources(moduleId)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingText, setEditingText] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [expandedAiInstructions, setExpandedAiInstructions] = useState<Set<string>>(new Set())
  const [editingAiInstructionsId, setEditingAiInstructionsId] = useState<string | null>(null)
  const [editingAiInstructionsText, setEditingAiInstructionsText] = useState('')
  const [refinePrompt, setRefinePrompt] = useState('')
  // Podcast review panel state: stepId -> {title, instructions, selectedSourceIds}
  const [expandedPodcastReview, setExpandedPodcastReview] = useState<Set<string>>(new Set())
  const [podcastReviewState, setPodcastReviewState] = useState<Record<string, {
    title: string
    instructions: string
    selectedSourceIds: Set<string>
    language: string
    episodeProfileName: string
  }>>({})

  const deleteAllMutation = useDeleteAllLessonSteps(moduleId)
  const refineMutation = useRefineLessonPlan(moduleId)
  const { episodeProfiles } = useEpisodeProfiles()

  const openPodcastReview = (stepId: string, stepTitle: string, podcastTopic: string | null, stepSourceIds?: string[] | null) => {
    if (!expandedPodcastReview.has(stepId)) {
      // Pre-select step's source_ids if available, otherwise all sources
      const initialSources = stepSourceIds?.length
        ? new Set(stepSourceIds)
        : new Set(sources.map(s => s.id))
      setPodcastReviewState(prev => ({
        ...prev,
        [stepId]: {
          title: stepTitle,
          instructions: podcastTopic || '',
          selectedSourceIds: initialSources,
          language: prev[stepId]?.language ?? 'en',
          episodeProfileName: prev[stepId]?.episodeProfileName ?? (episodeProfiles[0]?.name ?? ''),
        },
      }))
      setExpandedPodcastReview(prev => new Set([...prev, stepId]))
    } else {
      setExpandedPodcastReview(prev => {
        const next = new Set(prev)
        next.delete(stepId)
        return next
      })
    }
  }

  const updatePodcastReviewState = (stepId: string, field: 'title' | 'instructions', value: string) => {
    setPodcastReviewState(prev => ({
      ...prev,
      [stepId]: { ...prev[stepId], [field]: value },
    }))
  }

  const togglePodcastSource = (stepId: string, sourceId: string) => {
    setPodcastReviewState(prev => {
      const current = prev[stepId]
      if (!current) return prev
      const next = new Set(current.selectedSourceIds)
      if (next.has(sourceId)) next.delete(sourceId)
      else next.add(sourceId)
      return { ...prev, [stepId]: { ...current, selectedSourceIds: next } }
    })
  }

  const handleTriggerPodcast = (stepId: string) => {
    const state = podcastReviewState[stepId]
    if (!state) return
    triggerPodcastMutation.mutate(
      {
        stepId,
        data: {
          title: state.title || undefined,
          ai_instructions: state.instructions || undefined,
          source_ids: state.selectedSourceIds.size > 0 ? [...state.selectedSourceIds] : [],
          episode_profile_name: state.episodeProfileName || undefined,
          language: state.language || 'en',
        },
      },
      {
        onSuccess: () => {
          setExpandedPodcastReview(prev => {
            const next = new Set(prev)
            next.delete(stepId)
            return next
          })
        },
      }
    )
  }

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

  const toggleAiInstructions = (id: string) => {
    const isExpanded = expandedAiInstructions.has(id)
    setExpandedAiInstructions(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    if (isExpanded && editingAiInstructionsId === id) {
      setEditingAiInstructionsId(null)
    }
  }

  const handleAiInstructionsEditStart = (id: string, text: string) => {
    setEditingAiInstructionsId(id)
    setEditingAiInstructionsText(text || '')
  }

  const handleAiInstructionsSave = (id: string) => {
    const original = steps.find((s) => s.id === id)
    if (editingAiInstructionsText !== (original?.ai_instructions || '')) {
      updateMutation.mutate({
        stepId: id,
        data: { ai_instructions: editingAiInstructionsText || null }
      })
    }
    setEditingAiInstructionsId(null)
  }

  const handleRefineApply = () => {
    if (!refinePrompt.trim()) return
    refineMutation.mutate(refinePrompt, {
      onSuccess: () => {
        toast.success(lessonPlanT.refineSuccess)
        setRefinePrompt('')
      }
    })
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
            <div className="flex items-center gap-2">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={deleteAllMutation.isPending}
                  >
                    {deleteAllMutation.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{lessonPlanT.deleteAllTitle}</AlertDialogTitle>
                    <AlertDialogDescription>{lessonPlanT.deleteAllConfirm}</AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => deleteAllMutation.mutate()}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {lessonPlanT.deleteAll}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
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
                                {step.step_type === 'podcast' && !step.command_id && !step.artifact_id ? (
                                  <Badge
                                    variant="outline"
                                    className="flex-shrink-0 gap-1 text-xs bg-yellow-500 text-white border-transparent dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800"
                                  >
                                    <Headphones className="h-3 w-3" />
                                    {lessonPlanT.podcastReviewRequired}
                                  </Badge>
                                ) : (
                                  <Badge
                                    variant="outline"
                                    className={cn('flex-shrink-0 gap-1 text-xs', config.className)}
                                  >
                                    <Icon className="h-3 w-3" />
                                    {lessonPlanT.stepTypes[step.step_type] || step.step_type}
                                  </Badge>
                                )}

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

                                {/* Podcast Review & Generate button */}
                                {step.step_type === 'podcast' && !step.command_id && !step.artifact_id && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => openPodcastReview(step.id, step.title, step.podcast_topic, step.source_ids)}
                                    className="flex-shrink-0 text-xs border-yellow-500 text-yellow-700 hover:bg-yellow-50 dark:text-yellow-400 dark:hover:bg-yellow-900/20"
                                  >
                                    {lessonPlanT.podcastGenerateButton}
                                  </Button>
                                )}

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

                              {/* AI Instructions expandable */}
                              <div className="mt-2">
                                <button
                                  onClick={() => toggleAiInstructions(step.id)}
                                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                >
                                  {expandedAiInstructions.has(step.id) ? (
                                    <ChevronUp className="h-3 w-3" />
                                  ) : (
                                    <ChevronDown className="h-3 w-3" />
                                  )}
                                  {lessonPlanT.aiInstructionsToggle}
                                  {step.ai_instructions && (
                                    <span className="ml-1 text-primary">&bull;</span>
                                  )}
                                </button>
                                {expandedAiInstructions.has(step.id) && (
                                  <div className="mt-1 ml-4">
                                    {editingAiInstructionsId === step.id ? (
                                      <Textarea
                                        value={editingAiInstructionsText}
                                        onChange={(e) => setEditingAiInstructionsText(e.target.value)}
                                        onBlur={() => handleAiInstructionsSave(step.id)}
                                        onKeyDown={(e) => {
                                          if (e.key === 'Escape') setEditingAiInstructionsId(null)
                                        }}
                                        autoFocus
                                        className="text-xs min-h-[80px]"
                                        placeholder={lessonPlanT.aiInstructions}
                                      />
                                    ) : (
                                      <button
                                        onClick={() => handleAiInstructionsEditStart(step.id, step.ai_instructions || '')}
                                        className="text-left w-full text-xs text-muted-foreground hover:text-foreground transition-colors border border-dashed border-muted rounded p-2 min-h-[40px]"
                                      >
                                        {step.ai_instructions || (
                                          <span className="italic opacity-50">{lessonPlanT.aiInstructions}...</span>
                                        )}
                                      </button>
                                    )}
                                  </div>
                                )}
                              </div>

                              {/* Podcast Review Panel */}
                              {step.step_type === 'podcast' && !step.command_id && !step.artifact_id && expandedPodcastReview.has(step.id) && (
                                <div className="mt-3 border border-yellow-300 dark:border-yellow-800 rounded-md p-3 space-y-3 bg-yellow-50/50 dark:bg-yellow-900/10">
                                  {/* Episode Title */}
                                  <div className="space-y-1">
                                    <Label className="text-xs font-medium">{lessonPlanT.podcastTitleLabel}</Label>
                                    <Input
                                      value={podcastReviewState[step.id]?.title ?? step.title}
                                      onChange={(e) => updatePodcastReviewState(step.id, 'title', e.target.value)}
                                      className="h-8 text-xs"
                                    />
                                  </div>
                                  {/* Topic / Instructions */}
                                  <div className="space-y-1">
                                    <Label className="text-xs font-medium">{lessonPlanT.podcastTopicLabel}</Label>
                                    <Textarea
                                      value={podcastReviewState[step.id]?.instructions ?? step.podcast_topic ?? ''}
                                      onChange={(e) => updatePodcastReviewState(step.id, 'instructions', e.target.value)}
                                      className="text-xs min-h-[60px]"
                                    />
                                  </div>
                                  {/* Language + Profile */}
                                  <div className="flex flex-wrap gap-3">
                                    <div className="flex items-center gap-2 min-w-0">
                                      <Languages className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                                      <Label className="text-xs font-medium flex-shrink-0">Language:</Label>
                                      <Select
                                        value={podcastReviewState[step.id]?.language ?? 'en'}
                                        onValueChange={(v) => updatePodcastReviewState(step.id, 'language', v)}
                                      >
                                        <SelectTrigger className="h-7 w-28 text-xs">
                                          <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                          <SelectItem value="en">English</SelectItem>
                                          <SelectItem value="fr">Français</SelectItem>
                                        </SelectContent>
                                      </Select>
                                    </div>
                                    {episodeProfiles.length > 0 && (
                                      <div className="flex items-center gap-2 min-w-0">
                                        <Palette className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                                        <Label className="text-xs font-medium flex-shrink-0">Profile:</Label>
                                        <Select
                                          value={podcastReviewState[step.id]?.episodeProfileName ?? episodeProfiles[0]?.name ?? ''}
                                          onValueChange={(v) => updatePodcastReviewState(step.id, 'episodeProfileName', v)}
                                        >
                                          <SelectTrigger className="h-7 w-44 text-xs">
                                            <SelectValue />
                                          </SelectTrigger>
                                          <SelectContent>
                                            {episodeProfiles.map(ep => (
                                              <SelectItem key={ep.id} value={ep.name}>
                                                {ep.name}
                                              </SelectItem>
                                            ))}
                                          </SelectContent>
                                        </Select>
                                      </div>
                                    )}
                                  </div>
                                  {/* Source selection */}
                                  {sources.length > 0 && (
                                    <div className="space-y-1">
                                      <Label className="text-xs font-medium">{lessonPlanT.podcastSourceSelection}</Label>
                                      <div className="space-y-1 max-h-[120px] overflow-y-auto">
                                        {sources.map(source => (
                                          <div key={source.id} className="flex items-center gap-2">
                                            <Checkbox
                                              id={`podcast-src-${step.id}-${source.id}`}
                                              checked={podcastReviewState[step.id]?.selectedSourceIds?.has(source.id) ?? true}
                                              onCheckedChange={() => togglePodcastSource(step.id, source.id)}
                                            />
                                            <Label
                                              htmlFor={`podcast-src-${step.id}-${source.id}`}
                                              className="text-xs font-normal cursor-pointer truncate"
                                            >
                                              {source.title || source.id}
                                            </Label>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  {/* Generate button */}
                                  <div className="flex justify-end">
                                    <Button
                                      size="sm"
                                      onClick={() => handleTriggerPodcast(step.id)}
                                      disabled={triggerPodcastMutation.isPending}
                                      className="text-xs"
                                    >
                                      {triggerPodcastMutation.isPending ? (
                                        <>
                                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                          {lessonPlanT.podcastGenerating}
                                        </>
                                      ) : (
                                        <>
                                          <Headphones className="mr-2 h-3 w-3" />
                                          {lessonPlanT.podcastGenerateButton}
                                        </>
                                      )}
                                    </Button>
                                  </div>
                                </div>
                              )}
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

      {/* Refinement section */}
      {steps.length > 0 && (
        <Card className="mt-4">
          <CardContent className="pt-4 pb-4">
            <div className="space-y-2">
              <p className="text-sm font-medium flex items-center gap-1">
                <Sparkles className="h-4 w-4" />
                {lessonPlanT.refineLabel}
              </p>
              <Textarea
                value={refinePrompt}
                onChange={(e) => setRefinePrompt(e.target.value)}
                placeholder={lessonPlanT.refinePlaceholder}
                className="text-sm min-h-[60px]"
                rows={2}
              />
              <div className="flex justify-end">
                <Button
                  size="sm"
                  onClick={handleRefineApply}
                  disabled={refineMutation.isPending || !refinePrompt.trim()}
                >
                  {refineMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                      {lessonPlanT.generating}
                    </>
                  ) : (
                    lessonPlanT.refineApply
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
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
