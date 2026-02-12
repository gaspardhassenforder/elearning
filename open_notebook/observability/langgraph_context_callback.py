"""
LangGraph callback handler for context logging.

This module provides a callback handler that logs LangGraph operations
(node execution, tool invocations, LLM calls) to the rolling context buffer
for error diagnostics.
"""

from typing import Any, Dict, List, Optional

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from open_notebook.observability.request_context import log_operation


class ContextLoggingCallback(BaseCallbackHandler):
    """
    LangGraph callback handler that logs operations to rolling buffer.

    Captures:
    - Chain/graph execution (start/end)
    - Node entry/exit with timing
    - Tool invocations with inputs/outputs
    - LLM calls with token counts
    - Errors and exceptions

    Usage:
        >>> from open_notebook.observability.langgraph_context_callback import ContextLoggingCallback
        >>> result = await graph.ainvoke(
        ...     {"input": user_input},
        ...     config={"callbacks": [ContextLoggingCallback()]}
        ... )
    """

    def __init__(self):
        """Initialize callback handler."""
        super().__init__()
        self.run_id_to_name = {}  # Track run IDs to chain/tool names

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Log chain/graph start."""
        chain_name = serialized.get("name", "unknown") if serialized else "unknown"
        run_id = kwargs.get("run_id")

        if run_id:
            self.run_id_to_name[str(run_id)] = chain_name

        # Sanitize inputs (truncate long strings)
        sanitized_inputs = self._sanitize_dict(inputs)

        log_operation(
            "graph_chain_start",
            {
                "chain": chain_name,
                "run_id": str(run_id) if run_id else None,
                **self._flatten_dict(sanitized_inputs, prefix="input"),
            },
        )

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Log chain/graph end."""
        run_id = kwargs.get("run_id")
        chain_name = self.run_id_to_name.get(str(run_id), "unknown") if run_id else "unknown"

        # Sanitize outputs
        sanitized_outputs = self._sanitize_dict(outputs)

        log_operation(
            "graph_chain_end",
            {
                "chain": chain_name,
                "run_id": str(run_id) if run_id else None,
                **self._flatten_dict(sanitized_outputs, prefix="output"),
            },
        )

    def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Log chain/graph error."""
        run_id = kwargs.get("run_id")
        chain_name = self.run_id_to_name.get(str(run_id), "unknown") if run_id else "unknown"

        log_operation(
            "graph_chain_error",
            {
                "chain": chain_name,
                "run_id": str(run_id) if run_id else None,
                "error": str(error)[:200],
                "error_type": type(error).__name__,
            },
        )

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Log tool invocation start."""
        tool_name = serialized.get("name", "unknown") if serialized else "unknown"
        run_id = kwargs.get("run_id")

        log_operation(
            "graph_tool_start",
            {
                "tool": tool_name,
                "run_id": str(run_id) if run_id else None,
                "input": input_str[:200] if isinstance(input_str, str) else str(input_str)[:200],
            },
        )

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """Log tool invocation end."""
        run_id = kwargs.get("run_id")

        log_operation(
            "graph_tool_end",
            {
                "run_id": str(run_id) if run_id else None,
                "output": output[:200] if isinstance(output, str) else str(output)[:200],
            },
        )

    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Log tool error."""
        run_id = kwargs.get("run_id")

        log_operation(
            "graph_tool_error",
            {
                "run_id": str(run_id) if run_id else None,
                "error": str(error)[:200],
                "error_type": type(error).__name__,
            },
        )

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Log LLM call start."""
        model_name = serialized.get("model_name", serialized.get("name", "unknown")) if serialized else "unknown"
        run_id = kwargs.get("run_id")

        log_operation(
            "graph_llm_start",
            {
                "model": model_name,
                "run_id": str(run_id) if run_id else None,
                "prompt_count": len(prompts),
                "total_prompt_length": sum(len(p) for p in prompts),
            },
        )

    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """Log LLM call end with token usage."""
        run_id = kwargs.get("run_id")

        # Extract token usage if available
        token_usage = {}
        if response.llm_output and "token_usage" in response.llm_output:
            token_usage = response.llm_output["token_usage"]

        log_operation(
            "graph_llm_end",
            {
                "run_id": str(run_id) if run_id else None,
                "generations": len(response.generations),
                **token_usage,  # Include token counts if available
            },
        )

    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Log LLM error."""
        run_id = kwargs.get("run_id")

        log_operation(
            "graph_llm_error",
            {
                "run_id": str(run_id) if run_id else None,
                "error": str(error)[:200],
                "error_type": type(error).__name__,
            },
        )

    def _sanitize_dict(self, data: Dict[str, Any], max_depth: int = 2) -> Dict[str, Any]:
        """
        Sanitize dictionary values for logging.

        Args:
            data: Dictionary to sanitize
            max_depth: Maximum nesting depth to preserve

        Returns:
            Sanitized dictionary with truncated strings
        """
        if max_depth <= 0:
            return {"_truncated": "max_depth_reached"}

        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = value[:200] if len(value) > 200 else value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value, max_depth - 1)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = f"<{type(value).__name__} len={len(value)}>"
            elif isinstance(value, (int, float, bool, type(None))):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)[:100]

        return sanitized

    def _flatten_dict(
        self,
        data: Dict[str, Any],
        prefix: str = "",
        separator: str = "_",
    ) -> Dict[str, Any]:
        """
        Flatten nested dictionary into top-level keys.

        Args:
            data: Dictionary to flatten
            prefix: Prefix for flattened keys
            separator: Separator between prefix and key

        Returns:
            Flattened dictionary

        Example:
            >>> _flatten_dict({"a": {"b": 1}}, "input")
            {"input_a_b": 1}
        """
        flattened = {}

        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively flatten nested dicts (limit depth)
                flattened.update(self._flatten_dict(value, new_key, separator))
            else:
                # Keep primitives and convert complex types to strings
                if isinstance(value, (str, int, float, bool, type(None))):
                    flattened[new_key] = value
                else:
                    flattened[new_key] = str(value)[:100]

        return flattened
