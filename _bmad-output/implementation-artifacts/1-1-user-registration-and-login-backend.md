# Story 1.1: User Registration & Login (Backend)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user (admin or learner)**,
I want to register an account and log in with my credentials,
So that I can securely access the platform.

## Acceptance Criteria

1. **Given** a visitor has no account **When** they submit a registration request with username, email, and password **Then** a new User record is created with a hashed password (bcrypt via passlib) **And** the user is assigned a default role of "learner"

2. **Given** a registered user **When** they submit valid credentials to `/auth/login` **Then** an access token (30min, JWT) and refresh token (7 days) are set as httpOnly cookies **And** the response includes the user's id, role, and company_id

3. **Given** a user with an expired access token **When** they call `/auth/refresh` with a valid refresh token **Then** a new access token is issued

4. **Given** any API request with an invalid or missing token **When** the request reaches a protected endpoint **Then** a 401 Unauthorized response is returned

## Tasks / Subtasks

- [x] Task 1: Add python-jose and passlib dependencies (AC: #1, #2)
  - [x] 1.1: Add `python-jose[cryptography]` and `passlib[bcrypt]` to pyproject.toml
  - [x] 1.2: Run `uv sync` to install dependencies
- [x] Task 2: Create User domain model (AC: #1)
  - [x] 2.1: Create `open_notebook/domain/user.py` with User class extending ObjectModel
  - [x] 2.2: Fields: id, username, email, password_hash, role (admin|learner), company_id, profile (dict), onboarding_completed (bool), created, updated
  - [x] 2.3: Add class methods: `get_by_username()`, `get_by_email()`
- [x] Task 3: Create database migration 18 for user table (AC: #1)
  - [x] 3.1: Create `open_notebook/database/migrations/18.surrealql`
  - [x] 3.2: Define user table with fields, indexes on username (unique) and email (unique)
  - [x] 3.3: Create `open_notebook/database/migrations/18_down.surrealql` for rollback
  - [x] 3.4: Register migration in AsyncMigrationManager
- [x] Task 4: Rewrite auth module with JWT (AC: #2, #3, #4)
  - [x] 4.1: Rewrite `api/auth.py` — replace PasswordAuthMiddleware with JWT-based authentication
  - [x] 4.2: Implement `create_access_token(user_id, role, company_id)` returning 30min JWT
  - [x] 4.3: Implement `create_refresh_token(user_id)` returning 7-day JWT
  - [x] 4.4: Implement `verify_token(token)` decoding and validating JWT
  - [x] 4.5: Implement `get_current_user()` FastAPI dependency that extracts user from httpOnly cookie
  - [x] 4.6: Set JWT secret via `JWT_SECRET_KEY` environment variable (require on startup)
- [x] Task 5: Create auth router endpoints (AC: #1, #2, #3, #4)
  - [x] 5.1: Rewrite `api/routers/auth.py` with new endpoints
  - [x] 5.2: `POST /auth/register` — validate input, hash password, create User, return user info (no tokens yet, admin must approve or auto-login)
  - [x] 5.3: `POST /auth/login` — validate credentials, set httpOnly cookies (access + refresh), return user info
  - [x] 5.4: `POST /auth/refresh` — validate refresh cookie, issue new access token cookie
  - [x] 5.5: `POST /auth/logout` — clear httpOnly cookies
  - [x] 5.6: `GET /auth/me` — return current user info (requires valid access token)
  - [x] 5.7: Keep `GET /auth/status` endpoint for backward compatibility (returns auth_enabled: true always)
- [x] Task 6: Create user service (AC: #1, #2)
  - [x] 6.1: Create `api/user_service.py`
  - [x] 6.2: Implement `register_user(username, email, password)` — hash password, create User record
  - [x] 6.3: Implement `authenticate_user(username, password)` — verify credentials, return User
  - [x] 6.4: Implement `get_user_by_id(user_id)` — fetch user from database
- [x] Task 7: Add Pydantic models for auth (AC: #1, #2)
  - [x] 7.1: Add to `api/models.py`: `UserCreate`, `UserLogin`, `UserResponse`, `TokenResponse`, `AuthStatusResponse`
- [x] Task 8: Update main.py middleware (AC: #4)
  - [x] 8.1: Remove PasswordAuthMiddleware from middleware stack
  - [x] 8.2: Keep CORS middleware and HTTP exception handler
  - [x] 8.3: Auth is now per-endpoint via `get_current_user()` dependency, not global middleware
  - [x] 8.4: Update excluded paths: `/auth/login`, `/auth/register`, `/auth/status`, `/health`, `/docs`, `/openapi.json`, `/redoc` remain public
- [x] Task 9: Seed initial admin user (AC: #1)
  - [x] 9.1: Add startup logic or CLI command to create default admin user if no users exist
  - [x] 9.2: Default admin credentials from env vars: `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_EMAIL`
- [x] Task 10: Write tests (AC: #1, #2, #3, #4)
  - [x] 10.1: Create `tests/test_auth.py`
  - [x] 10.2: Test user registration (happy path + duplicate username/email)
  - [x] 10.3: Test login (happy path + wrong password + nonexistent user)
  - [x] 10.4: Test token refresh (valid + expired + invalid)
  - [x] 10.5: Test protected endpoint access (valid token + expired + missing)
  - [x] 10.6: Test logout clears cookies

## Dev Notes

### Architecture Decisions

- **Replace PasswordAuthMiddleware entirely.** The current auth is a simple shared password in an env var. The new system uses per-user JWT authentication.
- **httpOnly cookies, NOT localStorage.** Tokens go in httpOnly cookies for XSS protection. The frontend does NOT store tokens in localStorage or Zustand for auth — cookies are sent automatically by the browser.
- **Dependency injection, NOT global middleware.** Auth is enforced per-endpoint via FastAPI `Depends(get_current_user)`, not as a middleware layer. This allows fine-grained control (public vs admin vs learner endpoints).
- **Backend layering MANDATORY:** Router → Service → Domain → Database. The auth router calls user_service, which calls User domain model, which calls SurrealDB.

### Critical Implementation Details

**JWT Token Structure:**
```python
# Access token payload (30min expiry)
{
    "sub": "user:abc123",       # SurrealDB user record ID
    "role": "learner",          # "admin" or "learner"
    "company_id": "company:xyz", # null for admin
    "exp": 1738694400,          # 30 min from issuance
    "type": "access"
}

# Refresh token payload (7 day expiry)
{
    "sub": "user:abc123",
    "exp": 1739299200,
    "type": "refresh"
}
```

**Cookie Configuration:**
```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,         # HTTPS only in production
    samesite="lax",
    max_age=1800,        # 30 minutes
    path="/"
)
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="lax",
    max_age=604800,      # 7 days
    path="/auth/refresh"  # Only sent to refresh endpoint
)
```

**Password Hashing:**
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Hash: pwd_context.hash(password)
# Verify: pwd_context.verify(password, hashed_password)
```

**FastAPI Dependency:**
```python
from fastapi import Depends, Request, HTTPException
from jose import jwt, JWTError

async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Existing Code Patterns to Follow

**Domain Model Pattern** (from `open_notebook/domain/notebook.py`):
- Extend `ObjectModel` base class from `open_notebook/domain/base.py`
- Use `table_name` class attribute for SurrealDB table
- Use `save()`, `get()`, `get_all()`, `delete()` inherited methods
- All methods are `async def`

**Migration Pattern** (from `open_notebook/database/migrations/`):
- SurrealQL files numbered sequentially: `18.surrealql`
- Register in `AsyncMigrationManager` (check `open_notebook/database/repo.py` for how existing migrations 1-17 are loaded)
- Each migration file contains `DEFINE TABLE`, `DEFINE FIELD`, `DEFINE INDEX` statements

**Router Pattern** (from `api/routers/notebooks.py`):
- Use `APIRouter(prefix="/auth", tags=["auth"])`
- Register in `api/main.py` with `app.include_router()`
- Pydantic models for request/response in `api/models.py`
- `logger.error()` before every `HTTPException` raise

**Pydantic Model Naming** (from `api/models.py`):
- `{Entity}{Purpose}` pattern: `UserCreate`, `UserLogin`, `UserResponse`
- `snake_case` field names

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | YES | none | Secret key for JWT signing (HS256). Must be set. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | no | 30 | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | no | 7 | Refresh token lifetime |
| `DEFAULT_ADMIN_USERNAME` | no | admin | Initial admin username |
| `DEFAULT_ADMIN_PASSWORD` | no | changeme | Initial admin password |
| `DEFAULT_ADMIN_EMAIL` | no | admin@localhost | Initial admin email |

### Migration 18 SurrealQL Reference

```sql
DEFINE TABLE user SCHEMAFULL;

DEFINE FIELD username ON user TYPE string ASSERT string::len($value) >= 3;
DEFINE FIELD email ON user TYPE string;
DEFINE FIELD password_hash ON user TYPE string;
DEFINE FIELD role ON user TYPE string DEFAULT 'learner' ASSERT $value IN ['admin', 'learner'];
DEFINE FIELD company_id ON user TYPE option<record<company>>;
DEFINE FIELD profile ON user FLEXIBLE TYPE option<object>;
DEFINE FIELD onboarding_completed ON user TYPE bool DEFAULT false;
DEFINE FIELD created ON user TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON user TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_user_username ON user FIELDS username UNIQUE;
DEFINE INDEX idx_user_email ON user FIELDS email UNIQUE;
DEFINE INDEX idx_user_company ON user FIELDS company_id;
DEFINE INDEX idx_user_role ON user FIELDS role;
```

### Backward Compatibility

- **`OPEN_NOTEBOOK_PASSWORD` env var**: The old password auth mechanism should still work during migration. If `OPEN_NOTEBOOK_PASSWORD` is set AND no JWT_SECRET_KEY is set, fall back to old behavior. Once JWT is configured, old auth is disabled.
- **`/auth/status` endpoint**: Keep it. Return `{"auth_enabled": true}` always when JWT is active.
- **Existing API endpoints**: After removing PasswordAuthMiddleware, existing endpoints become unprotected UNTIL `Depends(get_current_user)` is added. Story 1.2 will add role-based protection to all endpoints. For this story, add `get_current_user` dependency to the existing notebook/source/note/chat endpoints to maintain security.

### Anti-Patterns to Avoid

| DO NOT | DO INSTEAD |
|--------|-----------|
| Store tokens in localStorage | Use httpOnly cookies |
| Put auth logic in router | Router → user_service → User model |
| Use `except Exception` silently | `logger.error()` then raise HTTPException |
| Create sync functions | All functions `async def` |
| Hardcode JWT secret | Read from `JWT_SECRET_KEY` env var |
| Skip password validation | Require min 8 chars |
| Use camelCase in Python | Use snake_case everywhere |
| Import from frontend code | Backend is fully independent |

### Project Structure Notes

- **User model**: `open_notebook/domain/user.py` (NEW)
- **Auth rewrite**: `api/auth.py` (REWRITE)
- **Auth router**: `api/routers/auth.py` (REWRITE)
- **User service**: `api/user_service.py` (NEW)
- **Pydantic models**: `api/models.py` (EXTEND)
- **Migration**: `open_notebook/database/migrations/18.surrealql` (NEW)
- **Main app**: `api/main.py` (MODIFY — remove PasswordAuthMiddleware, register new router)
- **Tests**: `tests/test_auth.py` (NEW)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]
- [Source: api/auth.py — current PasswordAuthMiddleware implementation]
- [Source: api/routers/auth.py — current auth status endpoint]
- [Source: open_notebook/domain/base.py — ObjectModel base class pattern]
- [Source: open_notebook/database/repo.py — AsyncMigrationManager pattern]
- [Source: api/main.py — middleware stack and lifespan handler]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Resolved bcrypt/passlib compatibility issue by using bcrypt directly instead of passlib (bcrypt 5.0.0 incompatible with passlib 1.7.4)

### Completion Notes List

- Implemented full JWT-based authentication system replacing PasswordAuthMiddleware
- Created User domain model with SurrealDB persistence
- Added migration 18 for user table with unique indexes on username and email
- Implemented auth endpoints: register, login, refresh, logout, me, status
- Added router-level authentication to notebooks, sources, notes, chat, source_chat routers
- Created admin user seeding on startup when JWT is enabled and no users exist
- All 26 auth tests pass; 93/94 overall tests pass (1 pre-existing failure unrelated to auth)

### File List

**New Files:**
- open_notebook/domain/user.py
- open_notebook/database/migrations/18.surrealql
- open_notebook/database/migrations/18_down.surrealql
- api/user_service.py
- tests/test_auth.py

**Modified Files:**
- pyproject.toml (added python-jose, bcrypt dependencies)
- api/auth.py (complete rewrite with JWT)
- api/routers/auth.py (complete rewrite with new endpoints)
- api/models.py (added UserCreate, UserLogin, UserResponse, TokenResponse, AuthStatusResponse)
- api/main.py (removed PasswordAuthMiddleware, added admin seeding)
- api/routers/notebooks.py (added get_current_user dependency)
- api/routers/sources.py (added get_current_user dependency)
- api/routers/notes.py (added get_current_user dependency)
- api/routers/chat.py (added get_current_user dependency)
- api/routers/source_chat.py (added get_current_user dependency)
- open_notebook/database/async_migrate.py (registered migration 18)

## Change Log

- 2026-02-05: Implemented JWT authentication system (Story 1.1) - User registration, login, token refresh, logout, protected endpoints
