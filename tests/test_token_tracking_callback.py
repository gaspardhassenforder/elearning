"""
Unit tests for TokenTrackingCallback handler.

Tests token extraction from different AI provider formats and async save behavior.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.outputs import LLMResult, Generation
from langchain_core.messages import AIMessage

from open_notebook.observability.token_tracking_callback import TokenTrackingCallback


class TestTokenTrackingCallback:
    """Test suite for TokenTrackingCallback handler."""

    def test_extract_token_usage_openai_format(self):
        """Extracts tokens from OpenAI llm_output format."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                },
                "model_name": "gpt-4-turbo"
            }
        )

        # Act
        result = callback._extract_token_usage(response)

        # Assert
        assert result is not None
        assert result["input_tokens"] == 150
        assert result["output_tokens"] == 75

    def test_extract_token_usage_anthropic_format(self):
        """Extracts tokens from Anthropic llm_output format."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={
                "usage": {
                    "input_tokens": 200,
                    "output_tokens": 100,
                },
                "model_name": "claude-3-5-sonnet-20241022"
            }
        )

        # Act
        result = callback._extract_token_usage(response)

        # Assert
        assert result is not None
        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100

    def test_extract_token_usage_google_format(self):
        """Extracts tokens from Google llm_output format."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="search")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={
                "usage_metadata": {
                    "prompt_token_count": 300,
                    "candidates_token_count": 150,
                },
                "model_name": "gemini-flash-3"
            }
        )

        # Act
        result = callback._extract_token_usage(response)

        # Assert
        assert result is not None
        assert result["input_tokens"] == 300
        assert result["output_tokens"] == 150

    def test_extract_token_usage_missing_metadata(self):
        """Returns None when token_usage metadata is missing."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={"model_name": "gpt-4"}
        )

        # Act
        result = callback._extract_token_usage(response)

        # Assert
        assert result is None

    def test_derive_provider_from_model_name(self):
        """Correctly identifies provider from model name string."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")

        # Act & Assert
        assert callback._derive_provider("gpt-4-turbo") == "openai"
        assert callback._derive_provider("claude-3-5-sonnet-20241022") == "anthropic"
        assert callback._derive_provider("gemini-flash-3") == "google"
        assert callback._derive_provider("groq-llama-70b") == "groq"
        assert callback._derive_provider("mistral-large") == "mistral"
        assert callback._derive_provider("deepseek-coder") == "deepseek"
        assert callback._derive_provider("grok-2") == "xai"
        assert callback._derive_provider("ollama/llama2") == "ollama"
        assert callback._derive_provider("unknown-model") == "unknown"

    @pytest.mark.asyncio
    async def test_on_llm_end_saves_token_usage(self):
        """on_llm_end creates TokenUsage record and saves async."""
        # Arrange
        callback = TokenTrackingCallback(
            user_id="user:test123",
            company_id="company:xyz",
            notebook_id="notebook:abc",
            operation_type="chat"
        )

        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                },
                "model_name": "gpt-4-turbo"
            }
        )

        # Mock the async save
        with patch('open_notebook.observability.token_tracking_callback.TokenUsage') as MockTokenUsage:
            mock_instance = AsyncMock()
            MockTokenUsage.return_value = mock_instance

            # Act
            callback.on_llm_end(response)

            # Wait a bit for async task to complete (fire-and-forget)
            import asyncio
            await asyncio.sleep(0.1)

            # Assert - TokenUsage was created with correct params
            MockTokenUsage.assert_called_once()
            call_kwargs = MockTokenUsage.call_args.kwargs
            assert call_kwargs["user_id"] == "user:test123"
            assert call_kwargs["company_id"] == "company:xyz"
            assert call_kwargs["notebook_id"] == "notebook:abc"
            assert call_kwargs["model_provider"] == "openai"
            assert call_kwargs["model_name"] == "gpt-4-turbo"
            assert call_kwargs["input_tokens"] == 150
            assert call_kwargs["output_tokens"] == 75
            assert call_kwargs["operation_type"] == "chat"

    @pytest.mark.asyncio
    async def test_on_llm_end_handles_missing_metadata_gracefully(self):
        """on_llm_end logs warning but doesn't fail when token_usage missing."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={"model_name": "gpt-4"}
        )

        # Mock logger to capture warning
        with patch('open_notebook.observability.token_tracking_callback.logger') as mock_logger:
            # Act
            callback.on_llm_end(response)

            # Wait a bit
            import asyncio
            await asyncio.sleep(0.05)

            # Assert - Warning logged, no exception raised
            mock_logger.debug.assert_called_once()
            assert "No token usage metadata found" in str(mock_logger.debug.call_args)

    def test_extract_model_info_from_llm_output(self):
        """Extracts provider and model name from llm_output."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={"model_name": "gpt-4-turbo"}
        )

        # Act
        provider, model_name = callback._extract_model_info(response)

        # Assert
        assert provider == "openai"
        assert model_name == "gpt-4-turbo"

    def test_extract_model_info_fallback_to_unknown(self):
        """Defaults to 'unknown' when model_name missing."""
        # Arrange
        callback = TokenTrackingCallback(operation_type="chat")
        response = LLMResult(
            generations=[[Generation(text="test")]],
            llm_output={}
        )

        # Act
        provider, model_name = callback._extract_model_info(response)

        # Assert
        assert provider == "unknown"
        assert model_name == "unknown"
