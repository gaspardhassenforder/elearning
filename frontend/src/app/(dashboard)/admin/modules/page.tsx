'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

/**
 * Legacy admin modules list — redirects to unified notebooks page.
 */
export default function AdminModulesRedirect() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/notebooks')
  }, [router])

  return null
}
