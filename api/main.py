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

# Configure structured logging (Story 7.2)
# Import early to ensure logging is configured before any log statements
from open_notebook.observability import structured_logger  # noqa: F401

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
    logs,
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

# Add Request Logging Middleware (Story 7.2)
# IMPORTANT: Must be registered BEFORE CORS middleware to ensure context is available
from api.middleware.request_logging import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register exception handlers with structured logging (Story 7.2)
# These handlers implement AC1, AC4, and AC5 requirements
from api.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler as structured_unhandled_handler,
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, structured_unhandled_handler)


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
app.include_router(logs.router, prefix="/api", tags=["logs"])


@app.get("/")
async def root():
    return {"message": "Open Notebook API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
