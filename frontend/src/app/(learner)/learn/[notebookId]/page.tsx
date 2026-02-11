'use client'

/**
 * Legacy Learn Page - Redirects to new modules/[id] route
 *
 * This page previously contained a 3-column layout for learners.
 * It has been replaced by the ChatGPT-like interface at /modules/[id].
 */

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

export default function LegacyLearnPage() {
  const params = useParams()
  const router = useRouter()
  const notebookId = params?.notebookId ? decodeURIComponent(params.notebookId as string) : ''

  useEffect(() => {
    if (notebookId) {
      router.replace(`/modules/${notebookId}`)
    } else {
      router.replace('/modules')
    }
  }, [notebookId, router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <LoadingSpinner size="lg" />
    </div>
  )
}
