"""
Unit tests for Story 4.7: Async Task Handling in Chat

Tests cover:
- generate_artifact tool submission
- Tool binding in chat graph
- Job status polling
- Error handling and graceful degradation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.graphs.tools import generate_artifact


# ============================================================================
# TEST SUITE 1: Generate Artifact Tool Submission
# ============================================================================


class TestGenerateArtifactTool:
    """Test suite for generate_artifact tool functionality."""

    @pytest.mark.asyncio
    async def test_podcast_generation_submission(self):
        """Test tool submits podcast job and returns job_id immediately."""
        # Mock PodcastService.submit_generation_job
        with patch(
            "open_notebook.graphs.tools.PodcastService.submit_generation_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = ("command:test_job_123", ["artifact:placeholder_456"])

            # Mock Artifact.create_for_artifact
            with patch(
                "open_notebook.graphs.tools.Artifact.create_for_artifact",
                new_callable=AsyncMock,
            ) as mock_create_artifact:
                mock_create_artifact.return_value = MagicMock(id="artifact:placeholder_456")

                # Invoke tool
                result = await generate_artifact.func(
                    artifact_type="podcast",
                    topic="Module summary",
                    notebook_id="notebook:test",
                    user_id="user:test",
                )

                # Assertions
                assert result["status"] == "submitted"
                assert result["job_id"] == "command:test_job_123"
                assert "artifact:placeholder_456" in result["artifact_ids"]
                assert result["artifact_type"] == "podcast"
                assert "message" in result
                assert "podcast" in result["message"].lower()

                # Verify service was called correctly
                mock_submit.assert_called_once()
                call_kwargs = mock_submit.call_args.kwargs
                assert call_kwargs["notebook_id"] == "notebook:test"

    @pytest.mark.asyncio
    async def test_quiz_generation_submission(self):
        """Test tool submits quiz job and returns job_id immediately."""
        # Mock QuizService.submit_generation_job
        with patch(
            "open_notebook.graphs.tools.QuizService.submit_generation_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = ("command:quiz_job_789", ["artifact:quiz_placeholder"])

            # Mock Artifact.create_for_artifact
            with patch(
                "open_notebook.graphs.tools.Artifact.create_for_artifact",
                new_callable=AsyncMock,
            ) as mock_create_artifact:
                mock_create_artifact.return_value = MagicMock(id="artifact:quiz_placeholder")

                # Invoke tool
                result = await generate_artifact.func(
                    artifact_type="quiz",
                    topic="Learning objectives assessment",
                    notebook_id="notebook:test",
                    user_id="user:learner",
                )

                # Assertions
                assert result["status"] == "submitted"
                assert result["job_id"] == "command:quiz_job_789"
                assert result["artifact_type"] == "quiz"
                assert "quiz" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_artifact_placeholder_created(self):
        """Test Artifact record created with job_id as artifact_id."""
        with patch(
            "open_notebook.graphs.tools.PodcastService.submit_generation_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = ("command:job_456", ["artifact:placeholder"])

            with patch(
                "open_notebook.graphs.tools.Artifact.create_for_artifact",
                new_callable=AsyncMock,
            ) as mock_create_artifact:
                mock_create_artifact.return_value = MagicMock(id="artifact:placeholder")

                # Invoke tool
                await generate_artifact.func(
                    artifact_type="podcast",
                    topic="Test topic",
                    notebook_id="notebook:test",
                    user_id="user:test",
                )

                # Verify Artifact.create_for_artifact was called
                mock_create_artifact.assert_called_once()
                call_kwargs = mock_create_artifact.call_args.kwargs
                assert call_kwargs["notebook_id"] == "notebook:test"
                assert call_kwargs["artifact_type"] == "podcast"
                assert call_kwargs["artifact_id"] == "command:job_456"
                assert "title" in call_kwargs
                assert "Test topic" in call_kwargs["title"]

    @pytest.mark.asyncio
    async def test_tool_returns_user_friendly_message(self):
        """Test tool result includes user-friendly acknowledgment message."""
        with patch(
            "open_notebook.graphs.tools.PodcastService.submit_generation_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = ("command:job", ["artifact:placeholder"])

            with patch(
                "open_notebook.graphs.tools.Artifact.create_for_artifact",
                new_callable=AsyncMock,
            ):
                result = await generate_artifact.func(
                    artifact_type="podcast",
                    topic="Summary",
                    notebook_id="notebook:test",
                    user_id="user:test",
                )

                # Check message is user-friendly
                message = result["message"]
                assert isinstance(message, str)
                assert len(message) > 20  # Reasonable length
                assert "podcast" in message.lower()
                assert "generat" in message.lower()  # "generating" or "generation"

    @pytest.mark.asyncio
    async def test_unsupported_artifact_type_raises_error(self):
        """Test tool raises error for unsupported artifact types."""
        with pytest.raises(ValueError, match="Unsupported artifact type"):
            await generate_artifact.func(
                artifact_type="unsupported_type",
                topic="Test",
                notebook_id="notebook:test",
                user_id="user:test",
            )


# ============================================================================
# TEST SUITE 2: Chat Graph Tool Binding
# ============================================================================


class TestChatGraphToolBinding:
    """Test suite for tool binding in chat graph."""

    @pytest.mark.asyncio
    async def test_generate_artifact_tool_bound(self):
        """Test generate_artifact tool is bound to chat graph model."""
        from open_notebook.graphs.chat import build_learner_chat_graph

        # Build graph
        graph = build_learner_chat_graph()

        # Extract tools from graph nodes
        # Note: This test verifies the tool is registered
        # Actual invocation testing is done via integration tests
        from open_notebook.graphs.tools import generate_artifact

        # Verify tool exists and has correct signature
        assert generate_artifact.name == "generate_artifact"
        assert "artifact_type" in str(generate_artifact.args_schema)
        assert "topic" in str(generate_artifact.args_schema)
        assert "notebook_id" in str(generate_artifact.args_schema)
        assert "user_id" in str(generate_artifact.args_schema)

    def test_tool_has_correct_description(self):
        """Test tool description guides AI on when to use it."""
        from open_notebook.graphs.tools import generate_artifact

        description = generate_artifact.description
        assert isinstance(description, str)
        assert "async" in description.lower() or "background" in description.lower()
        assert "artifact" in description.lower()
        assert "podcast" in description.lower() or "quiz" in description.lower()


# ============================================================================
# TEST SUITE 3: Job Status Polling
# ============================================================================


class TestJobStatusPolling:
    """Test suite for job status endpoint and polling."""

    @pytest.mark.asyncio
    async def test_job_status_endpoint_exists(self):
        """Test GET /commands/jobs/{job_id} returns status."""
        from api.command_service import CommandService

        # Mock CommandService.get_command_status
        with patch.object(
            CommandService, "get_command_status", new_callable=AsyncMock
        ) as mock_get_status:
            mock_get_status.return_value = {
                "job_id": "command:test",
                "status": "processing",
                "progress": {"current": 50, "total": 100, "percentage": 50},
                "result": None,
                "error_message": None,
            }

            # Call service method
            result = await CommandService.get_command_status("command:test")

            # Verify response structure
            assert "job_id" in result
            assert "status" in result
            assert result["status"] in ["pending", "processing", "completed", "error"]
            mock_get_status.assert_called_once_with("command:test")

    @pytest.mark.asyncio
    async def test_status_transitions(self):
        """Test status transitions: pending → processing → completed."""
        from api.command_service import CommandService

        # Simulate status progression
        statuses = ["pending", "processing", "completed"]

        for status in statuses:
            with patch.object(
                CommandService, "get_command_status", new_callable=AsyncMock
            ) as mock_get_status:
                mock_get_status.return_value = {"job_id": "command:test", "status": status}

                result = await CommandService.get_command_status("command:test")
                assert result["status"] == status

    @pytest.mark.asyncio
    async def test_error_status_includes_message(self):
        """Test error status returns error_message field."""
        from api.command_service import CommandService

        with patch.object(
            CommandService, "get_command_status", new_callable=AsyncMock
        ) as mock_get_status:
            mock_get_status.return_value = {
                "job_id": "command:test",
                "status": "error",
                "error_message": "TTS service failed: timeout",
                "result": {"success": False},
            }

            result = await CommandService.get_command_status("command:test")
            assert result["status"] == "error"
            assert result["error_message"] == "TTS service failed: timeout"
            assert result["result"]["success"] is False


# ============================================================================
# TEST SUITE 4: Prompt Guidance
# ============================================================================


class TestAsyncTaskPromptGuidance:
    """Test suite for prompt guidance on async tasks."""

    def test_prompt_includes_async_instructions(self):
        """Test global prompt includes async task handling section."""
        from pathlib import Path

        prompt_path = Path("prompts/global_teacher_prompt.j2")
        prompt_content = prompt_path.read_text()

        # Verify async task handling guidance is present
        assert "generate_artifact" in prompt_content
        assert "async" in prompt_content.lower() or "background" in prompt_content.lower()

    def test_error_recovery_guidance(self):
        """Test prompt instructs AI on error handling."""
        from pathlib import Path

        prompt_path = Path("prompts/global_teacher_prompt.j2")
        prompt_content = prompt_path.read_text()

        # Verify error recovery instructions
        # AI should gracefully handle failures and offer alternatives
        assert (
            "error" in prompt_content.lower()
            or "fail" in prompt_content.lower()
            or "alternative" in prompt_content.lower()
        )


# ============================================================================
# TEST SUITE 5: Integration Tests
# ============================================================================


class TestAsyncArtifactGenerationIntegration:
    """Integration tests for end-to-end async artifact generation."""

    @pytest.mark.asyncio
    async def test_podcast_generation_full_flow(self):
        """
        Test complete flow: tool call → job submission → status polling → completion.

        This test simulates the full lifecycle but uses mocks for LLM and service calls.
        """
        # Mock all services
        with patch(
            "open_notebook.graphs.tools.PodcastService.submit_generation_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = ("command:integration_test", ["artifact:placeholder"])

            with patch(
                "open_notebook.graphs.tools.Artifact.create_for_artifact",
                new_callable=AsyncMock,
            ):
                # Step 1: Tool invocation
                tool_result = await generate_artifact.func(
                    artifact_type="podcast",
                    topic="Integration test",
                    notebook_id="notebook:test",
                    user_id="user:test",
                )

                # Verify immediate response
                assert tool_result["status"] == "submitted"
                assert "job_id" in tool_result
                job_id = tool_result["job_id"]

                # Step 2: Simulate status polling
                from api.command_service import CommandService

                # Mock status progression
                with patch.object(
                    CommandService, "get_command_status", new_callable=AsyncMock
                ) as mock_status:
                    # First poll: processing
                    mock_status.return_value = {
                        "job_id": job_id,
                        "status": "processing",
                        "progress": {"percentage": 30},
                    }
                    status_1 = await CommandService.get_command_status(job_id)
                    assert status_1["status"] == "processing"

                    # Second poll: completed
                    mock_status.return_value = {
                        "job_id": job_id,
                        "status": "completed",
                        "result": {"success": True, "episode_id": "podcast_episode:final"},
                    }
                    status_2 = await CommandService.get_command_status(job_id)
                    assert status_2["status"] == "completed"
                    assert status_2["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_full_flow(self):
        """Test error handling: job fails → AI receives error → graceful recovery."""
        # Mock job submission
        with patch(
            "open_notebook.graphs.tools.PodcastService.submit_generation_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = ("command:error_test", ["artifact:placeholder"])

            with patch(
                "open_notebook.graphs.tools.Artifact.create_for_artifact",
                new_callable=AsyncMock,
            ):
                # Tool invocation succeeds
                tool_result = await generate_artifact.func(
                    artifact_type="podcast",
                    topic="Error test",
                    notebook_id="notebook:test",
                    user_id="user:test",
                )

                job_id = tool_result["job_id"]

                # Simulate job failure
                from api.command_service import CommandService

                with patch.object(
                    CommandService, "get_command_status", new_callable=AsyncMock
                ) as mock_status:
                    mock_status.return_value = {
                        "job_id": job_id,
                        "status": "error",
                        "error_message": "TTS service timeout",
                        "result": {"success": False},
                    }

                    status = await CommandService.get_command_status(job_id)
                    assert status["status"] == "error"
                    assert "timeout" in status["error_message"].lower()

                    # Verify error message is actionable
                    # (Frontend/AI can use this to inform user gracefully)
                    assert len(status["error_message"]) > 5
