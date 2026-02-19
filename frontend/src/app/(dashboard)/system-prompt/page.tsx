'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Info } from 'lucide-react'

import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useTranslation } from '@/lib/hooks/use-translation'
import { systemPromptApi } from '@/lib/api/system-prompt'
import { QUERY_KEYS } from '@/lib/api/query-client'

export default function SystemPromptPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: QUERY_KEYS.systemPrompt(),
    queryFn: () => systemPromptApi.get().then((r) => r.data),
  })

  useEffect(() => {
    if (data?.content !== undefined) {
      setContent(data.content)
    }
  }, [data?.content])

  const mutation = useMutation({
    mutationFn: (newContent: string) => systemPromptApi.update(newContent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.systemPrompt() })
      toast.success(t.systemPrompt.saveSuccess)
    },
    onError: () => {
      toast.error(t.systemPrompt.saveError)
    },
  })

  const handleSave = () => {
    mutation.mutate(content)
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h1 className="text-3xl font-bold">{t.systemPrompt.title}</h1>
              <p className="text-muted-foreground mt-2">{t.systemPrompt.desc}</p>
            </div>

            {/* Info box */}
            <div className="rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/30 p-4 space-y-2">
              <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 font-medium">
                <Info className="h-4 w-4" />
                {t.systemPrompt.infoTitle}
              </div>
              <p className="text-sm text-blue-600 dark:text-blue-300">
                {t.systemPrompt.infoDescription}
              </p>
              <p className="text-sm font-medium text-amber-600 dark:text-amber-400">
                {t.systemPrompt.infoWarning}
              </p>
            </div>

            {/* Editor area */}
            <div className="space-y-3">
              {isLoading && (
                <p className="text-muted-foreground text-sm">{t.systemPrompt.loading}</p>
              )}
              {isError && (
                <p className="text-destructive text-sm">{t.systemPrompt.loadError}</p>
              )}
              {!isLoading && (
                <>
                  <Textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder={t.systemPrompt.placeholder}
                    className="min-h-[420px] font-mono text-sm resize-y"
                    disabled={mutation.isPending}
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {content.length} {t.systemPrompt.charactersLabel}
                    </span>
                    <Button
                      onClick={handleSave}
                      disabled={mutation.isPending}
                    >
                      {mutation.isPending ? t.common.saving : t.common.save}
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
