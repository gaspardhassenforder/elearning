'use client';

/**
 * Podcast Preview Component (Story 3.2, Task 5)
 *
 * Displays podcast audio player and transcript.
 */

import { Mic, Clock } from 'lucide-react';
import { type PodcastPreview } from '@/lib/api/artifacts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface PodcastPreviewProps {
  preview: PodcastPreview;
}

export function PodcastPreview({ preview }: PodcastPreviewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{preview.title}</h2>
          {preview.duration && (
            <div className="flex items-center gap-2 text-muted-foreground mt-1">
              <Clock className="h-4 w-4" />
              <span>{preview.duration}</span>
            </div>
          )}
        </div>
        <Badge variant="secondary" className="text-sm">
          <Mic className="mr-1 h-3 w-3" />
          Podcast
        </Badge>
      </div>

      {/* Audio Player */}
      {preview.audio_url && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Audio</CardTitle>
          </CardHeader>
          <CardContent>
            <audio
              controls
              className="w-full"
              src={preview.audio_url}
            >
              Your browser does not support the audio element.
            </audio>
          </CardContent>
        </Card>
      )}

      {/* Transcript */}
      {preview.transcript && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p className="whitespace-pre-wrap">{preview.transcript}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Placeholder if still processing */}
      {!preview.audio_url && !preview.transcript && (
        <Card>
          <CardContent className="py-12 text-center">
            <Mic className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Podcast is still being generated. Check back in a few minutes.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
