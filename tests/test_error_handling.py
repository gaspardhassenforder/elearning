"""Story 7.1: Error Handling Tests

Tests for graceful error handling patterns across backend:
- Tool error response structure and user-safety
- Prompt error recovery instructions
- SSE error event format

These tests ensure technical details are never leaked to learners
and all error responses follow the standardized format.
"""

import pytest
from pathlib import Path


class TestPromptErrorRecovery:
    """Test AI prompt contains error recovery instructions."""

    def test_prompt_contains_error_handling_section(self):
        """Test global prompt has error recovery section."""
        prompt_path = Path("prompts/global_teacher_prompt.j2")
        assert prompt_path.exists(), "global_teacher_prompt.j2 should exist"

        content = prompt_path.read_text()

        # Must have error handling section
        assert "ERROR HANDLING" in content.upper(), "Prompt should have ERROR HANDLING section"
        assert "gracefully" in content.lower(), "Prompt should mention graceful handling"

    def test_prompt_contains_never_mention_technical_details(self):
        """Test prompt instructs AI to never expose technical details."""
        prompt_path = Path("prompts/global_teacher_prompt.j2")
        content = prompt_path.read_text()

        # Must instruct to not expose technical details
        assert "technical" in content.lower() or "NEVER mention" in content, \
            "Prompt should instruct to not expose technical details"
        assert "IDs" in content or "status codes" in content.lower(), \
            "Prompt should specifically mention IDs and status codes to avoid"

    def test_prompt_contains_tool_error_handling(self):
        """Test prompt has tool-specific error handling guidance."""
        prompt_path = Path("prompts/global_teacher_prompt.j2")
        content = prompt_path.read_text()

        # Should mention specific tools
        assert "surface_document" in content or "Document" in content, \
            "Prompt should mention document tool errors"
        assert "surface_quiz" in content or "Quiz" in content or "quiz" in content, \
            "Prompt should mention quiz tool errors"

    def test_prompt_contains_continue_teaching_guidance(self):
        """Test prompt instructs AI to continue teaching after errors."""
        prompt_path = Path("prompts/global_teacher_prompt.j2")
        content = prompt_path.read_text()

        # Must have continuity guidance
        assert "continue" in content.lower(), \
            "Prompt should instruct to continue after errors"
        assert "alternative" in content.lower() or "another way" in content.lower(), \
            "Prompt should suggest offering alternatives"


class TestToolErrorResponseFormat:
    """Test tool error responses have correct structure."""

    def test_tools_file_exists(self):
        """Test tools.py file exists."""
        tools_path = Path("open_notebook/graphs/tools.py")
        assert tools_path.exists(), "tools.py should exist"

    def test_tools_use_standardized_error_format(self):
        """Test tools return standardized error format."""
        tools_path = Path("open_notebook/graphs/tools.py")
        content = tools_path.read_text()

        # Should have error_type field usage
        assert "error_type" in content, "Tools should use error_type field"

        # Should have recoverable field usage
        assert "recoverable" in content, "Tools should use recoverable field"

    def test_tools_use_known_error_types(self):
        """Test tools use known error type values."""
        tools_path = Path("open_notebook/graphs/tools.py")
        content = tools_path.read_text()

        # Should use at least some known error types
        known_types = ["not_found", "access_denied", "service_error", "validation", "not_ready"]
        found_types = [t for t in known_types if f'"{t}"' in content or f"'{t}'" in content]

        assert len(found_types) >= 2, \
            f"Tools should use known error types, found: {found_types}"

    def test_tools_dont_expose_ids_in_errors(self):
        """Test tools don't expose source/quiz IDs in user-facing messages."""
        tools_path = Path("open_notebook/graphs/tools.py")
        content = tools_path.read_text()

        # Error messages should not include dynamic IDs in the "error" field
        # Look for patterns that would include IDs in error messages
        import re

        # Find all "error" field assignments
        error_patterns = re.findall(r'"error":\s*[f]?"([^"]+)"', content)
        error_patterns.extend(re.findall(r"'error':\s*[f]?'([^']+)'", content))

        for error_msg in error_patterns:
            # Should not contain ID patterns
            assert "{source_id}" not in error_msg, f"Error message exposes source_id: {error_msg}"
            assert "{quiz_id}" not in error_msg, f"Error message exposes quiz_id: {error_msg}"
            assert "{podcast_id}" not in error_msg, f"Error message exposes podcast_id: {error_msg}"

    def test_tools_log_full_errors_server_side(self):
        """Test tools log full error context before returning safe message."""
        tools_path = Path("open_notebook/graphs/tools.py")
        content = tools_path.read_text()

        # Should use logger.error or logger.warning
        assert "logger.error" in content or "logger.warning" in content, \
            "Tools should log errors server-side"

        # Should use exc_info=True for full stack traces
        assert "exc_info=True" in content, \
            "Tools should log with exc_info=True for debugging"


class TestSSEErrorEvents:
    """Test SSE error event structure in learner_chat.py."""

    def test_learner_chat_router_exists(self):
        """Test learner_chat.py exists."""
        router_path = Path("api/routers/learner_chat.py")
        assert router_path.exists(), "learner_chat.py should exist"

    def test_sse_error_has_structured_format(self):
        """Test SSE error events have error_type and recoverable fields."""
        router_path = Path("api/routers/learner_chat.py")
        content = router_path.read_text()

        # Should send structured error event
        assert "error_type" in content, "SSE error should include error_type"
        assert "recoverable" in content, "SSE error should include recoverable flag"

    def test_sse_error_has_user_friendly_message(self):
        """Test SSE error events have user-friendly messages."""
        router_path = Path("api/routers/learner_chat.py")
        content = router_path.read_text()

        # Should have user-friendly error message
        assert "I had trouble" in content or "user-friendly" in content.lower(), \
            "SSE error should have user-friendly message"

    def test_sse_error_logs_full_details(self):
        """Test SSE errors are logged fully before sending safe event."""
        router_path = Path("api/routers/learner_chat.py")
        content = router_path.read_text()

        # Should log with exc_info=True before sending safe message
        assert "exc_info=True" in content, \
            "SSE error handling should log with exc_info=True"


class TestErrorTypeValues:
    """Test error type values are consistent across codebase."""

    EXPECTED_ERROR_TYPES = ["not_found", "access_denied", "service_error", "validation", "not_ready"]

    def test_frontend_error_handler_knows_error_types(self):
        """Test frontend error-handler.ts knows all error types."""
        handler_path = Path("frontend/src/lib/utils/error-handler.ts")
        assert handler_path.exists(), "error-handler.ts should exist"

        content = handler_path.read_text()

        # Should define ErrorType type
        assert "ErrorType" in content, "Should define ErrorType type"

        # Should have mappings for known types
        for error_type in self.EXPECTED_ERROR_TYPES:
            assert error_type in content, f"Frontend should handle error_type: {error_type}"

    def test_frontend_learner_chat_handles_error_events(self):
        """Test frontend learner-chat.ts handles SSE error events."""
        chat_path = Path("frontend/src/lib/api/learner-chat.ts")
        assert chat_path.exists(), "learner-chat.ts should exist"

        content = chat_path.read_text()

        # Should have error event type
        assert "'error'" in content or '"error"' in content, \
            "Should handle error event type"

        # Should yield/handle error events
        assert "errorData" in content or "SSEErrorData" in content, \
            "Should have error data structure"
