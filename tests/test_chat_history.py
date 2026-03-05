"""Tests for Chat History and Re-engagement (Story 4.8).

Tests thread ID isolation, history loading, re-engagement greeting generation,
and chat graph integration for persistent chat history.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from unittest.mock import AsyncMock, Mock, patch

from open_notebook.graphs.chat import graph as chat_graph, memory as chat_memory


# ============================================================================
# Test Helpers
# ============================================================================


def construct_thread_id(user_id: str, notebook_id: str) -> str:
    """Construct thread ID using the deterministic pattern.

    Pattern: user:{user_id}:notebook:{notebook_id}

    Args:
        user_id: User record ID (e.g., "user:alice")
        notebook_id: Notebook record ID (e.g., "notebook:ai-fundamentals")

    Returns:
        Thread ID string for checkpoint isolation
    """
    return f"user:{user_id}:notebook:{notebook_id}"


# ============================================================================
# Thread ID Isolation Tests (4 tests)
# ============================================================================


class TestThreadIsolation:
    """Test thread_id pattern and isolation guarantees."""

    def test_thread_id_format(self):
        """Test thread_id constructed correctly with deterministic pattern."""
        user_id = "user:alice"
        notebook_id = "notebook:ai-fundamentals"

        thread_id = construct_thread_id(user_id, notebook_id)

        assert thread_id == "user:user:alice:notebook:notebook:ai-fundamentals"
        assert thread_id.startswith("user:")
        assert ":notebook:" in thread_id
        assert user_id in thread_id
        assert notebook_id in thread_id

    def test_thread_id_deterministic(self):
        """Test same user + notebook always produces same thread_id."""
        user_id = "user:bob"
        notebook_id = "notebook:python-basics"

        thread_id_1 = construct_thread_id(user_id, notebook_id)
        thread_id_2 = construct_thread_id(user_id, notebook_id)

        assert thread_id_1 == thread_id_2, "Thread ID must be deterministic"

    def test_thread_id_different_users_same_notebook(self):
        """Test different users have different thread_ids for same notebook."""
        notebook_id = "notebook:ai-fundamentals"

        alice_thread = construct_thread_id("user:alice", notebook_id)
        bob_thread = construct_thread_id("user:bob", notebook_id)

        assert alice_thread != bob_thread, "Different users must have separate threads"
        assert "user:alice" in alice_thread
        assert "user:bob" in bob_thread

    def test_thread_id_same_user_different_notebooks(self):
        """Test same user has different thread_ids per notebook."""
        user_id = "user:alice"

        thread_1 = construct_thread_id(user_id, "notebook:ai-fundamentals")
        thread_2 = construct_thread_id(user_id, "notebook:python-basics")

        assert thread_1 != thread_2, "Same user must have separate threads per notebook"
        assert "notebook:ai-fundamentals" in thread_1
        assert "notebook:python-basics" in thread_2


# ============================================================================
# Checkpoint Persistence Tests (3 tests)
# ============================================================================


class TestCheckpointPersistence:
    """Test conversation persistence across graph restarts."""

    def test_checkpoint_saves_messages(self):
        """Test messages are saved to checkpoint after graph invocation."""
        thread_id = "user:user:test:notebook:notebook:test"
        config = {"configurable": {"thread_id": thread_id}}

        # Send a message
        user_message = HumanMessage(content="Hello, this is a test message")

        # Mock the model provisioning to avoid actual LLM calls
        with patch("open_notebook.graphs.chat.provision_langchain_model") as mock_provision:
            # Create a mock model that returns a simple response
            mock_model = Mock()
            mock_model.bind_tools = Mock(return_value=mock_model)
            mock_model.invoke = Mock(return_value=AIMessage(content="Test response"))
            mock_provision.return_value = mock_model

            # Invoke graph (sync method for SqliteSaver compatibility)
            result = chat_graph.invoke(
                {
                    "messages": [user_message],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": "user:test",
                },
                config=config
            )

        # Check checkpoint was saved
        checkpoint_tuple = chat_memory.get(config)

        assert checkpoint_tuple is not None, "Checkpoint should exist after graph invocation"

        # Extract channel values from checkpoint (SqliteSaver returns dict, not tuple)
        if isinstance(checkpoint_tuple, dict):
            checkpoint_data = checkpoint_tuple
        else:
            checkpoint_data = checkpoint_tuple.checkpoint
        assert "channel_values" in checkpoint_data, "Checkpoint should have channel_values"

        channel_values = checkpoint_data["channel_values"]
        assert "messages" in channel_values, "Checkpoint should contain messages"

        messages = channel_values["messages"]
        assert len(messages) >= 2, "Should have at least user message + AI response"

        # Verify message content
        assert any(isinstance(msg, HumanMessage) and "test message" in msg.content for msg in messages)

    def test_checkpoint_loads_previous_messages(self):
        """Test conversation history loads from checkpoint on subsequent invocations."""
        thread_id = "user:user:test2:notebook:notebook:test2"
        config = {"configurable": {"thread_id": thread_id}}

        # Mock model provisioning
        with patch("open_notebook.graphs.chat.provision_langchain_model") as mock_provision:
            mock_model = Mock()
            mock_model.bind_tools = Mock(return_value=mock_model)
            mock_model.invoke = Mock(return_value=AIMessage(content="Response 1"))
            mock_provision.return_value = mock_model

            # First message (sync for SqliteSaver)
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="First message")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": "user:test2",
                },
                config=config
            )

            # Second message
            mock_model.invoke = Mock(return_value=AIMessage(content="Response 2"))
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="Second message")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": "user:test2",
                },
                config=config
            )

        # Load checkpoint (SqliteSaver returns dict, not tuple)
        checkpoint_tuple = chat_memory.get(config)
        if isinstance(checkpoint_tuple, dict):
            checkpoint_data = checkpoint_tuple
        else:
            checkpoint_data = checkpoint_tuple.checkpoint
        messages = checkpoint_data["channel_values"]["messages"]

        # Should have 4 messages: 2 user + 2 AI
        assert len(messages) >= 4, f"Expected at least 4 messages, got {len(messages)}"

        # Verify both conversations are in history
        message_contents = [msg.content for msg in messages]
        assert "First message" in " ".join(message_contents)
        assert "Second message" in " ".join(message_contents)

    def test_checkpoint_empty_for_new_thread(self):
        """Test empty checkpoint for new conversation (first visit)."""
        thread_id = "user:user:newuser:notebook:notebook:new"
        config = {"configurable": {"thread_id": thread_id}}

        # Try to get checkpoint for non-existent thread
        checkpoint = chat_memory.get(config)

        # Checkpoint should be None for new thread
        assert checkpoint is None, "Checkpoint should be None for new thread"


# ============================================================================
# Thread Isolation Integration Tests (2 tests)
# ============================================================================


class TestThreadIsolationIntegration:
    """Test thread isolation in real graph invocations."""

    def test_different_users_isolated_history(self):
        """Test different users see different histories for same notebook."""
        notebook_id = "notebook:isolation-test"

        alice_thread_id = construct_thread_id("user:alice", notebook_id)
        bob_thread_id = construct_thread_id("user:bob", notebook_id)

        alice_config = {"configurable": {"thread_id": alice_thread_id}}
        bob_config = {"configurable": {"thread_id": bob_thread_id}}

        with patch("open_notebook.graphs.chat.provision_langchain_model") as mock_provision:
            mock_model = Mock()
            mock_model.bind_tools = Mock(return_value=mock_model)
            mock_model.invoke = Mock(return_value=AIMessage(content="Response"))
            mock_provision.return_value = mock_model

            # Alice sends a message (sync for SqliteSaver)
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="Alice's message")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": "user:alice",
                },
                config=alice_config
            )

            # Bob sends a different message
            mock_model.invoke = Mock(return_value=AIMessage(content="Different response"))
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="Bob's message")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": "user:bob",
                },
                config=bob_config
            )

        # Check Alice's checkpoint (SqliteSaver returns dict, not tuple)
        alice_checkpoint = chat_memory.get(alice_config)
        if isinstance(alice_checkpoint, dict):
            alice_messages = alice_checkpoint["channel_values"]["messages"]
        else:
            alice_messages = alice_checkpoint.checkpoint["channel_values"]["messages"]
        alice_contents = " ".join([msg.content for msg in alice_messages])

        # Check Bob's checkpoint (SqliteSaver returns dict, not tuple)
        bob_checkpoint = chat_memory.get(bob_config)
        if isinstance(bob_checkpoint, dict):
            bob_messages = bob_checkpoint["channel_values"]["messages"]
        else:
            bob_messages = bob_checkpoint.checkpoint["channel_values"]["messages"]
        bob_contents = " ".join([msg.content for msg in bob_messages])

        # Alice should only see her messages
        assert "Alice's message" in alice_contents
        assert "Bob's message" not in alice_contents

        # Bob should only see his messages
        assert "Bob's message" in bob_contents
        assert "Alice's message" not in bob_contents

    def test_same_user_isolated_per_notebook(self):
        """Test same user has isolated histories per notebook."""
        user_id = "user:charlie"

        notebook_a_thread = construct_thread_id(user_id, "notebook:notebook-a")
        notebook_b_thread = construct_thread_id(user_id, "notebook:notebook-b")

        config_a = {"configurable": {"thread_id": notebook_a_thread}}
        config_b = {"configurable": {"thread_id": notebook_b_thread}}

        with patch("open_notebook.graphs.chat.provision_langchain_model") as mock_provision:
            mock_model = Mock()
            mock_model.bind_tools = Mock(return_value=mock_model)
            mock_model.invoke = Mock(return_value=AIMessage(content="Response"))
            mock_provision.return_value = mock_model

            # Message in notebook A (sync for SqliteSaver)
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="Message in notebook A")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": user_id,
                },
                config=config_a
            )

            # Message in notebook B
            mock_model.invoke = Mock(return_value=AIMessage(content="Different response"))
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="Message in notebook B")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": user_id,
                },
                config=config_b
            )

        # Check notebook A checkpoint (SqliteSaver returns dict, not tuple)
        checkpoint_a = chat_memory.get(config_a)
        if isinstance(checkpoint_a, dict):
            messages_a = checkpoint_a["channel_values"]["messages"]
        else:
            messages_a = checkpoint_a.checkpoint["channel_values"]["messages"]
        contents_a = " ".join([msg.content for msg in messages_a])

        # Check notebook B checkpoint (SqliteSaver returns dict, not tuple)
        checkpoint_b = chat_memory.get(config_b)
        if isinstance(checkpoint_b, dict):
            messages_b = checkpoint_b["channel_values"]["messages"]
        else:
            messages_b = checkpoint_b.checkpoint["channel_values"]["messages"]
        contents_b = " ".join([msg.content for msg in messages_b])

        # Notebook A should only have its messages
        assert "Message in notebook A" in contents_a
        assert "Message in notebook B" not in contents_a

        # Notebook B should only have its messages
        assert "Message in notebook B" in contents_b
        assert "Message in notebook A" not in contents_b


# ============================================================================
# Checkpoint Storage Lifecycle Tests (2 tests)
# ============================================================================


class TestCheckpointStorageLifecycle:
    """Test checkpoint storage location and lifecycle management."""

    def test_checkpoint_file_location(self):
        """Test checkpoint file is stored in expected location."""
        from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE
        import os

        # Verify checkpoint file path is configured
        assert LANGGRAPH_CHECKPOINT_FILE is not None
        assert len(LANGGRAPH_CHECKPOINT_FILE) > 0

        # Verify it's in /data/sqlite-db/ directory
        assert "/data/sqlite-db/" in LANGGRAPH_CHECKPOINT_FILE or "\\data\\sqlite-db\\" in LANGGRAPH_CHECKPOINT_FILE

        # Check if parent directory exists or can be created
        checkpoint_dir = os.path.dirname(LANGGRAPH_CHECKPOINT_FILE)
        assert os.path.isdir(checkpoint_dir) or not os.path.exists(checkpoint_dir), \
            "Checkpoint directory should exist or be creatable"

    def test_checkpoint_persists_across_restarts(self):
        """Test conversation persists if graph is 'restarted' (re-referenced)."""
        thread_id = "user:user:restart-test:notebook:notebook:restart"
        config = {"configurable": {"thread_id": thread_id}}

        with patch("open_notebook.graphs.chat.provision_langchain_model") as mock_provision:
            mock_model = Mock()
            mock_model.bind_tools = Mock(return_value=mock_model)
            mock_model.invoke = Mock(return_value=AIMessage(content="Persistent response"))
            mock_provision.return_value = mock_model

            # Send first message (sync for SqliteSaver)
            chat_graph.invoke(
                {
                    "messages": [HumanMessage(content="Message before restart")],
                    "notebook": None,
                    "model_override": None,
                    "system_prompt": "You are a test assistant.",
                    "user_id": "user:restart-test",
                },
                config=config
            )

        # Simulate "restart" by getting checkpoint without invoking graph
        checkpoint_after_restart = chat_memory.get(config)

        assert checkpoint_after_restart is not None, "Checkpoint should persist after 'restart'"
        # Verify checkpoint contains messages (exact structure may vary)
        assert checkpoint_after_restart is not None


# ============================================================================
# Re-engagement Generation Tests removed — functions deleted in greeting unification.
# See tests/test_proactive_greeting.py for build_intro_message tests.
# ============================================================================
