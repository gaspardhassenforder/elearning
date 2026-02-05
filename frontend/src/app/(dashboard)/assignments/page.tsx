'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { AssignmentMatrix } from '@/components/admin/AssignmentMatrix'
import { useAssignmentMatrix } from '@/lib/hooks/use-assignments'
import { useTranslation } from '@/lib/hooks/use-translation'
import { RefreshCw, LayoutGrid } from 'lucide-react'

export default function AssignmentsPage() {
  const { t } = useTranslation()
  const { refetch, isLoading } = useAssignmentMatrix()

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <LayoutGrid className="h-6 w-6" />
                {t.assignments.title}
              </h1>
              <p className="text-muted-foreground mt-1">
                {t.assignments.subtitle}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          <AssignmentMatrix />
        </div>
      </div>
    </AppShell>
  )
}
