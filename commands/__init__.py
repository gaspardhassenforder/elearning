"""Surreal-commands integration for Open Notebook"""
import os

# Patch surreal-commands db_connection to include namespace/database in signin.
# Required for SurrealDB Cloud database-level users.
# Our repository.py was fixed in commit eeb0fab; this applies the same fix to
# the surreal-commands library which doesn't include ns/db in its signin call.
_surreal_ns = os.environ.get("SURREAL_NAMESPACE")
if _surreal_ns:
    from contextlib import asynccontextmanager
    from surrealdb import AsyncSurreal
    import surreal_commands.repository as _sc_repo

    @asynccontextmanager
    async def _patched_db_connection(url=None, user=None, password=None, namespace=None, database=None):
        ns = namespace or os.environ.get("SURREAL_NAMESPACE", "test")
        db_name = database or os.environ.get("SURREAL_DATABASE", "test")
        surreal_url = (
            url
            or os.environ.get("SURREAL_URL")
            or f"ws://{os.environ.get('SURREAL_ADDRESS', 'localhost')}:{os.environ.get('SURREAL_PORT', 8000)}/rpc"
        )
        db_conn = AsyncSurreal(surreal_url)
        await db_conn.signin({
            "username": user or os.environ.get("SURREAL_USER", "test"),
            "password": password or os.environ.get("SURREAL_PASSWORD") or os.environ.get("SURREAL_PASS", "test"),
            "namespace": ns,
            "database": db_name,
        })
        await db_conn.use(ns, db_name)
        try:
            yield db_conn
        finally:
            try:
                await db_conn.close()
            except Exception:
                pass

    _sc_repo.db_connection = _patched_db_connection

from .embedding_commands import embed_single_item_command, rebuild_embeddings_command
from .example_commands import analyze_data_command, process_text_command
from .podcast_commands import generate_podcast_command
from .source_commands import process_source_command

__all__ = [
    "embed_single_item_command",
    "generate_podcast_command",
    "process_source_command",
    "process_text_command",
    "analyze_data_command",
    "rebuild_embeddings_command",
]
