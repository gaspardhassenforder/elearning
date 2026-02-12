"""LangGraph checkpoint cleanup utilities for user data deletion."""

import sqlite3
from typing import List

from loguru import logger

from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE


def delete_user_checkpoints(user_id: str) -> int:
    """
    Delete all LangGraph conversation checkpoints for a user.

    Thread ID pattern: user:{user_id}:notebook:{notebook_id}

    Args:
        user_id: User record ID (e.g., "user:alice")

    Returns:
        Number of checkpoint threads deleted

    Note:
        Gracefully handles SQLite connection errors (logs warning, returns 0)
    """
    try:
        conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)
        cursor = conn.cursor()

        # LangGraph stores checkpoints in 'checkpoints' table with thread_id column
        # Thread pattern: "user:{user_id}:notebook:{notebook_id}"
        thread_pattern = f"{user_id}:%"

        # Query matching threads
        cursor.execute(
            "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?",
            (thread_pattern,),
        )
        threads = cursor.fetchall()
        thread_count = len(threads)

        # Delete matching checkpoints
        cursor.execute(
            "DELETE FROM checkpoints WHERE thread_id LIKE ?",
            (thread_pattern,),
        )

        conn.commit()
        conn.close()

        logger.info(f"Deleted {thread_count} checkpoint threads for user {user_id}")
        return thread_count

    except sqlite3.Error as e:
        logger.warning("Failed to delete checkpoints for {}: {}", user_id, str(e))
        return 0


def list_user_checkpoint_threads(user_id: str) -> List[str]:
    """
    List all checkpoint thread IDs for a user (for debugging).

    Args:
        user_id: User record ID

    Returns:
        List of thread_id strings
    """
    try:
        conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)
        cursor = conn.cursor()

        thread_pattern = f"{user_id}:%"
        cursor.execute(
            "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?",
            (thread_pattern,),
        )
        threads = [row[0] for row in cursor.fetchall()]

        conn.close()
        return threads

    except sqlite3.Error as e:
        logger.error("Failed to list checkpoints for {}: {}", user_id, str(e))
        return []
