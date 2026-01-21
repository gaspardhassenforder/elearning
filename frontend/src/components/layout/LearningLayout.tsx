'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, StickyNote, MessageSquare, BookOpen, GraduationCap } from 'lucide-react'

interface LearningLayoutProps {
  children: React.ReactNode
  notebookId: string
  notebookName?: string
}

export function LearningLayout({ children, notebookId, notebookName }: LearningLayoutProps) {
  const [mobileActiveTab, setMobileActiveTab] = useState<'sources' | 'notes' | 'chat' | 'document' | 'artifacts'>('chat')

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Mobile: Tabbed interface */}
      <div className="lg:hidden mb-4">
        <Tabs value={mobileActiveTab} onValueChange={(value) => setMobileActiveTab(value as 'sources' | 'notes' | 'chat' | 'document' | 'artifacts')}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="document" className="gap-2">
              <BookOpen className="h-4 w-4" />
              Document
            </TabsTrigger>
            <TabsTrigger value="sources" className="gap-2">
              <FileText className="h-4 w-4" />
              Sources
            </TabsTrigger>
            <TabsTrigger value="notes" className="gap-2">
              <StickyNote className="h-4 w-4" />
              Notes
            </TabsTrigger>
            <TabsTrigger value="artifacts" className="gap-2">
              <GraduationCap className="h-4 w-4" />
              Artifacts
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Mobile: Show only active tab */}
      <div className="flex-1 overflow-hidden lg:hidden">
        {children}
      </div>

      {/* Desktop: 3-column layout */}
      <div className={cn(
        'hidden lg:flex h-full min-h-0 gap-6 transition-all duration-150',
        'flex-row'
      )}>
        {children}
      </div>
    </div>
  )
}