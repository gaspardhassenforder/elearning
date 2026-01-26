#!/usr/bin/env python3
"""
Clear the surreal-commands job queue (and optionally placeholder podcast artifacts).

Use this to wipe all pending/running command jobs (e.g. podcast generation backlog).
Requires .env (or SURREAL_* env vars) and SurrealDB to be reachable.

Usage:
  uv run python scripts/clear_command_queue.py              # clear command table only
  uv run python scripts/clear_command_queue.py --artifacts   # also remove placeholder podcast artifacts
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Ensure project root is on path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Clear the surreal-commands job queue")
    parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Also delete artifact rows that reference pending jobs (artifact_id starting with 'command:')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be deleted, do not run DELETE",
    )
    args = parser.parse_args()

    from open_notebook.database.repository import repo_query

    # 1. Clear command table (surreal-commands job queue)
    try:
        if args.dry_run:
            result = await repo_query("SELECT * FROM command")
            count = len(result) if isinstance(result, list) else 0
            print(f"[dry-run] Would DELETE {count} row(s) from table `command`")
        else:
            await repo_query("DELETE FROM command")
            print("Cleared table `command` (all job queue entries removed).")
    except Exception as e:
        if "Unknown table" in str(e) or "does not exist" in str(e).lower():
            print("Table `command` does not exist (no jobs ever queued). Nothing to clear.")
        else:
            raise

    # 2. Optionally remove placeholder podcast artifacts (artifact_id = command:xxx)
    if args.artifacts:
        # SurrealQL: match artifact_id starting with 'command:' (lexicographic range)
        query = (
            "DELETE FROM artifact WHERE artifact_type = 'podcast' "
            "AND artifact_id >= 'command:' AND artifact_id < 'command;'"
        )
        if args.dry_run:
            count_result = await repo_query(
                "SELECT * FROM artifact WHERE artifact_type = 'podcast' "
                "AND artifact_id >= 'command:' AND artifact_id < 'command;'"
            )
            count = len(count_result) if isinstance(count_result, list) else 0
            print(f"[dry-run] Would DELETE {count} placeholder podcast artifact(s)")
        else:
            await repo_query(query)
            print("Removed placeholder podcast artifacts (artifact_id starting with 'command:').")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
