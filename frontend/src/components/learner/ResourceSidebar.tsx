'use client'

/**
 * ResourceSidebar Component
 *
 * Fixed 280px sidebar for the ChatGPT-like learner interface.
 * Three collapsible sections: Sources, Quizzes/Podcasts, Progress.
 * Click on any item opens the ResourceViewerSheet.
 */

import { useState } from 'react'
import {
  FileText,
  GraduationCap,
  TrendingUp,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useNotebookArtifacts } from '@/lib/hooks/use-artifacts'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { ObjectiveProgressList } from './ObjectiveProgressList'

interface ResourceSidebarProps {
  notebookId: string
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

function getArtifactIcon(type: string): string {
  switch (type) {
    case 'quiz': return '📝'
    case 'podcast': return '🎧'
    case 'summary': return '📋'
    case 'transformation': return '✨'
    default: return '📦'
  }
}

export function ResourceSidebar({ notebookId }: ResourceSidebarProps) {
  const { t } = useTranslation()
  const openViewerSheet = useLearnerStore((state) => state.openViewerSheet)
  const viewerSheet = useLearnerStore((state) => state.viewerSheet)

  const [sourcesOpen, setSourcesOpen] = useState(true)
  const [artifactsOpen, setArtifactsOpen] = useState(true)
  const [progressOpen, setProgressOpen] = useState(true)

  const { sources, isLoading: sourcesLoading } = useNotebookSources(notebookId)
  const { data: artifacts, isLoading: artifactsLoading } = useNotebookArtifacts(notebookId)

  return (
    <div className="h-full overflow-y-auto overflow-x-hidden">
      <div className="py-4">
        {/* Sources Section */}
        <SectionHeader
          icon={<FileText className="h-3.5 w-3.5" />}
          label={t.learner.sources.title}
          count={sources?.length}
          isOpen={sourcesOpen}
          onToggle={() => setSourcesOpen(!sourcesOpen)}
        />
        {sourcesOpen && (
          <div className="mt-1 space-y-0.5 px-2">
            {sourcesLoading ? (
              <div className="flex items-center justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : !sources || sources.length === 0 ? (
              <p className="text-xs text-muted-foreground px-3 py-2">
                {t.learner.sources.noSources}
              </p>
            ) : (
              sources.map((source) => (
                <button
                  key={source.id}
                  onClick={() => openViewerSheet({ type: 'source', id: source.id })}
                  className={`w-full text-left flex items-center gap-2 py-2 px-3 rounded-lg text-sm transition-colors hover:bg-accent/50 ${
                    viewerSheet?.type === 'source' && viewerSheet?.id === source.id
                      ? 'bg-accent border-l-2 border-primary'
                      : ''
                  }`}
                >
                  <span className="flex-shrink-0 text-sm">
                    {getFileIcon(source)}
                  </span>
                  <span className="truncate">
                    {source.title || t.learner.sources.untitled}
                  </span>
                </button>
              ))
            )}
          </div>
        )}

        {/* Artifacts Section */}
        <SectionHeader
          icon={<GraduationCap className="h-3.5 w-3.5" />}
          label={t.learner.artifacts.title}
          count={artifacts?.length}
          isOpen={artifactsOpen}
          onToggle={() => setArtifactsOpen(!artifactsOpen)}
          className="mt-4"
        />
        {artifactsOpen && (
          <div className="mt-1 space-y-0.5 px-2">
            {artifactsLoading ? (
              <div className="flex items-center justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : !artifacts || artifacts.length === 0 ? (
              <p className="text-xs text-muted-foreground px-3 py-2">
                {t.learner.artifacts.noArtifacts}
              </p>
            ) : (
              artifacts.map((artifact) => (
                <button
                  key={artifact.id}
                  onClick={() => openViewerSheet({ type: 'artifact', id: artifact.id })}
                  className={`w-full text-left flex items-center gap-2 py-2 px-3 rounded-lg text-sm transition-colors hover:bg-accent/50 ${
                    viewerSheet?.type === 'artifact' && viewerSheet?.id === artifact.id
                      ? 'bg-accent border-l-2 border-primary'
                      : ''
                  }`}
                >
                  <span className="flex-shrink-0 text-sm">
                    {getArtifactIcon(artifact.artifact_type)}
                  </span>
                  <span className="truncate">{artifact.title}</span>
                </button>
              ))
            )}
          </div>
        )}

        {/* Progress Section */}
        <SectionHeader
          icon={<TrendingUp className="h-3.5 w-3.5" />}
          label={t.learner.progress.title}
          isOpen={progressOpen}
          onToggle={() => setProgressOpen(!progressOpen)}
          className="mt-4"
        />
        {progressOpen && (
          <div className="mt-1 overflow-hidden px-2">
            <ObjectiveProgressList notebookId={notebookId} />
          </div>
        )}
      </div>
    </div>
  )
}

// Section header with collapsible toggle
function SectionHeader({
  icon,
  label,
  count,
  isOpen,
  onToggle,
  className = '',
}: {
  icon: React.ReactNode
  label: string
  count?: number
  isOpen: boolean
  onToggle: () => void
  className?: string
}) {
  return (
    <button
      onClick={onToggle}
      className={`w-full flex items-center gap-2 px-4 py-1.5 text-xs font-medium uppercase text-muted-foreground tracking-wider hover:text-foreground transition-colors ${className}`}
    >
      {isOpen ? (
        <ChevronDown className="h-3 w-3" />
      ) : (
        <ChevronRight className="h-3 w-3" />
      )}
      {icon}
      <span>{label}</span>
      {count !== undefined && count > 0 && (
        <span className="ml-auto text-[10px] font-normal tabular-nums">
          {count}
        </span>
      )}
    </button>
  )
}
