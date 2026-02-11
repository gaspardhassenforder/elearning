'use client'

import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { LearningObjectivesEditor } from '@/components/admin/LearningObjectivesEditor'
import { ModulePromptEditor } from '@/components/admin/ModulePromptEditor'
import { ModulePublishFlow } from '@/components/admin/ModulePublishFlow'
import { useTranslation } from '@/lib/hooks/use-translation'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'

export default function ConfigurePage() {
  const { t } = useTranslation()
  const params = useParams()
  const router = useRouter()
  const notebookId = params?.id ? decodeURIComponent(params.id as string) : ''

  const { data: notebook, isLoading } = useNotebook(notebookId)

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-96 w-full" />
        </div>
      </AppShell>
    )
  }

  if (!notebook) {
    return (
      <AppShell>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">{t.notebooks.notFound}</p>
        </div>
      </AppShell>
    )
  }

  const notebookPath = `/notebooks/${encodeURIComponent(notebookId)}`

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-8 max-w-4xl mx-auto">
          {/* Header */}
          <div className="space-y-2">
            <Link href={notebookPath}>
              <Button variant="ghost" size="sm" className="gap-2 -ml-2 mb-2">
                <ArrowLeft className="h-4 w-4" />
                {t.notebooks.backToNotebook}
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{notebook.name}</h1>
              <Badge variant={notebook.published ? 'default' : 'secondary'}>
                {notebook.published ? t.notebooks.published : t.notebooks.draft}
              </Badge>
            </div>
            <p className="text-muted-foreground">{t.notebooks.configureSubtitle}</p>
          </div>

          {/* Section 1: Learning Objectives */}
          <Card>
            <CardHeader>
              <CardTitle>{t.learningObjectives.title}</CardTitle>
              <CardDescription>{t.learningObjectives.subtitle}</CardDescription>
            </CardHeader>
            <CardContent>
              <LearningObjectivesEditor
                moduleId={notebookId}
                isEditMode={notebook.published}
              />
            </CardContent>
          </Card>

          {/* Section 2: AI Teacher Prompt */}
          <ModulePromptEditor moduleId={notebookId} />

          {/* Section 3: Publish */}
          <ModulePublishFlow
            notebookId={notebookId}
            isEditMode={notebook.published}
            onSuccess={() => router.push(notebookPath)}
            onBack={() => router.push(notebookPath)}
          />
        </div>
      </div>
    </AppShell>
  )
}
