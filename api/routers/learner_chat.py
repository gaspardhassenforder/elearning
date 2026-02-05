"""Learner Chat Router - SSE Streaming Endpoint for AI Teacher Conversations.

Provides Server-Sent Events (SSE) streaming for learner chat interactions with AI teacher.
Implements company-scoped access control and thread isolation per user/notebook.

Story: 4.1 - Learner Chat Interface & SSE Streaming
"""

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import LearnerContext, get_current_learner
from api.learner_chat_service import (
    prepare_chat_context,
    validate_learner_access_to_notebook,
)
from open_notebook.graphs.chat import graph as chat_graph

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class LearnerChatRequest(BaseModel):
    """Request body for learner chat message."""

    message: str = Field(..., min_length=1, description="Learner's message content")


class SSETextEvent(BaseModel):
    """SSE text delta event (assistant-ui protocol)."""

    delta: str = Field(..., description="Text chunk")


class SSEToolCallEvent(BaseModel):
    """SSE tool call event (assistant-ui protocol)."""

    id: str
    toolName: str
    args: dict


class SSEToolResultEvent(BaseModel):
    """SSE tool result event (assistant-ui protocol)."""

    id: str
    result: dict


class SSEMessageCompleteEvent(BaseModel):
    """SSE message complete event (assistant-ui protocol)."""

    messageId: str
    metadata: dict


# ============================================================================
# SSE Streaming Endpoint
# ============================================================================


@router.post("/chat/learner/{notebook_id}")
async def stream_learner_chat(
    notebook_id: str,
    request: LearnerChatRequest,
    learner: LearnerContext = Depends(get_current_learner),
) -> StreamingResponse:
    """Stream AI teacher response via SSE for learner chat.

    Implements:
    - Company-scoped access control (learner can only access assigned modules)
    - Thread isolation per user/notebook (prevents cross-contamination)
    - SSE protocol compatible with assistant-ui React library
    - Two-layer prompt system (global + per-module from Story 3.4)
    - Graceful error handling (AI continues on tool failure)

    Args:
        notebook_id: Notebook/module record ID
        request: Chat request with learner message
        learner: Authenticated learner context (auto-injected)

    Returns:
        StreamingResponse with text/event-stream content type

    Raises:
        HTTPException 403: Learner does not have access to notebook
        HTTPException 404: Notebook not found
        HTTPException 500: Internal error during chat processing
    """
    logger.info(
        f"Learner chat request from user {learner.user.id} for notebook {notebook_id}"
    )

    try:
        # 1. Validate learner has access to this notebook
        # (published + assigned to learner's company + not locked)
        await validate_learner_access_to_notebook(
            notebook_id=notebook_id, learner_context=learner
        )

    except HTTPException:
        # Re-raise HTTP exceptions (403/404) from validation
        raise
    except Exception as e:
        logger.error(
            f"Error validating learner access to notebook {notebook_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to validate notebook access"
        )

    # 2. Prepare chat context (system prompt, learner profile, objectives)
    try:
        system_prompt, learner_profile_dict = await prepare_chat_context(
            notebook_id=notebook_id, learner=learner
        )
        logger.debug(
            f"System prompt prepared ({len(system_prompt)} chars) for notebook {notebook_id}"
        )
    except Exception as e:
        logger.error(f"Error preparing chat context for notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to prepare chat context")

    # 3. Define SSE event generator
    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events from LangGraph streaming output.

        Translates LangGraph events to assistant-ui SSE protocol format.
        """
        try:
            # Thread ID pattern: user:{user_id}:notebook:{notebook_id}
            thread_id = f"user:{learner.user.id}:notebook:{notebook_id}"
            logger.info(f"Using thread_id: {thread_id}")

            # Prepare user message
            user_message = HumanMessage(content=request.message)

            # Stream events from chat graph with assembled system prompt
            async for event in chat_graph.astream_events(
                {
                    "messages": [user_message],
                    "notebook": None,  # Will be loaded by graph if needed
                    "context": None,  # RAG context built by graph
                    "context_config": None,
                    "model_override": None,  # Use default model
                    "system_prompt_override": system_prompt,  # Story 4.1: Use assembled prompt
                },
                config={"configurable": {"thread_id": thread_id}},
                version="v2",
            ):
                event_type = event.get("event")

                # Text chunk from LLM
                if event_type == "on_chat_model_stream":
                    chunk_data = event.get("data", {})
                    chunk = chunk_data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        text_event = SSETextEvent(delta=chunk.content)
                        yield f"event: text\ndata: {text_event.model_dump_json()}\n\n"

                # Tool call start
                elif event_type == "on_tool_start":
                    tool_data = event.get("data", {})
                    tool_name = tool_data.get("name", "unknown")
                    tool_input = tool_data.get("input", {})
                    tool_run_id = event.get("run_id", f"call_{event.get('name', 'unknown')}")

                    tool_call_event = SSEToolCallEvent(
                        id=tool_run_id, toolName=tool_name, args=tool_input
                    )
                    yield f"event: tool_call\ndata: {tool_call_event.model_dump_json()}\n\n"

                # Tool call end (result)
                elif event_type == "on_tool_end":
                    tool_result = event.get("data", {}).get("output", {})
                    tool_run_id = event.get("run_id", "call_result")

                    tool_result_event = SSEToolResultEvent(
                        id=tool_run_id, result={"output": tool_result}
                    )
                    yield f"event: tool_result\ndata: {tool_result_event.model_dump_json()}\n\n"

            # Message complete event
            message_complete_event = SSEMessageCompleteEvent(
                messageId=f"msg_{thread_id}_{len(request.message)}",
                metadata={"thread_id": thread_id, "notebook_id": notebook_id},
            )
            yield f"event: message_complete\ndata: {message_complete_event.model_dump_json()}\n\n"

        except Exception as e:
            # Stream error event to frontend
            # Log full error details but don't leak to client
            logger.error(f"Error during SSE streaming for notebook {notebook_id}: {e}", exc_info=True)
            error_event = {
                "error": "An error occurred while streaming the response",
                "detail": "Please try again. If the problem persists, contact support.",
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

    # 4. Return streaming response with SSE headers
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
            "Connection": "keep-alive",
        },
    )
