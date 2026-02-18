'use client'

import { useMemo } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useTranslation } from '@/lib/hooks/use-translation'

interface LearnerSourceSelectorProps {
  notebookId: string
  selectedSourceIds: string[]
  onSelectionChange: (ids: string[]) => void
}

function getFileIcon(source: { asset?: { file_path?: string; url?: string } | null }): string {
  const path = source.asset?.file_path || source.asset?.url || ''
  const ext = path.split('.').pop()?.toLowerCase() || ''
  if (ext === 'pdf') return '📕'
  if (['doc', 'docx'].includes(ext)) return '📘'
  if (['xls', 'xlsx', 'csv'].includes(ext)) return '📗'
  if (['ppt', 'pptx'].includes(ext)) return '📙'
  if (['mp4', 'avi', 'mov', 'webm'].includes(ext)) return '🎬'
  if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return '🎵'
  if (source.asset?.url) return '🔗'
  return '📄'
}

export function LearnerSourceSelector({
  notebookId,
  selectedSourceIds,
  onSelectionChange,
}: LearnerSourceSelectorProps) {
  const { t } = useTranslation()
  const { sources, isLoading } = useNotebookSources(notebookId)

  const allSelected = useMemo(
    () => sources.length > 0 && selectedSourceIds.length === sources.length,
    [sources.length, selectedSourceIds.length]
  )

  const toggleSource = (sourceId: string) => {
    if (selectedSourceIds.includes(sourceId)) {
      onSelectionChange(selectedSourceIds.filter((id) => id !== sourceId))
    } else {
      onSelectionChange([...selectedSourceIds, sourceId])
    }
  }

  const toggleAll = () => {
    if (allSelected) {
      onSelectionChange([])
    } else {
      onSelectionChange(sources.map((s) => s.id))
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-6">
        <LoadingSpinner />
      </div>
    )
  }

  if (!sources || sources.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        {t.learner?.sources?.noSources || 'No sources available'}
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {t.learner?.createArtifact?.selectSources || 'Select Sources'}
        </span>
        <button
          type="button"
          onClick={toggleAll}
          className="text-xs text-primary hover:underline"
        >
          {allSelected
            ? (t.learner?.createArtifact?.deselectAll || 'Deselect All')
            : (t.learner?.createArtifact?.selectAll || 'Select All')}
        </button>
      </div>
      <ScrollArea className="max-h-[200px] rounded-md border p-2">
        <div className="space-y-1">
          {sources.map((source) => (
            <label
              key={source.id}
              className="flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-accent/50 cursor-pointer text-sm"
            >
              <Checkbox
                checked={selectedSourceIds.includes(source.id)}
                onCheckedChange={() => toggleSource(source.id)}
              />
              <span className="flex-shrink-0 text-sm">{getFileIcon(source)}</span>
              <span className="truncate">{source.title || 'Untitled'}</span>
            </label>
          ))}
        </div>
      </ScrollArea>
      {selectedSourceIds.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {(t.learner?.createArtifact?.selectedSources || '{selected} / {total} selected')
            .replace('{selected}', String(selectedSourceIds.length))
            .replace('{total}', String(sources.length))}
        </p>
      )}
    </div>
  )
}
