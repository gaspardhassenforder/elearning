# Story 1.2: Role-Based Access Control & Route Protection

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform operator**,
I want the system to distinguish between Admin and Learner roles and restrict access accordingly,
So that each role only sees their authorized interface.

## Acceptance Criteria

1. **Given** a logged-in user with role "admin" **When** they access the platform **Then** they are routed to the `(admin)` route group

2. **Given** a logged-in user with role "learner" **When** they access the platform **Then** they are routed to the `(learner)` route group

3. **Given** a learner **When** they attempt to access an admin-only API endpoint **Then** a 403 Forbidden response is returned

4. **Given** an admin **When** they attempt to access a learner-only API endpoint **Then** a 403 Forbidden response is returned

5. **Given** an unauthenticated user **When** they access any non-public route **Then** they are redirected to `/login`

6. **Given** a learner makes any API request **When** the request reaches a learner-scoped endpoint **Then** all database queries are automatically scoped to the learner's company via the `get_current_learner()` dependency (extracts company_id from the authenticated user)

## Tasks / Subtasks

- [ ] Task 1: Create `require_admin()` FastAPI dependency (AC: #3)
  - [ ] 1.1: In `api/auth.py`, add `require_admin()` dependency that wraps `get_current_user()` and checks `user.role == "admin"`
  - [ ] 1.2: Return 403 Forbidden with detail "Admin access required" if role is not admin
  - [ ] 1.3: Return type is `User` (the authenticated admin user object)
- [ ] Task 2: Create `require_learner()` FastAPI dependency (AC: #4)
  - [ ] 2.1: In `api/auth.py`, add `require_learner()` dependency that wraps `get_current_user()` and checks `user.role == "learner"`
  - [ ] 2.2: Return 403 Forbidden with detail "Learner access required" if role is not learner
  - [ ] 2.3: Return type is `User` (the authenticated learner user object)
- [ ] Task 3: Create `get_current_learner()` FastAPI dependency with company scoping (AC: #6)
  - [ ] 3.1: In `api/auth.py`, add `get_current_learner()` that calls `require_learner()` AND extracts `company_id` from the user
  - [ ] 3.2: If `company_id` is null/missing, return 403 with detail "Learner must be assigned to a company"
  - [ ] 3.3: Return a dataclass or dict: `{ user: User, company_id: str }` so downstream endpoints can use both
  - [ ] 3.4: This dependency is the single enforcement point for per-company data isolation on all future learner endpoints
- [ ] Task 4: Apply auth dependencies to ALL existing API endpoints (AC: #3, #4, #5)
  - [ ] 4.1: Add `Depends(require_admin)` to all existing notebook CRUD endpoints (create, update, delete) in `api/routers/notebooks.py`
  - [ ] 4.2: Add `Depends(get_current_user)` to all read endpoints (notebooks list, notebook get, sources list, etc.) — both roles can read
  - [ ] 4.3: Add `Depends(require_admin)` to source create/update/delete endpoints in `api/routers/sources.py`
  - [ ] 4.4: Add `Depends(require_admin)` to settings, models config, and other admin-only endpoints
  - [ ] 4.5: Add `Depends(get_current_user)` to chat, search, artifacts, and quiz read endpoints
  - [ ] 4.6: Ensure public endpoints remain unprotected: `/auth/login`, `/auth/register`, `/auth/status`, `/auth/refresh`, `/health`, `/docs`, `/openapi.json`, `/redoc`, `/api/config`
  - [ ] 4.7: Verify every protected endpoint returns 401 without token and 403 with wrong role
- [ ] Task 5: Create Next.js middleware.ts for route protection (AC: #1, #2, #5)
  - [ ] 5.1: Create `frontend/src/middleware.ts` (Next.js middleware at the App Router level)
  - [ ] 5.2: Check for `access_token` cookie presence on every request
  - [ ] 5.3: If no token and route is protected → redirect to `/login`
  - [ ] 5.4: **Do NOT validate JWT in middleware** (per Next.js 16 best practices — keep middleware lightweight). Only check cookie existence.
  - [ ] 5.5: Configure matcher to exclude: `/_next/static`, `/_next/image`, `/favicon.ico`, `/login`, `/api`
  - [ ] 5.6: If token exists and path is `/login` → redirect to `/` (root, which triggers role routing)
- [ ] Task 6: Create AuthProvider component (AC: #1, #2, #5)
  - [ ] 6.1: Create `frontend/src/components/providers/AuthProvider.tsx`
  - [ ] 6.2: On mount, call `GET /auth/me` to validate token and get user data (id, role, company_id, username)
  - [ ] 6.3: Store user data in auth-store (extend Zustand store with `user: { id, username, role, company_id } | null`)
  - [ ] 6.4: If token validation fails (401), clear auth state and redirect to `/login`
  - [ ] 6.5: Provide `isLoading`, `isAuthenticated`, `user` through context or Zustand store
  - [ ] 6.6: Wrap the app in AuthProvider in root layout
- [ ] Task 7: Update auth-store.ts with user/role state (AC: #1, #2)
  - [ ] 7.1: Extend `AuthState` interface with `user: { id: string, username: string, role: 'admin' | 'learner', company_id: string | null } | null`
  - [ ] 7.2: Update `login()` method to call `/auth/login` and then `/auth/me` to populate user data
  - [ ] 7.3: Update `logout()` to call `/auth/logout` (clear httpOnly cookies) and clear user state
  - [ ] 7.4: Remove the old password-based `login()` that tested against `/api/notebooks`
  - [ ] 7.5: Update persistence to NOT store user object (it's fetched from `/auth/me` on each load)
- [ ] Task 8: Implement role-based routing in root layout (AC: #1, #2)
  - [ ] 8.1: In `frontend/src/app/layout.tsx`, after AuthProvider hydration, check `user.role`
  - [ ] 8.2: If user is authenticated and at root `/` → redirect admin to `/(admin)/notebooks`, learner to `/(learner)/modules`
  - [ ] 8.3: Ensure the redirect happens server-side or on initial client render to avoid flash
- [ ] Task 9: Rename `(dashboard)` route group to `(admin)` (AC: #1)
  - [ ] 9.1: Rename directory `frontend/src/app/(dashboard)/` to `frontend/src/app/(admin)/`
  - [ ] 9.2: Update `(admin)/layout.tsx` — add admin role check. If user is not admin, redirect to `/(learner)/modules`
  - [ ] 9.3: Update all internal imports and relative paths that reference `(dashboard)`
  - [ ] 9.4: Verify all existing admin routes still work: `/notebooks`, `/sources`, `/search`, `/models`, `/settings`, `/advanced`, `/podcasts`, `/transformations`
- [ ] Task 10: Create `(learner)` route group scaffold (AC: #2)
  - [ ] 10.1: Create `frontend/src/app/(learner)/layout.tsx` — minimal layout with learner role check (redirect non-learners to `/(admin)`)
  - [ ] 10.2: Create `frontend/src/app/(learner)/modules/page.tsx` — placeholder "Module Selection" page (simple header + "Coming soon" text)
  - [ ] 10.3: Add learner role guard in layout: if user is not learner, redirect to admin
  - [ ] 10.4: This is a scaffold only — full learner UI comes in later epics
- [ ] Task 11: Update login page for role-aware redirect (AC: #1, #2)
  - [ ] 11.1: Update `frontend/src/app/(auth)/login/page.tsx`
  - [ ] 11.2: On successful login, redirect based on role: admin → `/notebooks`, learner → `/modules`
  - [ ] 11.3: Update the login form to use the new `/auth/login` endpoint (POST with username/password body, NOT bearer token)
  - [ ] 11.4: Handle httpOnly cookie-based auth (no need to manually store tokens — browser handles cookies)
  - [ ] 11.5: Update the login form UI: replace single password field with username + password fields
- [ ] Task 12: Update API client for cookie-based auth (AC: #5)
  - [ ] 12.1: Update `frontend/src/lib/api/client.ts` — remove `Authorization: Bearer` header injection
  - [ ] 12.2: Ensure `withCredentials: true` (or `credentials: 'include'` for fetch) so cookies are sent automatically
  - [ ] 12.3: Add 401 interceptor: on 401 response, attempt token refresh via `POST /auth/refresh`, then retry. On refresh failure, redirect to `/login`
  - [ ] 12.4: Add 403 interceptor: on 403 response, show toast "Access denied" (do NOT redirect — let user know they lack permission)
- [ ] Task 13: Write backend tests (AC: #3, #4, #6)
  - [ ] 13.1: Add to `tests/test_auth.py` (extending from Story 1.1)
  - [ ] 13.2: Test `require_admin()` — admin user passes, learner gets 403
  - [ ] 13.3: Test `require_learner()` — learner passes, admin gets 403
  - [ ] 13.4: Test `get_current_learner()` — learner with company_id passes, learner without company_id gets 403
  - [ ] 13.5: Test existing notebook endpoint now requires auth (401 without token)
  - [ ] 13.6: Test existing notebook create endpoint requires admin role (403 for learner)
  - [ ] 13.7: Test protected endpoint returns 401 with expired token

## Dev Notes

### Architecture Decisions

- **Three auth dependencies, not one.** `get_current_user()` (from Story 1.1) validates any authenticated user. `require_admin()` and `require_learner()` add role gates. `get_current_learner()` adds company scoping. Each endpoint picks the right dependency.
- **Company scoping is a dependency, NOT a query filter you remember to add.** `get_current_learner()` extracts and returns `company_id`. ALL future learner endpoints use this dependency, making it impossible to forget the company filter.
- **Next.js middleware is LIGHTWEIGHT.** Per Next.js 16 best practices, middleware only checks cookie existence for fast redirects. JWT signature validation happens in Server Components or via `/auth/me` API call. This avoids adding latency to every request.
- **Cookie-based auth, NOT token in headers.** Story 1.1 sets httpOnly cookies. The frontend never reads or stores JWT tokens directly. `withCredentials: true` sends cookies automatically. This is more secure against XSS.
- **Route group renaming preserves URLs.** Renaming `(dashboard)` to `(admin)` has zero URL impact — route groups are non-URL-affecting in Next.js App Router. All existing `/notebooks`, `/sources`, etc. URLs continue working.

### Critical Implementation Details

**Auth Dependencies Chain:**
```python
# api/auth.py — extend with these dependencies

async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != "admin":
        logger.error(f"Admin access denied for user {user.id} with role {user.role}")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_learner(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != "learner":
        logger.error(f"Learner access denied for user {user.id} with role {user.role}")
        raise HTTPException(status_code=403, detail="Learner access required")
    return user

async def get_current_learner(
    user: User = Depends(require_learner)
) -> dict:
    if not user.company_id:
        logger.error(f"Learner {user.id} has no company assignment")
        raise HTTPException(status_code=403, detail="Learner must be assigned to a company")
    return {"user": user, "company_id": user.company_id}
```

**Applying to Existing Endpoints (example):**
```python
# api/routers/notebooks.py
from api.auth import get_current_user, require_admin

@router.get("/notebooks")
async def list_notebooks(user: User = Depends(get_current_user)):
    # Both admin and learner can list (learner will be company-scoped in future stories)
    return await notebook_service.list_notebooks()

@router.post("/notebooks")
async def create_notebook(data: NotebookCreate, admin: User = Depends(require_admin)):
    # Only admin can create
    return await notebook_service.create_notebook(data)
```

**Next.js Middleware (lightweight):**
```typescript
// frontend/src/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login', '/register']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('access_token')?.value

  // Allow public paths
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) {
    // If authenticated, redirect away from login
    if (token) {
      return NextResponse.redirect(new URL('/', request.url))
    }
    return NextResponse.next()
  }

  // Redirect to login if no token
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api|health).*)'],
}
```

**AuthProvider Pattern:**
```typescript
// frontend/src/components/providers/AuthProvider.tsx
'use client'
import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/stores/auth-store'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, isLoading, fetchCurrentUser } = useAuth()

  useEffect(() => {
    fetchCurrentUser() // calls GET /auth/me
  }, [])

  // Role-based redirect after auth is resolved
  useEffect(() => {
    if (isLoading || !user) return
    if (pathname === '/') {
      router.replace(user.role === 'admin' ? '/notebooks' : '/modules')
    }
  }, [user, isLoading, pathname])

  if (isLoading) return <LoadingSpinner />
  return <>{children}</>
}
```

**API Client Update:**
```typescript
// frontend/src/lib/api/client.ts — key changes
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // CRITICAL: sends httpOnly cookies
})

// Remove old Authorization header logic
// Add 401 interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      try {
        await apiClient.post('/auth/refresh')
        return apiClient(error.config) // retry original request
      } catch {
        // Refresh failed — redirect to login
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

### Existing Code to Modify

**Backend files to modify:**
| File | Change | Details |
|------|--------|---------|
| `api/auth.py` | EXTEND | Add `require_admin()`, `require_learner()`, `get_current_learner()` |
| `api/routers/notebooks.py` | MODIFY | Add `Depends(require_admin)` or `Depends(get_current_user)` to all endpoints |
| `api/routers/sources.py` | MODIFY | Add auth dependencies to all endpoints |
| `api/routers/chat.py` | MODIFY | Add `Depends(get_current_user)` |
| `api/routers/source_chat.py` | MODIFY | Add `Depends(get_current_user)` |
| `api/routers/notes.py` | MODIFY | Add auth dependencies |
| `api/routers/search.py` | MODIFY | Add `Depends(get_current_user)` |
| `api/routers/artifacts.py` | MODIFY | Add `Depends(get_current_user)` |
| `api/routers/quizzes.py` | MODIFY | Add auth dependencies |
| `api/routers/podcasts.py` | MODIFY | Add auth dependencies |
| `api/routers/models.py` | MODIFY | Add `Depends(require_admin)` |
| `api/routers/settings.py` | MODIFY | Add `Depends(require_admin)` |
| `api/routers/transformations.py` | MODIFY | Add auth dependencies |

**Frontend files to modify:**
| File | Change | Details |
|------|--------|---------|
| `frontend/src/app/(dashboard)/` | RENAME | Rename to `(admin)` |
| `frontend/src/app/(dashboard)/layout.tsx` | MODIFY | Add admin role guard |
| `frontend/src/app/(auth)/login/page.tsx` | MODIFY | Username+password form, role redirect |
| `frontend/src/app/layout.tsx` | MODIFY | Add AuthProvider, role routing |
| `frontend/src/lib/stores/auth-store.ts` | MODIFY | Add user/role state, new login/logout flow |
| `frontend/src/lib/api/client.ts` | MODIFY | Cookie-based auth, 401/403 interceptors |

**Frontend files to create:**
| File | Type | Details |
|------|------|---------|
| `frontend/src/middleware.ts` | NEW | Lightweight cookie check, redirect to login |
| `frontend/src/components/providers/AuthProvider.tsx` | NEW | Auth state initialization, role routing |
| `frontend/src/app/(learner)/layout.tsx` | NEW | Learner role guard, minimal layout |
| `frontend/src/app/(learner)/modules/page.tsx` | NEW | Placeholder module selection page |

### Endpoint Protection Matrix

| Endpoint Pattern | Dependency | Rationale |
|-----------------|------------|-----------|
| `POST /auth/*` (login, register, refresh) | None (public) | Must be accessible without auth |
| `GET /auth/status`, `/health`, `/docs` | None (public) | System/documentation endpoints |
| `GET /auth/me` | `get_current_user` | Returns authenticated user info |
| `POST /auth/logout` | `get_current_user` | Must be authenticated to logout |
| `GET /notebooks`, `GET /sources`, etc. | `get_current_user` | Both roles can read content |
| `POST/PUT/DELETE /notebooks/*` | `require_admin` | Only admin creates/edits content |
| `POST/PUT/DELETE /sources/*` | `require_admin` | Only admin manages sources |
| `GET/POST /chat/*` | `get_current_user` | Both roles can chat (for now) |
| `GET /search` | `get_current_user` | Both roles can search |
| `GET /artifacts/*` | `get_current_user` | Both roles can view artifacts |
| `POST /quizzes/generate` | `require_admin` | Only admin generates quizzes |
| `GET /quizzes/*` | `get_current_user` | Both roles can view quizzes |
| `POST /podcasts/generate` | `require_admin` | Only admin generates podcasts |
| `GET /podcasts/*` | `get_current_user` | Both roles can view podcasts |
| `*/models/*`, `*/settings/*` | `require_admin` | Admin-only configuration |

### Previous Story (1.1) Context

Story 1.1 creates the foundation this story builds on:
- `get_current_user()` dependency in `api/auth.py`
- User domain model with `role` field in `open_notebook/domain/user.py`
- JWT tokens in httpOnly cookies (access + refresh)
- Auth router with login, register, refresh, logout, me endpoints
- User service with registration and authentication
- Migration 18 for user table with role field

**Important**: Story 1.1 references `python-jose` and `passlib`, but these libraries are deprecated as of 2025-2026. The developer implementing 1.1 may have used the recommended replacements instead:
- **PyJWT** (replaces python-jose) — `import jwt` instead of `from jose import jwt`
- **pwdlib + Argon2** (replaces passlib + bcrypt) — `from pwdlib import PasswordHash`

Before implementing 1.2, check what was actually installed in `pyproject.toml` and match the import style.

### Library Version Notes (Feb 2026)

| Library | Status | Notes |
|---------|--------|-------|
| python-jose | DEPRECATED | Unmaintained since 2021, security issues. Use PyJWT 2.11.0+ |
| passlib | DEPRECATED | Broken on Python 3.13+. Use pwdlib |
| jose (npm) | v6.1.3, ACTIVE | Edge Runtime compatible. Use for JWT in frontend if needed |
| PyJWT | v2.11.0, ACTIVE | Drop-in replacement for python-jose |
| pwdlib | ACTIVE | FastAPI-recommended passlib replacement |

### Anti-Patterns to Avoid

| DO NOT | DO INSTEAD |
|--------|-----------|
| Validate JWT signature in Next.js middleware | Only check cookie existence. Validate via `/auth/me` API call |
| Store user role in localStorage | Fetch from `/auth/me` on each page load. Zustand for session only |
| Create new middleware pattern per route group | Single `middleware.ts` at app root handles all routing |
| Add auth to individual routes manually | Use layout-level role guards in `(admin)` and `(learner)` layouts |
| Forget auth on even one endpoint | Systematically apply to ALL routers — use the protection matrix above |
| Use `except Exception` without logging | Always `logger.error()` before raising HTTPException |
| Import admin components in learner layout | Strict separation: `components/admin/` and `components/learner/` |
| Duplicate `company_id` extraction logic | Single `get_current_learner()` dependency is the only place |

### CORS Configuration Check

With cookie-based auth, CORS must allow credentials:
```python
# api/main.py — verify this is set
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # NOT "*" when using credentials
    allow_credentials=True,  # CRITICAL for httpOnly cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**WARNING**: `allow_origins=["*"]` does NOT work with `allow_credentials=True`. Must specify exact frontend origin. Check the current `api/main.py` CORS config and update if needed.

### Project Structure Notes

- Alignment with architecture: Route groups `(admin)` and `(learner)` match architecture decision for single Next.js app
- Frontend middleware.ts pattern follows Next.js 16 best practices (lightweight, no JWT validation)
- Auth dependency chain (get_current_user → require_admin/require_learner → get_current_learner) matches architecture's RBAC design
- No new database migrations needed — Story 1.1's User model already has the `role` field

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Role-Based Access Control]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Strategy Decision — Route Groups]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries — API Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns — Auth Flow]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns — Structure Patterns]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md — Two independent frontends]
- [Source: _bmad-output/implementation-artifacts/1-1-user-registration-and-login-backend.md — Previous story context]
- [Source: api/auth.py — Current PasswordAuthMiddleware to be replaced by 1.1]
- [Source: frontend/src/app/(dashboard)/layout.tsx — Current client-side auth guard pattern]
- [Source: frontend/src/lib/stores/auth-store.ts — Current Zustand auth store to extend]
- [Source: frontend/src/lib/api/client.ts — Current API client to update]
- [Source: api/main.py — CORS middleware configuration to verify]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
