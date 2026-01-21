'use client'

import { useState } from 'react'
import { ArtifactResponse } from '@/lib/api/artifacts'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FileText, Trash2, Play } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { getDateLocale } from '@/lib/utils/date-locale'
import { useTranslation } from '@/lib/hooks/use-translation'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { QuizViewer } from './QuizViewer'

interface QuizCardProps {
  artifact: ArtifactResponse
  onDelete: (artifactId: string) => void
  notebookId: string
}

export function QuizCard({ artifact, onDelete, notebookId }: QuizCardProps) {
  const { t, language } = useTranslation()
  const [showQuizViewer, setShowQuizViewer] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = () => {
    onDelete(artifact.id)
    setDeleteDialogOpen(false)
  }

  return (
    <>
      <Card 
        className="cursor-pointer hover:bg-accent/50 transition-colors"
        onClick={() => setShowQuizViewer(true)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="mt-1">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm truncate">{artifact.title}</h4>
                  <Badge variant="secondary" className="text-xs">
                    {t.artifacts?.quiz || 'Quiz'}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(artifact.created), {
                    addSuffix: true,
                    locale: getDateLocale(language)
                  })}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowQuizViewer(true)
                }}
                className="h-8"
              >
                <Play className="h-4 w-4 mr-1" />
                {t.artifacts?.takeQuiz || 'Take Quiz'}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={handleDeleteClick}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {showQuizViewer && (
        <QuizViewer
          quizId={artifact.artifact_id}
          notebookId={notebookId}
          open={showQuizViewer}
          onOpenChange={setShowQuizViewer}
        />
      )}

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title={t.artifacts?.deleteArtifact || 'Delete Artifact'}
        description={t.artifacts?.deleteConfirm || 'Are you sure you want to delete this artifact?'}
        confirmText={t.common.delete}
        onConfirm={handleDeleteConfirm}
        confirmVariant="destructive"
      />
    </>
  )
}
