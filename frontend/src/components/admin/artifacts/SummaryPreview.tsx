'use client';

/**
 * Summary Preview Component (Story 3.2, Task 5)
 *
 * Displays summary content with markdown rendering.
 */

import { BookOpen, FileText } from 'lucide-react';
import { type SummaryPreview } from '@/lib/api/artifacts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SummaryPreviewProps {
  preview: SummaryPreview;
}

export function SummaryPreview({ preview }: SummaryPreviewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{preview.title}</h2>
          <p className="text-muted-foreground mt-1">
            {preview.word_count} words
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          <BookOpen className="mr-1 h-3 w-3" />
          Summary
        </Badge>
      </div>

      {/* Content */}
      <Card>
        <CardContent className="pt-6">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <div dangerouslySetInnerHTML={{ __html: formatMarkdown(preview.content) }} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Simple markdown-to-HTML converter
 * For production, consider using a library like react-markdown
 */
function formatMarkdown(content: string): string {
  return content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/gm, '<p>$1</p>');
}
