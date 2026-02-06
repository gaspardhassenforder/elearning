"""
Tests for rolling context buffer.

Tests cover:
- Operation appending
- Auto-eviction when buffer is full
- Flush operation (return and clear)
- Clear operation (clear without return)
- Peek operation (view without clearing)
- Buffer overflow handling
"""

import pytest

from open_notebook.observability.context_buffer import RollingContextBuffer


class TestRollingContextBuffer:
    """Tests for RollingContextBuffer class."""

    def test_buffer_initialization(self):
        """Test buffer initializes with correct max_size."""
        buffer = RollingContextBuffer(max_size=10)

        assert buffer.max_size == 10
        assert len(buffer) == 0

    def test_buffer_appends_operations(self):
        """Test operations are appended to buffer."""
        buffer = RollingContextBuffer(max_size=5)

        buffer.append({"type": "db_query", "query": "SELECT *"})
        buffer.append({"type": "tool_invoke", "tool": "surface_doc"})

        assert len(buffer) == 2
        operations = buffer.peek()
        assert operations[0]["type"] == "db_query"
        assert operations[1]["type"] == "tool_invoke"

    def test_buffer_auto_evicts_oldest(self):
        """Test buffer evicts oldest when max_size reached."""
        buffer = RollingContextBuffer(max_size=3)

        for i in range(5):
            buffer.append({"type": "op", "index": i})

        operations = buffer.peek()
        assert len(operations) == 3
        # Oldest 2 (index 0, 1) should be evicted
        assert operations[0]["index"] == 2
        assert operations[1]["index"] == 3
        assert operations[2]["index"] == 4

    def test_buffer_flush_returns_and_clears(self):
        """Test flush returns all operations and clears buffer."""
        buffer = RollingContextBuffer(max_size=5)
        buffer.append({"type": "op1"})
        buffer.append({"type": "op2"})

        operations = buffer.flush()

        assert len(operations) == 2
        assert operations[0]["type"] == "op1"
        assert operations[1]["type"] == "op2"
        assert len(buffer) == 0  # Buffer cleared

    def test_buffer_clear_without_return(self):
        """Test clear discards buffer without returning."""
        buffer = RollingContextBuffer(max_size=5)
        buffer.append({"type": "op1"})
        buffer.append({"type": "op2"})

        buffer.clear()

        assert len(buffer) == 0

    def test_buffer_peek_without_clearing(self):
        """Test peek returns operations without clearing."""
        buffer = RollingContextBuffer(max_size=5)
        buffer.append({"type": "op1"})
        buffer.append({"type": "op2"})

        operations = buffer.peek()

        assert len(operations) == 2
        assert len(buffer) == 2  # Buffer not cleared

    def test_buffer_overflow_handling(self):
        """Test buffer handles > max_size gracefully."""
        buffer = RollingContextBuffer(max_size=50)

        for i in range(100):
            buffer.append({"type": "op", "index": i})

        assert len(buffer) == 50  # Only last 50
        operations = buffer.peek()
        assert operations[0]["index"] == 50  # First operation is index 50
        assert operations[-1]["index"] == 99  # Last operation is index 99

    def test_buffer_adds_position_and_timestamp(self):
        """Test buffer adds buffer_position to operations."""
        buffer = RollingContextBuffer(max_size=5)

        buffer.append({"type": "op1"})
        buffer.append({"type": "op2"})

        operations = buffer.peek()
        assert "buffer_position" in operations[0]
        assert "buffer_position" in operations[1]
        assert "timestamp" in operations[0]

    def test_buffer_repr(self):
        """Test buffer string representation."""
        buffer = RollingContextBuffer(max_size=10)
        buffer.append({"type": "op1"})
        buffer.append({"type": "op2"})

        repr_str = repr(buffer)

        assert "RollingContextBuffer" in repr_str
        assert "2/10" in repr_str

    def test_buffer_empty_flush(self):
        """Test flushing empty buffer returns empty list."""
        buffer = RollingContextBuffer(max_size=5)

        operations = buffer.flush()

        assert operations == []
        assert len(buffer) == 0

    def test_buffer_multiple_flush_calls(self):
        """Test multiple flush calls return empty after first."""
        buffer = RollingContextBuffer(max_size=5)
        buffer.append({"type": "op1"})

        first_flush = buffer.flush()
        second_flush = buffer.flush()

        assert len(first_flush) == 1
        assert len(second_flush) == 0

    def test_buffer_preserves_operation_fields(self):
        """Test buffer preserves all operation fields."""
        buffer = RollingContextBuffer(max_size=5)

        operation = {
            "type": "db_query",
            "details": {"query": "SELECT * FROM source"},
            "duration_ms": 45.2,
            "custom_field": "custom_value",
        }
        buffer.append(operation)

        operations = buffer.peek()
        assert operations[0]["type"] == "db_query"
        assert operations[0]["details"]["query"] == "SELECT * FROM source"
        assert operations[0]["duration_ms"] == 45.2
        assert operations[0]["custom_field"] == "custom_value"

    def test_buffer_handles_complex_details(self):
        """Test buffer handles nested dictionaries and lists."""
        buffer = RollingContextBuffer(max_size=5)

        operation = {
            "type": "complex",
            "details": {
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "string": "test",
            },
        }
        buffer.append(operation)

        operations = buffer.peek()
        assert operations[0]["details"]["nested"]["key"] == "value"
        assert operations[0]["details"]["list"] == [1, 2, 3]
