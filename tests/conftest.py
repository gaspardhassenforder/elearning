"""
Pytest configuration file.

This file ensures that the project root is in the Python path,
allowing tests to import from the api and open_notebook modules.
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure password auth and JWT auth are disabled for tests BEFORE any imports
# Set to empty string instead of deleting to prevent it from being reloaded
os.environ["OPEN_NOTEBOOK_PASSWORD"] = ""
os.environ["JWT_SECRET_KEY"] = ""

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
async def test_user_with_data():
    """Create test user with associated data for cascade deletion testing."""
    from open_notebook.database.repository import repo_create, repo_query
    from open_notebook.domain.user import User

    # Create test user
    user_data = {
        "username": "test_user_cascade",
        "email": "cascade@test.com",
        "password_hash": "hashed_password",
        "role": "learner",
        "company_id": "company:test",
    }
    user_record = await repo_create("user", user_data)
    user = User(**user_record)

    # Create associated data: 2 progress records
    await repo_create(
        "learner_objective_progress",
        {
            "user_id": user.id,
            "objective_id": "objective:1",
            "status": "completed",
            "completed_via": "chat",
        },
    )
    await repo_create(
        "learner_objective_progress",
        {
            "user_id": user.id,
            "objective_id": "objective:2",
            "status": "in_progress",
            "completed_via": None,
        },
    )

    # Create 1 quiz
    await repo_create(
        "quiz",
        {"created_by": user.id, "title": "Test Quiz", "questions": []},
    )

    # Create 1 note
    await repo_create(
        "note",
        {"user_id": user.id, "content": "Test note", "notebook_id": "notebook:test"},
    )

    # Create checkpoint in SQLite
    from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE

    conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)
    cursor = conn.cursor()

    # Ensure checkpoints table exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type TEXT,
            checkpoint BLOB,
            metadata BLOB,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        )
    """
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_id, checkpoint, metadata)
        VALUES (?, ?, ?, ?)
    """,
        (f"{user.id}:notebook:test", "chk1", b"test_data", b"test_meta"),
    )
    conn.commit()
    conn.close()

    yield user

    # Cleanup: Delete any remaining data
    try:
        await repo_query(
            "DELETE learner_objective_progress WHERE user_id = $uid", {"uid": user.id}
        )
        await repo_query("DELETE quiz WHERE created_by = $uid", {"uid": user.id})
        await repo_query("DELETE note WHERE user_id = $uid", {"uid": user.id})
        existing_user = await User.get(user.id)
        if existing_user:
            await existing_user.delete()

        # Cleanup checkpoint
        conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM checkpoints WHERE thread_id LIKE ?", (f"{user.id}:%",)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Cleanup best effort


@pytest.fixture
async def test_user_no_checkpoints():
    """Create test user without checkpoints (for testing checkpoint failure scenarios)."""
    from open_notebook.database.repository import repo_create, repo_query
    from open_notebook.domain.user import User

    # Create test user
    user_data = {
        "username": "test_user_no_cp",
        "email": "nocp@test.com",
        "password_hash": "hashed_password",
        "role": "learner",
        "company_id": "company:test",
    }
    user_record = await repo_create("user", user_data)
    user = User(**user_record)

    yield user

    # Cleanup
    try:
        existing_user = await User.get(user.id)
        if existing_user:
            await existing_user.delete()
    except Exception:
        pass
