"""Unit tests for LangGraph checkpoint cleanup utilities."""

import os
import sqlite3
import tempfile

import pytest

from open_notebook.observability.checkpoint_cleanup import (
    delete_user_checkpoints,
    list_user_checkpoint_threads,
)


@pytest.fixture
def temp_checkpoint_db():
    """Create temporary SQLite checkpoint database for testing."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)

    # Create checkpoints table schema (matches LangGraph structure)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE checkpoints (
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
    conn.commit()
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


@pytest.fixture
def checkpoint_db_with_data(temp_checkpoint_db, monkeypatch):
    """Create checkpoint DB with sample user data."""
    # Patch LANGGRAPH_CHECKPOINT_FILE to use temp DB
    import open_notebook.observability.checkpoint_cleanup as checkpoint_module

    monkeypatch.setattr(
        checkpoint_module, "LANGGRAPH_CHECKPOINT_FILE", temp_checkpoint_db
    )

    # Insert sample checkpoint data
    conn = sqlite3.connect(temp_checkpoint_db)
    cursor = conn.cursor()

    # User alice has 2 checkpoint threads
    cursor.execute(
        """
        INSERT INTO checkpoints (thread_id, checkpoint_id, checkpoint, metadata)
        VALUES (?, ?, ?, ?)
    """,
        ("user:alice:notebook:nb1", "chk1", b"data", b"meta"),
    )
    cursor.execute(
        """
        INSERT INTO checkpoints (thread_id, checkpoint_id, checkpoint, metadata)
        VALUES (?, ?, ?, ?)
    """,
        ("user:alice:notebook:nb2", "chk2", b"data", b"meta"),
    )

    # User bob has 1 checkpoint thread
    cursor.execute(
        """
        INSERT INTO checkpoints (thread_id, checkpoint_id, checkpoint, metadata)
        VALUES (?, ?, ?, ?)
    """,
        ("user:bob:notebook:nb1", "chk3", b"data", b"meta"),
    )

    conn.commit()
    conn.close()

    return temp_checkpoint_db


class TestDeleteUserCheckpoints:
    """Test delete_user_checkpoints function."""

    def test_delete_user_checkpoints_removes_matching_threads(
        self, checkpoint_db_with_data
    ):
        """delete_user_checkpoints removes threads matching user_id pattern."""
        # Act: Delete alice's checkpoints
        deleted_count = delete_user_checkpoints("user:alice")

        # Assert: 2 threads deleted
        assert deleted_count == 2

        # Verify: Only bob's checkpoint remains
        conn = sqlite3.connect(checkpoint_db_with_data)
        cursor = conn.cursor()
        cursor.execute("SELECT thread_id FROM checkpoints")
        remaining = cursor.fetchall()
        conn.close()

        assert len(remaining) == 1
        assert remaining[0][0] == "user:bob:notebook:nb1"

    def test_delete_user_checkpoints_returns_zero_for_no_matches(
        self, checkpoint_db_with_data
    ):
        """delete_user_checkpoints returns 0 when no checkpoints match."""
        # Act: Delete checkpoints for user with no data
        deleted_count = delete_user_checkpoints("user:charlie")

        # Assert
        assert deleted_count == 0

    def test_delete_user_checkpoints_handles_sqlite_error_gracefully(
        self, monkeypatch
    ):
        """delete_user_checkpoints returns 0 on SQLite connection error."""
        # Arrange: Patch to use invalid DB path
        import open_notebook.observability.checkpoint_cleanup as checkpoint_module

        monkeypatch.setattr(
            checkpoint_module,
            "LANGGRAPH_CHECKPOINT_FILE",
            "/invalid/path/to/db.sqlite",
        )

        # Act: Should not raise exception
        deleted_count = delete_user_checkpoints("user:alice")

        # Assert: Returns 0 gracefully
        assert deleted_count == 0


class TestListUserCheckpointThreads:
    """Test list_user_checkpoint_threads function."""

    def test_list_user_checkpoint_threads_returns_thread_ids(
        self, checkpoint_db_with_data
    ):
        """list_user_checkpoint_threads returns list of thread IDs."""
        # Act
        threads = list_user_checkpoint_threads("user:alice")

        # Assert
        assert len(threads) == 2
        assert "user:alice:notebook:nb1" in threads
        assert "user:alice:notebook:nb2" in threads

    def test_list_user_checkpoint_threads_returns_empty_for_no_matches(
        self, checkpoint_db_with_data
    ):
        """list_user_checkpoint_threads returns empty list when no matches."""
        # Act
        threads = list_user_checkpoint_threads("user:charlie")

        # Assert
        assert threads == []

    def test_list_user_checkpoint_threads_handles_sqlite_error(self, monkeypatch):
        """list_user_checkpoint_threads returns empty list on SQLite error."""
        # Arrange: Patch to use invalid DB path
        import open_notebook.observability.checkpoint_cleanup as checkpoint_module

        monkeypatch.setattr(
            checkpoint_module,
            "LANGGRAPH_CHECKPOINT_FILE",
            "/invalid/path/to/db.sqlite",
        )

        # Act
        threads = list_user_checkpoint_threads("user:alice")

        # Assert
        assert threads == []
