'use client';

/**
 * Document Uploader Component (Story 3.1, Task 5)
 *
 * Drag-and-drop file uploader with progress tracking.
 * Polls backend for processing status and displays inline errors.
 */

import { useState, useCallback } from 'react';
import { Upload, FileText, Check, AlertCircle, Loader2, X } from 'lucide-react';
import { useUploadDocument, useModuleDocuments } from '@/lib/hooks/use-modules';
import { useTranslation } from '@/lib/hooks/use-translation';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface DocumentUploaderProps {
  moduleId: string;
}

interface UploadingFile {
  file: File;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  id?: string;
  error?: string;
}

export function DocumentUploader({ moduleId }: DocumentUploaderProps) {
  const { t } = useTranslation();
  const uploadDocument = useUploadDocument(moduleId);
  const { data: documents } = useModuleDocuments(moduleId, { pollingInterval: 2000 });

  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  }, []);

  const handleFiles = async (files: File[]) => {
    // Add files to uploading state
    const newFiles: UploadingFile[] = files.map((file) => ({
      file,
      status: 'uploading',
      progress: 0,
    }));

    setUploadingFiles((prev) => [...prev, ...newFiles]);

    // Upload each file
    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      try {
        // Update progress to show uploading
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.file === file ? { ...f, progress: 50 } : f
          )
        );

        // Upload file
        const result = await uploadDocument.mutateAsync(file);

        // Update to processing state
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.file === file
              ? { ...f, status: 'processing', progress: 100, id: result.id }
              : f
          )
        );
      } catch (error: any) {
        // Update to error state
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.file === file
              ? {
                  ...f,
                  status: 'error',
                  progress: 0,
                  error: error?.response?.data?.detail || t.modules.uploadFailed,
                }
              : f
          )
        );
      }
    }
  };

  const handleRetry = async (uploadingFile: UploadingFile) => {
    setUploadingFiles((prev) =>
      prev.map((f) =>
        f === uploadingFile ? { ...f, status: 'uploading', progress: 0, error: undefined } : f
      )
    );

    try {
      setUploadingFiles((prev) =>
        prev.map((f) => (f === uploadingFile ? { ...f, progress: 50 } : f))
      );

      const result = await uploadDocument.mutateAsync(uploadingFile.file);

      setUploadingFiles((prev) =>
        prev.map((f) =>
          f === uploadingFile
            ? { ...f, status: 'processing', progress: 100, id: result.id }
            : f
        )
      );
    } catch (error: any) {
      setUploadingFiles((prev) =>
        prev.map((f) =>
          f === uploadingFile
            ? {
                ...f,
                status: 'error',
                progress: 0,
                error: error?.response?.data?.detail || t.modules.uploadFailed,
              }
            : f
        )
      );
    }
  };

  const handleRemove = (uploadingFile: UploadingFile) => {
    setUploadingFiles((prev) => prev.filter((f) => f !== uploadingFile));
  };

  // Update status from polling
  const updateStatusFromDocuments = () => {
    if (!documents) return;

    setUploadingFiles((prev) =>
      prev.map((uploadingFile) => {
        if (!uploadingFile.id) return uploadingFile;

        const doc = documents.find((d) => d.id === uploadingFile.id);
        if (!doc) return uploadingFile;

        if (doc.status === 'completed') {
          return { ...uploadingFile, status: 'completed' as const };
        } else if (doc.status === 'error') {
          return {
            ...uploadingFile,
            status: 'error' as const,
            error: doc.error_message || t.modules.documentError,
          };
        }

        return uploadingFile;
      })
    );
  };

  // Run status update when documents change
  if (documents) {
    updateStatusFromDocuments();
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        )}
      >
        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-sm font-medium mb-2">{t.modules.dragDrop}</p>
        <p className="text-xs text-muted-foreground mb-4">{t.modules.orClickBrowse}</p>

        <input
          type="file"
          id="file-upload"
          multiple
          onChange={handleFileInput}
          className="hidden"
          accept=".pdf,.docx,.doc,.txt,.md"
        />

        <Button asChild variant="outline">
          <label htmlFor="file-upload" className="cursor-pointer">
            {t.modules.uploadDocuments}
          </label>
        </Button>

        <p className="text-xs text-muted-foreground mt-4">
          {t.modules.supportedFormats}
        </p>
        <p className="text-xs text-muted-foreground">{t.modules.maxFileSize}</p>
      </div>

      {/* Uploading Files List */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">{t.modules.uploadingFiles}</h3>
          {uploadingFiles.map((uploadingFile, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 border rounded-lg"
            >
              <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {uploadingFile.file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(uploadingFile.file.size / 1024 / 1024).toFixed(2)} MB
                </p>

                {/* Progress Bar */}
                {uploadingFile.status === 'uploading' && (
                  <Progress value={uploadingFile.progress} className="mt-2" />
                )}

                {/* Error Message */}
                {uploadingFile.status === 'error' && uploadingFile.error && (
                  <p className="text-xs text-destructive mt-1">
                    {uploadingFile.error}
                  </p>
                )}
              </div>

              {/* Status Icon */}
              <div className="flex-shrink-0">
                {uploadingFile.status === 'uploading' && (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                )}
                {uploadingFile.status === 'processing' && (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                )}
                {uploadingFile.status === 'completed' && (
                  <Check className="h-5 w-5 text-green-600" />
                )}
                {uploadingFile.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-destructive" />
                )}
              </div>

              {/* Actions */}
              {uploadingFile.status === 'error' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRetry(uploadingFile)}
                >
                  {t.modules.retryUpload}
                </Button>
              )}

              {(uploadingFile.status === 'completed' ||
                uploadingFile.status === 'error') && (
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => handleRemove(uploadingFile)}
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Existing Documents */}
      {documents && documents.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">
            {t.modules.documentsUploaded.replace('{count}', String(documents.length))}
          </h3>
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-3 p-3 border rounded-lg bg-muted/20"
            >
              <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{doc.title}</p>
                <p className="text-xs text-muted-foreground">
                  {doc.status === 'processing' && t.modules.documentProcessing}
                  {doc.status === 'completed' && t.modules.documentCompleted}
                  {doc.status === 'error' && doc.error_message}
                </p>
              </div>
              {doc.status === 'completed' && (
                <Check className="h-5 w-5 text-green-600 flex-shrink-0" />
              )}
              {doc.status === 'processing' && (
                <Loader2 className="h-5 w-5 animate-spin text-primary flex-shrink-0" />
              )}
              {doc.status === 'error' && (
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
