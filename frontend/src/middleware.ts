import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Next.js Middleware for route protection.
 *
 * Per Next.js 16 best practices, this middleware is LIGHTWEIGHT:
 * - Only checks cookie existence for fast redirects
 * - Does NOT validate JWT signature (happens in AuthProvider via /auth/me)
 * - Minimal logic to avoid adding latency to every request
 */

const PUBLIC_PATHS = ['/login', '/register']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('access_token')?.value

  // Allow public paths
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) {
    // If authenticated, redirect away from login to root (which triggers role routing)
    if (token) {
      return NextResponse.redirect(new URL('/', request.url))
    }
    return NextResponse.next()
  }

  // Redirect to login if no token
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  // Match all paths except static files, API routes, and health endpoints
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api|health).*)'],
}
