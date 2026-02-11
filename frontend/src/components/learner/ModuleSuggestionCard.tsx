/**
 * ModuleSuggestionCard Component (Story 6.1)
 *
 * Displays a clickable module suggestion from the navigation assistant.
 * Shows title, description, and "Open module" action.
 */

'use client'

import { useRouter } from 'next/navigation'
import { ArrowRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNavigationStore } from '@/lib/stores/navigation-store'
import type { ModuleSuggestion } from '@/lib/api/navigation'

interface ModuleSuggestionCardProps {
  suggestion: ModuleSuggestion
}

export function ModuleSuggestionCard({ suggestion }: ModuleSuggestionCardProps) {
  const { t } = useTranslation()
  const router = useRouter()
  const { closeNavigator } = useNavigationStore()

  const handleOpenModule = () => {
    // Navigate to module
    router.push(`/modules/${suggestion.id}`)
    // Close navigation overlay
    closeNavigator()
  }

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md hover:scale-[1.02] border-muted"
      onClick={handleOpenModule}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm mb-1 line-clamp-1">
              {suggestion.title}
            </h4>
            <p className="text-xs text-muted-foreground line-clamp-2">
              {suggestion.description || t.learner.navigation.moduleNotFound}
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="shrink-0 h-8"
            onClick={(e) => {
              e.stopPropagation()
              handleOpenModule()
            }}
          >
            <span className="text-xs">{t.learner.navigation.openModule}</span>
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
