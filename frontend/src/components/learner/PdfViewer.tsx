'use client'

/**
 * PdfViewer Component
 *
 * Renders PDF documents using the PDF.js pre-built viewer (viewer.html)
 * served from /pdfjs/web/. Supports page navigation via #page=N and
 * text search highlighting via #search=text.
 *
 * Cookie-based auth means the viewer can fetch PDFs directly from the
 * API endpoint without blob URLs or ArrayBuffer passing.
 */

interface PdfViewerProps {
  sourceId: string
  pageNumber?: number
  searchText?: string
}

export function PdfViewer({ sourceId, pageNumber, searchText }: PdfViewerProps) {
  const fileUrl = encodeURIComponent(`/api/sources/${sourceId}/file`)

  let hash = ''
  if (pageNumber) hash += `page=${pageNumber}`
  if (searchText) {
    const phrase = extractSearchPhrase(searchText)
    if (phrase) hash += `${hash ? '&' : ''}search=${encodeURIComponent(phrase)}`
  }

  const src = `/pdfjs/web/viewer.html?file=${fileUrl}${hash ? '#' + hash : ''}`

  return <iframe src={src} className="w-full h-full border-0" title="PDF viewer" />
}

/**
 * Extract a short distinctive phrase (up to 6 words) for PDF.js search.
 * Strips markdown formatting before extracting.
 */
function extractSearchPhrase(text: string): string {
  const clean = text
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/#{1,6}\s/g, '')
    .replace(/`/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return clean.split(' ').filter(Boolean).slice(0, 6).join(' ')
}
