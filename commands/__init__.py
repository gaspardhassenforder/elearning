"""Surreal-commands integration for Open Notebook"""
import os

# Always patch surreal-commands to support SurrealDB Cloud.
# Two problems are fixed here:
#
# 1. AUTH: Cloud database-level users require namespace+database in signin payload.
#    Three binding sites patched independently (see comments below).
#    Patch must be unconditional — a `if SURREAL_NAMESPACE:` guard causes the
#    entire block to be skipped when the env var is absent, leaving the original
#    broken functions in place (confirmed from Render deploy traceback).
#
# 2. LIVE QUERIES: surreal-commands worker uses db.live() to watch the command
#    table. LIVE queries require a WebSocket connection. SurrealDB Cloud URLs are
#    https:// which the surrealdb library treats as HTTP (AsyncHttpSurrealConnection),
#    which raises NotImplementedError for live(). The worker connection must use
#    wss:// (or ws:// for local). We auto-convert https→wss and http→ws here.
#    The API's own repository.py uses the same https URL without issues because
#    it never calls db.live().

from contextlib import asynccontextmanager
from surrealdb import AsyncSurreal
import surreal_commands.repository as _sc_repo
import surreal_commands.core.worker as _sc_worker
import surreal_commands.core.service as _sc_service


def _to_ws_url(url: str) -> str:
    """Convert https/http URL to wss/ws for WebSocket LIVE query support."""
    if url.startswith("https://"):
        base = url[8:].rstrip("/")
        if not base.endswith("/rpc"):
            base += "/rpc"
        return "wss://" + base
    if url.startswith("http://"):
        base = url[7:].rstrip("/")
        if not base.endswith("/rpc"):
            base += "/rpc"
        return "ws://" + base
    return url  # already ws:// or wss://


def _build_url(url=None, ws=False):
    raw = (
        url
        or os.environ.get("SURREAL_URL")
        or f"ws://{os.environ.get('SURREAL_ADDRESS', 'localhost')}:{os.environ.get('SURREAL_PORT', 8000)}/rpc"
    )
    return _to_ws_url(raw) if ws else raw


def _build_signin(user=None, password=None, namespace=None, database=None):
    ns = namespace or os.environ.get("SURREAL_NAMESPACE")
    db_name = database or os.environ.get("SURREAL_DATABASE")
    data = {
        "username": user or os.environ.get("SURREAL_USER", "test"),
        "password": password or os.environ.get("SURREAL_PASSWORD") or os.environ.get("SURREAL_PASS", "test"),
    }
    if ns:
        data["namespace"] = ns
    if db_name:
        data["database"] = db_name
    return data, ns, db_name


# Fix 1 & 2: repository helpers (HTTP ok, no LIVE queries)
@asynccontextmanager
async def _patched_db_connection(url=None, user=None, password=None, namespace=None, database=None):
    signin_data, ns, db_name = _build_signin(user, password, namespace, database)
    db_conn = AsyncSurreal(_build_url(url, ws=False))
    await db_conn.signin(signin_data)
    await db_conn.use(ns, db_name)
    try:
        yield db_conn
    finally:
        try:
            await db_conn.close()
        except Exception:
            pass


# Fix 1 & 2: worker LIVE query listener — must use WebSocket URL
@asynccontextmanager
async def _patched_db_connection_ws(url=None, user=None, password=None, namespace=None, database=None):
    signin_data, ns, db_name = _build_signin(user, password, namespace, database)
    db_conn = AsyncSurreal(_build_url(url, ws=True))
    await db_conn.signin(signin_data)
    await db_conn.use(ns, db_name)
    try:
        yield db_conn
    finally:
        try:
            await db_conn.close()
        except Exception:
            pass


# Patch 1: repository module attribute (repo_query, repo_create, etc.)
_sc_repo.db_connection = _patched_db_connection

# Patch 2: worker's local binding — `from ..repository import db_connection`
# creates a direct reference in worker's namespace; must patch separately.
# Uses WebSocket variant so db.live() works.
_sc_worker.db_connection = _patched_db_connection_ws

# Patch 3: CommandService.db_auth omits namespace/database (submit/execute paths)
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
