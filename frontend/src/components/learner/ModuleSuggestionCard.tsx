'use client'

/**
 * Story 4.5: Module Suggestion Card
 *
 * Displays a suggested module card when learner completes all objectives.
 * Shows module title, description, and "Start Module" link.
 */

import { useRouter } from 'next/navigation'
import { BookOpen, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useTranslation } from '@/lib/hooks/use-translation'

interface ModuleSuggestionCardProps {
  moduleId: string
  title: string
  description?: string
}

export function ModuleSuggestionCard({
  moduleId,
  title,
  description,
}: ModuleSuggestionCardProps) {
  const { t } = useTranslation()
  const router = useRouter()

  const handleStartModule = () => {
    // Navigate to module page
    router.push(`/modules/${moduleId}`)
  }

  return (
    <Card className="bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20 hover:border-primary/40 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
            <BookOpen className="h-5 w-5 text-primary" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm mb-1 text-foreground">
              {title}
            </h4>
            {description && (
              <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                {description}
              </p>
            )}

            {/* Start button */}
            <Button
              size="sm"
              onClick={handleStartModule}
              className="h-8 text-xs"
            >
              {t.learner.chat.startModule}
              <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
