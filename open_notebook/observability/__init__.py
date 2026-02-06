"""
Observability module for structured contextual logging and LLM tracing.

This module provides:
- Request context tracking with contextvars (Story 7.2)
- Rolling context buffers for error diagnostics (Story 7.2)
- Structured JSON logging (Story 7.2)
- LangSmith integration for end-to-end LLM tracing (Story 7.4)
- Admin error notifications (Story 7.3)
"""

from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.db_instrumentation import (
    log_db_query,
    log_external_api_call,
    log_graph_invocation,
    log_service_call,
)
from open_notebook.observability.langgraph_context_callback import ContextLoggingCallback
from open_notebook.observability.langsmith_handler import get_langsmith_callback
from open_notebook.observability.notification_service import (
    NotificationPayload,
    get_notification_service,
)
from open_notebook.observability.request_context import (
    context_buffer,
    get_request_context,
    log_operation,
    request_context,
)
from open_notebook.observability.structured_logger import configure_logging, structured_log

__all__ = [
    # Story 7.2: Request context and structured logging
    "get_request_context",
    "log_operation",
    "request_context",
    "context_buffer",
    "RollingContextBuffer",
    "configure_logging",
    "structured_log",
    # Story 7.2: Service/DB instrumentation
    "log_db_query",
    "log_service_call",
    "log_graph_invocation",
    "log_external_api_call",
    # Story 7.2: LangGraph context callback
    "ContextLoggingCallback",
    # Story 7.3: Admin error notifications
    "get_notification_service",
    "NotificationPayload",
    # Story 7.4: LangSmith LLM tracing
    "get_langsmith_callback",
]
