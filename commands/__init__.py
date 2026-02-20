"""Surreal-commands integration for Open Notebook"""
import os

# Always patch surreal-commands to support SurrealDB Cloud database-level users.
# Cloud users require namespace+database in the signin payload; the library omits them.
# The patch mirrors the logic in open_notebook/database/repository.py (commit eeb0fab).
#
# Three binding sites must be patched independently:
#   1. surreal_commands.repository.db_connection  — used by repo helpers
#   2. surreal_commands.core.worker.db_connection — LOCAL binding from
#      `from ..repository import db_connection`; patching the module attr above
#      does NOT update this reference, so it must be patched separately
#   3. CommandService.db_auth — built in __init__ without ns/db; used in
#      submit_command / execute flows
#
# NOTE: The patch must be unconditional (no `if SURREAL_NAMESPACE:` guard).
# If the guard is used and the env var is not set, the entire block is skipped
# and the original broken functions run unchanged — the exact failure mode seen
# in Render deploy logs where the original library code at repo/__init__.py:47
# appeared in the traceback instead of our patched version.

from contextlib import asynccontextmanager
from surrealdb import AsyncSurreal
import surreal_commands.repository as _sc_repo
import surreal_commands.core.worker as _sc_worker
import surreal_commands.core.service as _sc_service


@asynccontextmanager
async def _patched_db_connection(url=None, user=None, password=None, namespace=None, database=None):
    ns = namespace or os.environ.get("SURREAL_NAMESPACE")
    db_name = database or os.environ.get("SURREAL_DATABASE")
    surreal_url = (
        url
        or os.environ.get("SURREAL_URL")
        or f"ws://{os.environ.get('SURREAL_ADDRESS', 'localhost')}:{os.environ.get('SURREAL_PORT', 8000)}/rpc"
    )
    db_conn = AsyncSurreal(surreal_url)
    signin_data = {
        "username": user or os.environ.get("SURREAL_USER", "test"),
        "password": password or os.environ.get("SURREAL_PASSWORD") or os.environ.get("SURREAL_PASS", "test"),
    }
    # Only include namespace/database when set — mirrors open_notebook/database/repository.py
    if ns:
        signin_data["namespace"] = ns
    if db_name:
        signin_data["database"] = db_name
    await db_conn.signin(signin_data)
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
# creates a direct reference in worker's namespace that must be patched separately
_sc_worker.db_connection = _patched_db_connection

# Fix 3: CommandService builds db_auth = {username, password} without ns/db
# and calls db.signin(self.db_auth) directly in submit/execute paths
_orig_service_init = _sc_service.CommandService.__init__


def _patched_service_init(self, *args, **kwargs):
    _orig_service_init(self, *args, **kwargs)
    ns = os.environ.get("SURREAL_NAMESPACE")
    db_name = os.environ.get("SURREAL_DATABASE")
    if ns:
        self.db_auth["namespace"] = ns
    if db_name:
        self.db_auth["database"] = db_name


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
