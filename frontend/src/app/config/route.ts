import { NextRequest, NextResponse } from 'next/server'

/**
 * Runtime Configuration Endpoint
 *
 * This endpoint provides server-side environment variables to the client at runtime.
 * This solves the NEXT_PUBLIC_* limitation where variables are baked into the build.
 *
 * Environment Variables:
 * - API_URL: Where the browser/client should make API requests (public/external URL)
 * - INTERNAL_API_URL: Where Next.js server-side should proxy API requests (internal URL)
 *   Default: http://localhost:5055 (used by Next.js rewrites in next.config.ts)
 *
 * Why two different variables?
 * - API_URL: Used by browser clients, can be https://your-domain.com or http://server-ip:5055
 * - INTERNAL_API_URL: Used by Next.js rewrites for server-side proxying, typically http://localhost:5055
 *
 * Auto-detection logic for API_URL:
 * 1. If API_URL env var is set, use it (explicit override)
 * 2. Otherwise, detect from incoming HTTP request headers (zero-config)
 * 3. Fallback to localhost:5055 if detection fails
 *
 * This allows the same Docker image to work in different deployment scenarios.
 */
export async function GET(request: NextRequest) {
  // Priority 1: Check if API_URL is explicitly set
  const envApiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL

  if (envApiUrl) {
    return NextResponse.json({
      apiUrl: envApiUrl,
    })
  }

  // Priority 2: Check if behind a reverse proxy (cloud deployments like Render, Heroku, etc.)
  // In these environments, only the frontend port is exposed externally.
  // Port 5055 (API) is NOT accessible from the browser.
  // Return empty string so the frontend uses Next.js rewrites to proxy API requests
  // internally (frontend → localhost:5055).
  const isProxied = request.headers.get('x-forwarded-proto') !== null
  if (isProxied) {
    console.log('[runtime-config] Behind reverse proxy, using Next.js rewrites (empty apiUrl)')
    return NextResponse.json({
      apiUrl: '',
    })
  }

  // Priority 3: Auto-detect from request headers (direct access, e.g. local Docker)
  try {
    const hostHeader = request.headers.get('host')

    if (hostHeader) {
      // Extract just the hostname (remove port if present)
      const hostname = hostHeader.split(':')[0]
      const proto = request.nextUrl.protocol.replace(':', '') || 'http'

      // Construct the API URL with port 5055
      const apiUrl = `${proto}://${hostname}:5055`

      console.log(`[runtime-config] Auto-detected API URL: ${apiUrl} (proto=${proto}, host=${hostHeader})`)

      return NextResponse.json({
        apiUrl,
      })
    }
  } catch (error) {
    console.error('[runtime-config] Auto-detection failed:', error)
  }

  // Priority 4: Fallback to localhost
  console.log('[runtime-config] Using fallback: http://localhost:5055')
  return NextResponse.json({
    apiUrl: 'http://localhost:5055',
  })
}
