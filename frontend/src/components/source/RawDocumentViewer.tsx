'use client'

import { useState, useEffect, useMemo } from 'react'
import { sourcesApi } from '@/lib/api/sources'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { AlertCircle, FileText } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'

interface RawDocumentViewerProps {
  sourceId: string
  filePath?: string
  fileAvailable?: boolean | null
}

type FileType = 'pdf' | 'image' | 'markdown' | 'text' | 'unknown'

const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif']
const MARKDOWN_EXTENSIONS = ['.md', '.markdown']
const TEXT_EXTENSIONS = ['.txt', '.text']

function getFileType(filePath: string): FileType {
  const lowerPath = filePath.toLowerCase()
  const extension = lowerPath.substring(lowerPath.lastIndexOf('.'))

  if (extension === '.pdf') {
    return 'pdf'
  }
  if (IMAGE_EXTENSIONS.includes(extension)) {
    return 'image'
  }
  if (MARKDOWN_EXTENSIONS.includes(extension)) {
    return 'markdown'
  }
  if (TEXT_EXTENSIONS.includes(extension)) {
    return 'text'
  }

  return 'unknown'
}

function getMimeType(filePath: string): string {
  const lowerPath = filePath.toLowerCase()
  const extension = lowerPath.substring(lowerPath.lastIndexOf('.'))

  const mimeTypes: Record<string, string> = {
    '.pdf': 'application/pdf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    '.md': 'text/markdown',
    '.markdown': 'text/markdown',
    '.txt': 'text/plain',
    '.text': 'text/plain',
  }

  return mimeTypes[extension] || 'application/octet-stream'
}

export function RawDocumentViewer({ sourceId, filePath, fileAvailable }: RawDocumentViewerProps) {
  const { t } = useTranslation()
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [textContent, setTextContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fileType = useMemo(() => {
    if (!filePath) return 'unknown'
    return getFileType(filePath)
  }, [filePath])

  useEffect(() => {
    if (!filePath || fileAvailable === false) {
      return
    }

    const loadFile = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await sourcesApi.downloadFile(sourceId)
        const blob = response.data

        if (fileType === 'pdf' || fileType === 'image') {
          // Read blob as ArrayBuffer to ensure we have raw data
          const arrayBuffer = await blob.arrayBuffer()
          // Create a new blob with the correct MIME type to prevent download
          const mimeType = getMimeType(filePath)
          const typedBlob = new Blob([arrayBuffer], { type: mimeType })
          const url = window.URL.createObjectURL(typedBlob)
          setBlobUrl(url)
        } else if (fileType === 'markdown' || fileType === 'text') {
          // Read as text for markdown/text files
          const text = await blob.text()
          setTextContent(text)
        } else {
          // For unknown types, try to read as text
          const text = await blob.text()
          setTextContent(text)
        }
      } catch (err) {
        console.error('Failed to load file:', err)
        setError(t.sources.fileUnavailable || 'File unavailable')
      } finally {
        setLoading(false)
      }
    }

    void loadFile()
  }, [sourceId, filePath, fileType, fileAvailable, t])

  // Cleanup blob URL when it changes or component unmounts
  useEffect(() => {
    return () => {
      if (blobUrl) {
        window.URL.revokeObjectURL(blobUrl)
      }
    }
  }, [blobUrl])

  if (!filePath) {
    return (
      <Card className="flex flex-col h-full">
        <CardHeader className="flex-shrink-0">
          <CardTitle>{t.sources.raw}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>{t.sources.raw}</AlertTitle>
            <AlertDescription>
              This source does not have an associated file to display.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (fileAvailable === false) {
    return (
      <Card className="flex flex-col h-full">
        <CardHeader className="flex-shrink-0">
          <CardTitle>{t.sources.raw}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>{t.sources.fileUnavailable}</AlertTitle>
            <AlertDescription>
              {t.sources.fileUnavailableDesc || 'The file is no longer available on the server.'}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card className="flex flex-col h-full">
        <CardHeader className="flex-shrink-0">
          <CardTitle>{t.sources.raw}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <LoadingSpinner />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="flex flex-col h-full">
        <CardHeader className="flex-shrink-0">
          <CardTitle>{t.sources.raw}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          {t.sources.raw}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {fileType === 'pdf' && blobUrl && (
          <div className="flex-1 w-full border rounded-lg overflow-hidden bg-muted min-h-0">
            <iframe
              src={blobUrl}
              title={t.sources.raw}
              className="w-full h-full"
              style={{ 
                border: 'none'
              }}
            />
          </div>
        )}

        {fileType === 'image' && blobUrl && (
          <div className="flex-1 flex items-center justify-center overflow-auto">
            <img
              src={blobUrl}
              alt={t.sources.raw}
              className="max-w-full max-h-full object-contain rounded-lg"
            />
          </div>
        )}

        {(fileType === 'markdown' || fileType === 'text') && textContent && (
          <div className="flex-1 overflow-y-auto prose prose-sm prose-neutral dark:prose-invert max-w-none prose-headings:font-semibold prose-a:text-blue-600 prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-p:mb-4 prose-p:leading-7 prose-li:mb-2">
            {fileType === 'markdown' ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p className="mb-4">{children}</p>,
                  h1: ({ children }) => <h1 className="text-2xl font-bold mt-6 mb-4">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-bold mt-5 mb-3">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>,
                  ul: ({ children }) => <ul className="mb-4 list-disc pl-6">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-4 list-decimal pl-6">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  table: ({ children }) => (
                    <div className="my-4 overflow-x-auto">
                      <table className="min-w-full border-collapse border border-border">{children}</table>
                    </div>
                  ),
                  thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                  tbody: ({ children }) => <tbody>{children}</tbody>,
                  tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
                  th: ({ children }) => <th className="border border-border px-3 py-2 text-left font-semibold">{children}</th>,
                  td: ({ children }) => <td className="border border-border px-3 py-2">{children}</td>,
                }}
              >
                {textContent}
              </ReactMarkdown>
            ) : (
              <pre className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded-lg overflow-x-auto">
                {textContent}
              </pre>
            )}
          </div>
        )}

        {fileType === 'unknown' && textContent && (
          <div className="flex-1 overflow-y-auto prose prose-sm prose-neutral dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded-lg overflow-x-auto">
              {textContent}
            </pre>
          </div>
        )}

        {!blobUrl && !textContent && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Unable to display file</AlertTitle>
            <AlertDescription>
              The file type ({fileType}) is not supported for preview, or the file could not be loaded.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
