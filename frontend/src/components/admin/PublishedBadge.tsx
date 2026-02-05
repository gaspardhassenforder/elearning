/**
 * Published Badge Component (Story 3.5, Task 8)
 *
 * Displays module publication status with:
 * - "Published" badge (success variant) for published modules
 * - "Draft" badge (secondary variant) for unpublished modules
 * - i18n support for badge labels
 */

'use client'

import { useTranslation } from '@/lib/hooks/use-translation'
import { Badge } from '@/components/ui/badge'

interface PublishedBadgeProps {
  published: boolean
}

export function PublishedBadge({ published }: PublishedBadgeProps) {
  const { t } = useTranslation()

  return (
    <Badge variant={published ? 'success' : 'secondary'}>
      {published ? t.modules.published : t.modules.draft}
    </Badge>
  )
}
