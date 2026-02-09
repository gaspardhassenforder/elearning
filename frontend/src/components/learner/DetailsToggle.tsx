/**
 * Story 7.8: Details Toggle Component
 *
 * Subtle toggle button for expanding/collapsing AI message details view.
 * Shows tool calls, reasoning steps, and execution order.
 */

import { ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/lib/hooks/use-translation'
import type { LearnerChatMessage } from '@/lib/api/learner-chat'

interface DetailsToggleProps {
  message: LearnerChatMessage
  isExpanded: boolean
  onToggle: () => void
}

export function DetailsToggle({ message, isExpanded, onToggle }: DetailsToggleProps) {
  const { t } = useTranslation()

  // Only render for assistant messages with tool calls
  if (message.role !== 'assistant' || !message.toolCalls || message.toolCalls.length === 0) {
    return null
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onToggle}
      aria-label={isExpanded ? t.learner.details.hide : t.learner.details.show}
      aria-expanded={isExpanded}
      className="min-h-[44px] px-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
    >
      {isExpanded ? (
        <>
          <ChevronUp className="h-3 w-3 mr-1.5" />
          {t.learner.details.hide}
        </>
      ) : (
        <>
          <ChevronDown className="h-3 w-3 mr-1.5" />
          {t.learner.details.show}
        </>
      )}
    </Button>
  )
}
