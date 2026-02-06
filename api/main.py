# Load environment variables
from dotenv import load_dotenv

load_dotenv()

import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routers import (
    admin_chat,
    artifacts,
    auth,
    chat,
    companies,
    config,
    context,
    debug,
    embedding,
    embedding_rebuild,
    episode_profiles,
    insights,
    learner,
    learner_chat,
    learning_objectives,
    models,
    module_assignments,
    module_prompts,
    notebooks,
    notes,
    podcasts,
    quizzes,
    search,
    settings,
    source_chat,
    sources,
    speaker_profiles,
    transformations,
    users,
)
from api.routers import commands as commands_router
from open_notebook.database.async_migrate import AsyncMigrationManager

# Import commands to register them in the API process
try:
    logger.info("Commands imported in API process")
except Exception as e:
    logger.error(f"Failed to import commands in API process: {e}")


async def seed_admin_user():
    """Create default admin user if no users exist."""
    from api.auth import hash_password, is_jwt_enabled
    from open_notebook.domain.user import User

    if not is_jwt_enabled():
        logger.info("JWT not enabled, skipping admin user seeding")
        return

    # Check if any users exist
    existing_users = await User.get_all()
    if existing_users:
        logger.info(f"Users already exist ({len(existing_users)}), skipping admin seeding")
        return

    # Create default admin user
    admin_username = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "changeme")
    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@localhost")

    admin = User(
        username=admin_username,
        email=admin_email,
        password_hash=hash_password(admin_password),
        role="admin",
    )
    await admin.save()
    logger.success(f"Default admin user created: {admin_username}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    Runs database migrations automatically on startup.
    """
    # Startup: Run database migrations
    logger.info("Starting API initialization...")

    try:
        migration_manager = AsyncMigrationManager()
        current_version = await migration_manager.get_current_version()
        logger.info(f"Current database version: {current_version}")

        if await migration_manager.needs_migration():
            logger.warning("Database migrations are pending. Running migrations...")
            await migration_manager.run_migration_up()
            new_version = await migration_manager.get_current_version()
            logger.success(
                f"Migrations completed successfully. Database is now at version {new_version}"
            )
        else:
            logger.info(
                "Database is already at the latest version. No migrations needed."
            )
    except Exception as e:
        logger.error(f"CRITICAL: Database migration failed: {str(e)}")
        logger.exception(e)
        # Fail fast - don't start the API with an outdated database schema
        raise RuntimeError(f"Failed to run database migrations: {str(e)}") from e

    # Seed default admin user if no users exist
    try:
        await seed_admin_user()
    except Exception as e:
        logger.error(f"Failed to seed admin user: {str(e)}")
        # Non-fatal - continue startup even if seeding fails

    logger.success("API initialization completed successfully")

    # Yield control to the application
    yield

    # Shutdown: cleanup if needed
    logger.info("API shutdown complete")


app = FastAPI(
    title="Open Notebook API",
    description="API for Open Notebook - Research Assistant",
    version="0.2.2",
    lifespan=lifespan,
)

# Auth is now per-endpoint via Depends(get_current_user), not global middleware.
# Public endpoints: /auth/login, /auth/register, /auth/status, /health, /docs, /openapi.json, /redoc

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import notification service
from open_notebook.observability.notification_service import (
    get_notification_service,
    NotificationPayload,
)
from open_notebook.observability.request_context import (
    get_request_context,
    context_buffer as context_buffer_var,
)
import traceback


async def send_error_notification(
    error_type: str,
    error_summary: str,
    severity: str = "ERROR",
    exc_info: Optional[Exception] = None,
):
    """
    Helper function to send admin error notification.

    Extracts request context and sends notification via configured backend.
    Gracefully handles notification failures (never raises).
    """
    try:
        # Get request context from contextvars
        ctx = get_request_context()
        buffer = context_buffer_var.get()

        # Extract context snippet (last 3 operations)
        context_snippet = []
        if buffer:
            recent_ops = buffer.peek()[-3:]  # Last 3 operations
            context_snippet = [
                f"{op.get('type', 'unknown')}: {op.get('details', {})}"
                for op in recent_ops
            ]

        # Extract stack trace preview if exception provided
        stack_trace_preview = None
        if exc_info:
            tb = "".join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
            stack_trace_preview = tb[:500]  # Truncate to 500 chars

        # Build notification payload
        payload = NotificationPayload(
            error_summary=error_summary[:200],  # Truncate to 200 chars
            error_type=error_type,
            severity=severity,
            request_id=ctx.get("request_id"),
            user_id=ctx.get("user_id"),
            company_id=ctx.get("company_id"),
            endpoint=ctx.get("endpoint"),
            timestamp=datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc),
            context_snippet=context_snippet,
            stack_trace_preview=stack_trace_preview,
        )

        # Send notification (async, non-blocking)
        service = get_notification_service()
        await service.notify(payload)

    except Exception as e:
        # Notification failure MUST NOT affect error handling
        logger.warning(f"Failed to send error notification: {e}")


# Custom exception handler to ensure CORS headers are included in error responses
# This helps when errors occur before the CORS middleware can process them
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom exception handler that ensures CORS headers are included in error responses.
    This is particularly important for 413 (Payload Too Large) errors during file uploads.

    Note: If a reverse proxy (nginx, traefik) returns 413 before the request reaches
    FastAPI, this handler won't be called. In that case, configure your reverse proxy
    to add CORS headers to error responses.
    """
    # Send admin notification for 5xx errors (server errors)
    if exc.status_code >= 500:
        await send_error_notification(
            error_type=f"HTTP{exc.status_code}",
            error_summary=str(exc.detail),
            severity="ERROR",
        )

    # Get the origin from the request
    origin = request.headers.get("origin", "*")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            **(exc.headers or {}), "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# Add unhandled exception handler for all other exceptions
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.

    Logs the exception, sends admin notification, and returns 500 error response.
    """
    # Log exception
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)

    # Send admin notification
    await send_error_notification(
        error_type=type(exc).__name__,
        error_summary=str(exc),
        severity="ERROR",
        exc_info=exc,
    )

    # Return error response
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(notebooks.router, prefix="/api", tags=["notebooks"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(embedding.router, prefix="/api", tags=["embedding"])
app.include_router(
    embedding_rebuild.router, prefix="/api/embeddings", tags=["embeddings"]
)
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(context.router, prefix="/api", tags=["context"])
app.include_router(sources.router, prefix="/api", tags=["sources"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(commands_router.router, prefix="/api", tags=["commands"])
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(episode_profiles.router, prefix="/api", tags=["episode-profiles"])
app.include_router(speaker_profiles.router, prefix="/api", tags=["speaker-profiles"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(source_chat.router, prefix="/api", tags=["source-chat"])
app.include_router(quizzes.router, prefix="/api", tags=["quizzes"])
app.include_router(artifacts.router, prefix="/api", tags=["artifacts"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(companies.router, prefix="/api", tags=["companies"])
app.include_router(module_assignments.router, prefix="/api", tags=["module-assignments"])
app.include_router(learner.router, prefix="/api", tags=["learner"])
app.include_router(learner_chat.router, prefix="/api", tags=["learner-chat"])
app.include_router(learning_objectives.router, prefix="/api", tags=["learning-objectives"])
app.include_router(learning_objectives.learner_router, prefix="/api", tags=["learner-objectives"])  # Story 4.4
app.include_router(module_prompts.router, prefix="/api", tags=["module-prompts"])
app.include_router(admin_chat.router, prefix="/api", tags=["admin-chat"])
app.include_router(debug.router, prefix="/api", tags=["debug"])


@app.get("/")
async def root():
    return {"message": "Open Notebook API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
