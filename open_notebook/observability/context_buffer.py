"""
Rolling context buffer for request operation history.

This module provides a fixed-size buffer that tracks operations during a request,
automatically evicting oldest operations when the buffer is full.
"""

from collections import deque
from datetime import UTC, datetime
from typing import Any, Dict, List


class RollingContextBuffer:
    """
    Thread-safe rolling buffer for request context operations.

    Stores the last N operations in memory, flushes on error.
    Uses collections.deque with maxlen for automatic eviction of oldest entries.

    Attributes:
        buffer: Deque of operation dictionaries
        max_size: Maximum number of operations to store
    """

    def __init__(self, max_size: int = 50):
        """
        Initialize rolling buffer.

        Args:
            max_size: Maximum operations to store (default: 50)
        """
        self.buffer: deque = deque(maxlen=max_size)
        self.max_size = max_size

    def append(self, operation: Dict[str, Any]):
        """
        Add operation to buffer (auto-evicts oldest if full).

        Args:
            operation: Dictionary containing operation details
                       (type, details, timestamp, duration_ms, etc.)
        """
        self.buffer.append(
            {
                **operation,
                "buffer_position": len(self.buffer),
                "timestamp": operation.get("timestamp", datetime.now(UTC).isoformat()),
            }
        )

    def flush(self) -> List[Dict[str, Any]]:
        """
        Return all operations and clear buffer.

        Returns:
            List of operation dictionaries in chronological order

        Note:
            This is typically called on error to include full context in logs.
        """
        operations = list(self.buffer)
        self.buffer.clear()
        return operations

    def clear(self):
        """
        Clear buffer without returning (for successful requests).

        Note:
            This prevents memory accumulation for successful requests
            where we don't need to preserve operation history.
        """
        self.buffer.clear()

    def peek(self) -> List[Dict[str, Any]]:
        """
        View buffer without clearing (for debugging).

        Returns:
            List of operation dictionaries currently in buffer
        """
        return list(self.buffer)

    def __len__(self) -> int:
        """Return current buffer size."""
        return len(self.buffer)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"RollingContextBuffer(size={len(self.buffer)}/{self.max_size})"
