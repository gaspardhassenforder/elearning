"""
Token Tracking Callback Handler

LangChain callback handler that captures token usage for all LLM calls.
Saves TokenUsage records asynchronously (non-blocking) for every LLM operation.
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from loguru import logger

from open_notebook.domain.token_usage import TokenUsage


class TokenTrackingCallback(BaseCallbackHandler):
    """
    LangChain callback handler that captures token usage for all LLM calls.

    Saves TokenUsage records asynchronously (non-blocking) for every LLM operation.
    Gracefully handles missing token usage metadata (logs warning, doesn't fail).

    Usage:
        >>> from open_notebook.observability.token_tracking_callback import TokenTrackingCallback
        >>> callback = TokenTrackingCallback(
        ...     user_id="user:abc123",
        ...     company_id="company:xyz",
        ...     notebook_id="notebook:456",
        ...     operation_type="chat"
        ... )
        >>> config = RunnableConfig(callbacks=[callback])
        >>> result = await graph.ainvoke(state, config)
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        notebook_id: Optional[str] = None,
        operation_type: str = "unknown",
    ):
        """
        Initialize token tracking callback.

        Args:
            user_id: User performing operation (None for system ops)
            company_id: Company context for learner operations
            notebook_id: Module context if applicable
            operation_type: Type of operation (chat, quiz_generation, embedding, etc.)
        """
        super().__init__()
        self.user_id = user_id
        self.company_id = company_id
        self.notebook_id = notebook_id
        self.operation_type = operation_type

    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """
        Capture token usage when LLM call completes.

        Extracts token counts from response metadata and saves TokenUsage record
        asynchronously (fire-and-forget, non-blocking).
        """
        try:
            # Extract token usage from llm_output
            token_usage = self._extract_token_usage(response)

            if not token_usage:
                logger.debug(
                    f"No token usage metadata found for {self.operation_type} operation"
                )
                return

            # Extract model metadata
            model_provider, model_name = self._extract_model_info(response)

            # Create TokenUsage record
            usage_record = TokenUsage(
                user_id=self.user_id,
                company_id=self.company_id,
                notebook_id=self.notebook_id,
                model_provider=model_provider,
                model_name=model_name,
                input_tokens=token_usage["input_tokens"],
                output_tokens=token_usage["output_tokens"],
                operation_type=self.operation_type,
                timestamp=datetime.now(timezone.utc),
            )

            # Fire-and-forget async save (non-blocking)
            task = asyncio.create_task(self._save_usage_async(usage_record))
            # Add done callback to log unhandled exceptions
            task.add_done_callback(self._handle_task_exception)

        except Exception as e:
            # Log error but don't raise - token tracking failure should not block workflow
            logger.warning(
                "Failed to capture token usage for {}: {}", self.operation_type, str(e)
            )

    def _extract_token_usage(self, response: LLMResult) -> Optional[Dict[str, int]]:
        """
        Extract token counts from LLMResult metadata.

        Handles different providers' metadata formats:
        - OpenAI: llm_output["token_usage"]["prompt_tokens", "completion_tokens"]
        - Anthropic: llm_output["usage"]["input_tokens", "output_tokens"]
        - Google: llm_output["usage_metadata"]["prompt_token_count", "candidates_token_count"]

        Returns:
            {"input_tokens": int, "output_tokens": int} or None if not found
        """
        if not response.llm_output:
            return None

        # OpenAI format
        if "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            return {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            }

        # Anthropic format
        if "usage" in response.llm_output:
            usage = response.llm_output["usage"]
            return {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }

        # Google format
        if "usage_metadata" in response.llm_output:
            usage = response.llm_output["usage_metadata"]
            return {
                "input_tokens": usage.get("prompt_token_count", 0),
                "output_tokens": usage.get("candidates_token_count", 0),
            }

        return None

    def _extract_model_info(self, response: LLMResult) -> tuple[str, str]:
        """
        Extract provider and model name from response metadata.

        Returns:
            (provider: str, model_name: str)

        Example:
            ("openai", "gpt-4-turbo")
            ("anthropic", "claude-3-5-sonnet-20241022")
            ("google", "gemini-3-flash-preview")
        """
        model_name = "unknown"

        if response.llm_output and "model_name" in response.llm_output:
            model_name = response.llm_output["model_name"]
        elif response.generations and len(response.generations) > 0:
            gen = response.generations[0][0]
            if hasattr(gen, "message") and hasattr(gen.message, "response_metadata"):
                model_name = gen.message.response_metadata.get("model", "unknown")

        # Derive provider from model name
        provider = self._derive_provider(model_name)

        return provider, model_name

    def _derive_provider(self, model_name: str) -> str:
        """Derive provider from model name using pattern matching."""
        model_lower = model_name.lower()

        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower or "google" in model_lower:
            return "google"
        elif "groq" in model_lower:
            return "groq"
        elif "mistral" in model_lower:
            return "mistral"
        elif "ollama" in model_lower:
            return "ollama"
        elif "deepseek" in model_lower:
            return "deepseek"
        elif "grok" in model_lower or "xai" in model_lower:
            return "xai"
        else:
            return "unknown"

    async def _save_usage_async(self, usage_record: TokenUsage) -> None:
        """
        Async save of TokenUsage record (fire-and-forget).

        Catches all exceptions to prevent workflow disruption.
        """
        try:
            await usage_record.save()
            logger.debug(
                f"Token usage saved: {usage_record.input_tokens} in + "
                f"{usage_record.output_tokens} out ({usage_record.operation_type})"
            )
        except Exception as e:
            logger.error("Failed to save TokenUsage record: {}", str(e))

    def _handle_task_exception(self, task) -> None:
        """
        Callback to handle unhandled exceptions in background save task.

        Logs any exception that wasn't caught by _save_usage_async.
        """
        try:
            # Check if task raised an exception
            exception = task.exception()
            if exception:
                logger.error(
                    "Unhandled exception in token usage save task: {}", str(exception)
                )
        except Exception as e:
            # task.exception() itself can raise if task was cancelled
            logger.error("Error checking task exception: {}", str(e))
