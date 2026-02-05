'use client';

/**
 * Async Status Bar Component (Story 3.2, Task 4)
 *
 * Persistent status indicator for long-running async operations (podcasts).
 */

import { Loader2, Check, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface AsyncStatusBarProps {
  status: 'pending' | 'processing' | 'completed' | 'error';
  message: string;
  progress?: number;
  className?: string;
}

export function AsyncStatusBar({ status, message, progress, className }: AsyncStatusBarProps) {
  const getVariant = () => {
    switch (status) {
      case 'error':
        return 'destructive';
      case 'completed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getIcon = () => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'completed':
        return <Check className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <Alert variant={getVariant()} className={cn('', className)}>
      <div className="flex items-center gap-3">
        {getIcon()}
        <div className="flex-1">
          <AlertDescription>{message}</AlertDescription>
          {progress !== undefined && status === 'processing' && (
            <Progress value={progress} className="mt-2 h-2" />
          )}
        </div>
      </div>
    </Alert>
  );
}
