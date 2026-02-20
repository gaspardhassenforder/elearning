"""Surreal-commands integration for Open Notebook"""
import os

# Patch surreal-commands for SurrealDB Cloud database-level user auth.
# Cloud users require namespace+database in the signin payload.
# Three places in the library need fixing:
#   1. repository.db_connection  - async context manager (repo_query etc.)
#   2. worker.db_connection      - local binding via `from ..repository import db_connection`
#                                  patching the module attr above does NOT affect this binding
#   3. CommandService.db_auth    - built in __init__ without ns/db; used in submit/execute
_surreal_ns = os.environ.get("SURREAL_NAMESPACE")
if _surreal_ns:
    from contextlib import asynccontextmanager
    from surrealdb import AsyncSurreal
    import surreal_commands.repository as _sc_repo
    import surreal_commands.core.worker as _sc_worker
    import surreal_commands.core.service as _sc_service

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

    # Fix 1: repository module attribute (repo_query, repo_create, etc.)
    _sc_repo.db_connection = _patched_db_connection

    # Fix 2: worker's local binding — `from ..repository import db_connection`
    # creates a direct reference in worker's namespace; must patch that too
    _sc_worker.db_connection = _patched_db_connection

    # Fix 3: CommandService builds db_auth without namespace/database in __init__
    # and calls db.signin(self.db_auth) directly in submit_command / execute flows
    _orig_service_init = _sc_service.CommandService.__init__

    def _patched_service_init(self, *args, **kwargs):
        _orig_service_init(self, *args, **kwargs)
        self.db_auth["namespace"] = os.environ.get("SURREAL_NAMESPACE", "test")
        self.db_auth["database"] = os.environ.get("SURREAL_DATABASE", "test")

    _sc_service.CommandService.__init__ = _patched_service_init

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
