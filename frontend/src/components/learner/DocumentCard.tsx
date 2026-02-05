'use client'

/**
 * Story 4.1: Learner Document Card
 *
 * Collapsible card displaying document metadata in sources panel.
 * Read-only for learners (no edit/delete actions).
 */

import { FileText, File } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'

interface DocumentCardProps {
  source: {
    id: string
    title: string | null
    file_type?: string | null
    status?: string
    embedded?: boolean
  }
}

export function DocumentCard({ source }: DocumentCardProps) {
  const { t } = useTranslation()

  const getStatusBadge = () => {
    if (source.status === 'processing') {
      return <Badge variant="secondary">{t.learner.sources.processing}</Badge>
    }
    if (source.status === 'error') {
      return <Badge variant="destructive">{t.learner.sources.error}</Badge>
    }
    if (source.embedded) {
      return <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600">{t.learner.sources.ready}</Badge>
    }
    return null
  }

  const getFileIcon = () => {
    const fileType = source.file_type?.toLowerCase()

    // Map file types to appropriate icons
    if (fileType?.includes('pdf')) {
      return <File className="h-4 w-4 text-red-500" />
    }
    if (fileType?.includes('doc') || fileType?.includes('word')) {
      return <File className="h-4 w-4 text-blue-500" />
    }
    if (fileType?.includes('sheet') || fileType?.includes('excel')) {
      return <File className="h-4 w-4 text-green-500" />
    }
    if (fileType?.includes('text') || fileType?.includes('txt')) {
      return <FileText className="h-4 w-4 text-gray-500" />
    }

    return <FileText className="h-4 w-4 text-muted-foreground" />
  }

  return (
    <Card className={cn(
      "cursor-pointer transition-colors hover:bg-accent/50",
      source.status === 'processing' && "opacity-60"
    )}>
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {getFileIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium line-clamp-2 mb-1">
              {source.title || t.learner.sources.untitled}
            </h3>
            {source.file_type && (
              <p className="text-xs text-muted-foreground">
                {source.file_type}
              </p>
            )}
          </div>
          <div className="flex-shrink-0">
            {getStatusBadge()}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
