"""
Database instrumentation for context logging.

Wraps database operations to automatically log queries to the rolling
context buffer with timing and result information.
"""

import time
from typing import Any, Dict, List, Optional

from open_notebook.observability.request_context import log_operation


def log_db_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    result_count: Optional[int] = None,
    duration_ms: Optional[float] = None,
):
    """
    Log database query to context buffer.

    Args:
        query: SQL/SurrealQL query string
        params: Query parameters (will be sanitized)
        result_count: Number of results returned
        duration_ms: Query execution time in milliseconds

    Note:
        Automatically truncates long queries to 500 characters.
    """
    # Truncate long queries
    query_snippet = query[:500] if len(query) > 500 else query

    # Flatten params into detail fields (to avoid nested dict → string conversion)
    details = {
        "query": query_snippet,
        "result_count": result_count,
    }

    # Add flattened params with "param_" prefix
    if params:
        sensitive_keys = {"password", "token", "secret", "key", "credential"}
        for key, value in params.items():
            param_key = f"param_{key}"
            if any(k in key.lower() for k in sensitive_keys):
                details[param_key] = "***REDACTED***"
            else:
                # Keep primitives, convert complex types
                if isinstance(value, (str, int, float, bool, type(None))):
                    details[param_key] = value
                else:
                    details[param_key] = str(value)[:100]

    log_operation("db_query", details, duration_ms=duration_ms)


async def instrumented_query(db, query: str, params: Optional[Dict] = None) -> Any:
    """
    Execute database query with instrumentation.

    Args:
        db: Database connection
        query: Query string
        params: Query parameters

    Returns:
        Query results

    Note:
        This is a helper function. For full instrumentation, use the
        context manager approach in your repository functions.
    """
    start_time = time.time()

    try:
        result = await db.query(query, params or {})
        duration_ms = (time.time() - start_time) * 1000

        # Get result count
        result_count = len(result) if isinstance(result, list) else (1 if result else 0)

        log_db_query(query, params, result_count, duration_ms)

        return result

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_operation(
            "db_query_error",
            {
                "query": query[:500],
                "params": params,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            duration_ms=duration_ms,
        )
        raise


def log_service_call(service: str, operation: str, **details):
    """
    Log service operation to context buffer.

    Args:
        service: Service name (e.g., "learner_chat", "notebook")
        operation: Operation name (e.g., "send_message", "create")
        **details: Additional operation details

    Example:
        >>> log_service_call("learner_chat", "send_message",
        ...                  notebook_id="notebook:123", message_length=150)
    """
    log_operation(
        "service_call",
        {
            "service": service,
            "operation": operation,
            **details,
        },
    )


def log_graph_invocation(graph_name: str, inputs: Dict[str, Any], **details):
    """
    Log LangGraph invocation to context buffer.

    Args:
        graph_name: Name of the graph (e.g., "chat", "source", "ask")
        inputs: Input parameters to the graph
        **details: Additional details

    Example:
        >>> log_graph_invocation("chat", {"message": "Hello"},
        ...                      notebook_id="notebook:123")
    """
    # Flatten inputs into detail fields (to avoid nested dict → string conversion)
    log_details = {
        "graph": graph_name,
        **details,
    }

    # Add flattened inputs with "input_" prefix
    for key, value in inputs.items():
        input_key = f"input_{key}"
        if isinstance(value, str):
            log_details[input_key] = value[:200] if len(value) > 200 else value
        elif isinstance(value, (int, float, bool, type(None))):
            log_details[input_key] = value
        else:
            log_details[input_key] = str(value)[:100]

    log_operation("graph_invocation", log_details)


def log_external_api_call(
    provider: str,
    operation: str,
    duration_ms: Optional[float] = None,
    **details,
):
    """
    Log external API call to context buffer.

    Args:
        provider: API provider (e.g., "openai", "anthropic", "surrealdb")
        operation: Operation type (e.g., "chat_completion", "embedding")
        duration_ms: Request duration in milliseconds
        **details: Additional details (token_count, model, etc.)

    Example:
        >>> log_external_api_call("openai", "chat_completion",
        ...                       duration_ms=1250.5,
        ...                       model="gpt-4", tokens=150)
    """
    log_operation(
        "external_api_call",
        {
            "provider": provider,
            "operation": operation,
            **details,
        },
        duration_ms=duration_ms,
    )
