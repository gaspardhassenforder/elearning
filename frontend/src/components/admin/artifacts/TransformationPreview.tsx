'use client';

/**
 * Transformation Preview Component (Story 3.2, Task 5)
 *
 * Displays transformed content with markdown rendering.
 */

import { Wand2 } from 'lucide-react';
import { type TransformationPreview } from '@/lib/api/artifacts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TransformationPreviewProps {
  preview: TransformationPreview;
}

export function TransformationPreview({ preview }: TransformationPreviewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{preview.title}</h2>
          <div className="flex items-center gap-3 text-muted-foreground mt-1">
            {preview.transformation_name && (
              <Badge variant="outline" className="text-xs">
                {preview.transformation_name}
              </Badge>
            )}
            <span>{preview.word_count} words</span>
          </div>
        </div>
        <Badge variant="secondary" className="text-sm">
          <Wand2 className="mr-1 h-3 w-3" />
          Transformation
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
