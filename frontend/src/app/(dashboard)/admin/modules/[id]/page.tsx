'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'

/**
 * Legacy admin module detail — redirects to notebook page.
 */
export default function AdminModuleDetailRedirect() {
  const router = useRouter()
  const params = useParams()
  const moduleId = params?.id as string

  useEffect(() => {
    if (moduleId) {
      router.replace(`/notebooks/${encodeURIComponent(moduleId)}`)
    } else {
      router.replace('/notebooks')
    }
  }, [router, moduleId])

  return null
}
