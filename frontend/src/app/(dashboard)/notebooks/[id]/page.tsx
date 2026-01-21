'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { LearningLayout } from '@/components/layout/LearningLayout'
import { NotebookHeader } from '../components/NotebookHeader'
import { DocumentsColumn } from '../components/DocumentsColumn'
import { NotesColumn } from '../components/NotesColumn'
import { ChatColumn } from '../components/ChatColumn'
import { ArtifactsPanel } from '@/components/layout/ArtifactsPanel'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useNotes } from '@/lib/hooks/use-notes'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useNotebookColumnsStore } from '@/lib/stores/notebook-columns-store'
import { useIsDesktop } from '@/lib/hooks/use-media-query'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, StickyNote, MessageSquare, BookOpen, GraduationCap, GripVertical } from 'lucide-react'

export type ContextMode = 'off' | 'insights' | 'full'

export interface ContextSelections {
  sources: Record<string, ContextMode>
  notes: Record<string, ContextMode>
}

export default function NotebookPage() {
  const { t } = useTranslation()
  const params = useParams()

  // Ensure the notebook ID is properly decoded from URL
  const notebookId = params?.id ? decodeURIComponent(params.id as string) : ''

  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId)
  const {
    sources,
    isLoading: sourcesLoading,
    refetch: refetchSources,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useNotebookSources(notebookId)
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId)

  // Get collapse states for dynamic layout
  const { sourcesCollapsed, notesCollapsed, artifactsCollapsed, chatCollapsed } = useNotebookColumnsStore()

  // Detect desktop to avoid double-mounting ChatColumn
  const isDesktop = useIsDesktop()

  // Resizable column widths
  const [documentsWidth, setDocumentsWidth] = useState(33.33) // percentage
  const [notesArtifactsWidth, setNotesArtifactsWidth] = useState(33.33) // percentage
  const [notesHeight, setNotesHeight] = useState(66.67) // percentage of Notes+Artifacts column
  const [isResizing, setIsResizing] = useState<'documents' | 'notes-artifacts' | 'notes-vertical' | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const resizeStartRef = useRef({ x: 0, y: 0, documentsWidth: 0, notesArtifactsWidth: 0, notesHeight: 0 })

  const handleResizeStart = useCallback((type: 'documents' | 'notes-artifacts' | 'notes-vertical', e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(type)
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      resizeStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        documentsWidth,
        notesArtifactsWidth,
        notesHeight,
      }
    }
  }, [documentsWidth, notesArtifactsWidth, notesHeight])

  useEffect(() => {
    if (!isResizing || !containerRef.current) return

    const handleMouseMove = (e: MouseEvent) => {
      requestAnimationFrame(() => {
        if (!containerRef.current) return
        const rect = containerRef.current.getBoundingClientRect()
        
        if (isResizing === 'documents' || isResizing === 'notes-artifacts') {
          const deltaX = e.clientX - resizeStartRef.current.x
          const deltaPercent = (deltaX / rect.width) * 100

          if (isResizing === 'documents') {
            const newDocWidth = resizeStartRef.current.documentsWidth + deltaPercent
            const minDocWidth = 10
            const maxDocWidth = 60
            
            // Ensure there's enough space for middle and chat columns (min 15% each)
            const maxAllowedDocWidth = 100 - 30 // Reserve 30% for middle + chat
            
            const constrainedDocWidth = Math.max(minDocWidth, Math.min(maxDocWidth, Math.min(maxAllowedDocWidth, newDocWidth)))
            setDocumentsWidth(constrainedDocWidth)
            
          } else if (isResizing === 'notes-artifacts') {
            const newMiddleWidth = resizeStartRef.current.notesArtifactsWidth + deltaPercent
            const minMiddleWidth = 15
            const maxMiddleWidth = 60
            
            // Ensure there's enough space for chat column (min 10%)
            const maxAllowedMiddle = 100 - documentsWidth - 10
            
            const constrainedMiddleWidth = Math.max(minMiddleWidth, Math.min(maxMiddleWidth, Math.min(maxAllowedMiddle, newMiddleWidth)))
            setNotesArtifactsWidth(constrainedMiddleWidth)
          }
        } else if (isResizing === 'notes-vertical') {
          const notesArtifactsContainer = containerRef.current.querySelector('[data-notes-artifacts-container]') as HTMLElement
          if (notesArtifactsContainer) {
            const containerRect = notesArtifactsContainer.getBoundingClientRect()
            const deltaY = e.clientY - resizeStartRef.current.y
            const deltaPercent = (deltaY / containerRect.height) * 100
            const newHeight = Math.max(20, Math.min(80, resizeStartRef.current.notesHeight + deltaPercent))
            setNotesHeight(newHeight)
          }
        }
      })
    }

    const handleMouseUp = () => {
      setIsResizing(null)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  // Mobile tab state (Documents, Notes, Chat, or Artifacts)
  const [mobileActiveTab, setMobileActiveTab] = useState<'documents' | 'notes' | 'chat' | 'artifacts'>('documents')

  // Context selection state
  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {}
  })

  // Initialize default selections when sources/notes load
  useEffect(() => {
    if (sources && sources.length > 0) {
      setContextSelections(prev => {
        const newSourceSelections = { ...prev.sources }
        sources.forEach(source => {
          // Only set default if not already set
          if (!(source.id in newSourceSelections)) {
            // Default to 'insights' if has insights, otherwise 'full'
            newSourceSelections[source.id] = source.insights_count > 0 ? 'insights' : 'full'
          }
        })
        return { ...prev, sources: newSourceSelections }
      })
    }
  }, [sources])

  useEffect(() => {
    if (notes && notes.length > 0) {
      setContextSelections(prev => {
        const newNoteSelections = { ...prev.notes }
        notes.forEach(note => {
          // Only set default if not already set
          if (!(note.id in newNoteSelections)) {
            // Notes default to 'full'
            newNoteSelections[note.id] = 'full'
          }
        })
        return { ...prev, notes: newNoteSelections }
      })
    }
  }, [notes])

  // Handler to update context selection
  const handleContextModeChange = (itemId: string, mode: ContextMode, type: 'source' | 'note') => {
    setContextSelections(prev => ({
      ...prev,
      [type === 'source' ? 'sources' : 'notes']: {
        ...(type === 'source' ? prev.sources : prev.notes),
        [itemId]: mode
      }
    }))
  }

  if (notebookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!notebook) {
    return (
      <AppShell>
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">{t.notebooks.notFound}</h1>
          <p className="text-muted-foreground">{t.notebooks.notFoundDesc}</p>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col flex-1 min-h-0">
        <div className="flex-shrink-0 p-6 pb-0">
          <NotebookHeader notebook={notebook} />
        </div>

        <div className="flex-1 p-6 pt-6 overflow-x-auto flex flex-col">
          {/* Mobile: Tabbed interface - only render on mobile to avoid double-mounting */}
          {!isDesktop && (
            <>
              <div className="lg:hidden mb-4">
                <Tabs value={mobileActiveTab} onValueChange={(value) => setMobileActiveTab(value as 'documents' | 'notes' | 'chat' | 'artifacts')}>
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="documents" className="gap-2">
                      <FileText className="h-4 w-4" />
                      {t.navigation.documents}
                    </TabsTrigger>
                    <TabsTrigger value="notes" className="gap-2">
                      <StickyNote className="h-4 w-4" />
                      {t.common.notes}
                    </TabsTrigger>
                    <TabsTrigger value="artifacts" className="gap-2">
                      <GraduationCap className="h-4 w-4" />
                      Artifacts
                    </TabsTrigger>
                    <TabsTrigger value="chat" className="gap-2">
                      <MessageSquare className="h-4 w-4" />
                      {t.common.chat}
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* Mobile: Show only active tab */}
              <div className="flex-1 overflow-hidden lg:hidden">
                {mobileActiveTab === 'documents' && (
                  <DocumentsColumn
                    sources={sources}
                    isLoading={sourcesLoading}
                    notebookId={notebookId}
                    notebookName={notebook?.name}
                    onRefresh={refetchSources}
                    contextSelections={contextSelections.sources}
                    onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                    hasNextPage={hasNextPage}
                    isFetchingNextPage={isFetchingNextPage}
                    fetchNextPage={fetchNextPage}
                  />
                )}
                {mobileActiveTab === 'notes' && (
                  <NotesColumn
                    notes={notes}
                    isLoading={notesLoading}
                    notebookId={notebookId}
                    contextSelections={contextSelections.notes}
                    onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                  />
                )}
                {mobileActiveTab === 'artifacts' && (
                  <ArtifactsPanel
                    notebookId={notebookId}
                  />
                )}
                {mobileActiveTab === 'chat' && (
                  <ChatColumn
                    notebookId={notebookId}
                    contextSelections={contextSelections}
                  />
                )}
              </div>
            </>
          )}

          {/* Desktop: 3-column learning layout */}
          <div 
            ref={containerRef}
            className={cn(
              'hidden lg:flex h-full min-h-0',
              'flex-row relative',
              isResizing && 'select-none cursor-col-resize'
            )}
            style={{ gap: '6px' }}
          >
            {/* Column 1: Documents (merged Sources + Reader) */}
            <div 
              className={cn(
                'relative h-full',
                sourcesCollapsed ? 'w-12 flex-shrink-0' : ''
              )}
              style={!sourcesCollapsed ? { 
                width: `${documentsWidth}%`,
                transition: isResizing ? 'none' : 'width 150ms'
              } : undefined}
            >
              <DocumentsColumn
                sources={sources}
                isLoading={sourcesLoading}
                notebookId={notebookId}
                notebookName={notebook?.name}
                onRefresh={refetchSources}
                contextSelections={contextSelections.sources}
                onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                hasNextPage={hasNextPage}
                isFetchingNextPage={isFetchingNextPage}
                fetchNextPage={fetchNextPage}
              />
              {!sourcesCollapsed && !(notesCollapsed && artifactsCollapsed) && (
                <div
                  onMouseDown={(e) => handleResizeStart('documents', e)}
                  className={cn(
                    'absolute right-0 top-0 h-full cursor-col-resize z-20 group',
                    'flex items-center justify-center'
                  )}
                  style={{ right: '-3px', width: '6px' }}
                >
                  <div className="w-px h-full bg-transparent group-hover:bg-primary/50 transition-colors" />
                  <GripVertical className="absolute opacity-0 group-hover:opacity-100 transition-opacity text-primary" size={14} />
                </div>
              )}
            </div>

            {/* Column 2: Notes + Artifacts (stacked vertically) */}
            <div 
              className={cn(
                'relative h-full',
                (notesCollapsed && artifactsCollapsed) ? 'w-12 flex-shrink-0' : ''
              )}
              style={!(notesCollapsed && artifactsCollapsed) ? { 
                width: `${notesArtifactsWidth}%`,
                transition: isResizing ? 'none' : 'width 150ms'
              } : undefined}
              data-notes-artifacts-container
            >
              <div className="flex flex-col h-full gap-1.5">
                {/* Notes - resizable height when both expanded, else takes available space */}
                <div 
                  className={cn(
                    'relative',
                    notesCollapsed ? 'w-12 flex-shrink-0' : 'w-full min-h-0'
                  )}
                  style={!notesCollapsed && !artifactsCollapsed ? { 
                    height: `${notesHeight}%`,
                    transition: isResizing === 'notes-vertical' ? 'none' : 'height 150ms'
                  } : !notesCollapsed ? { flex: 1 } : undefined}
                >
                  <NotesColumn
                    notes={notes}
                    isLoading={notesLoading}
                    notebookId={notebookId}
                    contextSelections={contextSelections.notes}
                    onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                  />
                </div>
                
                {/* Horizontal resize handle between Notes and Artifacts */}
                {!notesCollapsed && !artifactsCollapsed && (
                  <div
                    onMouseDown={(e) => handleResizeStart('notes-vertical', e)}
                    className={cn(
                      'cursor-row-resize z-20 group flex items-center justify-center',
                      'h-[6px] -my-[3px]'
                    )}
                  >
                    <div className="w-full h-px bg-transparent group-hover:bg-primary/50 transition-colors" />
                    <GripVertical className="absolute opacity-0 group-hover:opacity-100 transition-opacity text-primary rotate-90" size={14} />
                  </div>
                )}
                
                {/* Artifacts - takes remaining space */}
                <div 
                  className={cn(
                    'relative',
                    artifactsCollapsed ? 'w-12 flex-shrink-0' : 'w-full flex-1 min-h-0'
                  )}
                  style={{
                    transition: isResizing === 'notes-vertical' ? 'none' : 'flex 150ms, height 150ms'
                  }}
                >
                  <ArtifactsPanel
                    notebookId={notebookId}
                  />
                </div>
              </div>
              {!(notesCollapsed && artifactsCollapsed) && !chatCollapsed && (
                <div
                  onMouseDown={(e) => handleResizeStart('notes-artifacts', e)}
                  className={cn(
                    'absolute right-0 top-0 h-full cursor-col-resize z-20 group',
                    'flex items-center justify-center'
                  )}
                  style={{ right: '-3px', width: '6px' }}
                >
                  <div className="w-px h-full bg-transparent group-hover:bg-primary/50 transition-colors" />
                  <GripVertical className="absolute opacity-0 group-hover:opacity-100 transition-opacity text-primary" size={14} />
                </div>
              )}
            </div>

            {/* Column 3: Chat - takes remaining space */}
            <div 
              className={cn(
                'h-full',
                chatCollapsed ? 'w-12 flex-shrink-0' : 'flex-1 min-w-0'
              )}
              style={{
                transition: isResizing ? 'none' : 'width 150ms, flex 150ms'
              }}
            >
              <ChatColumn
                notebookId={notebookId}
                contextSelections={contextSelections}
              />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
