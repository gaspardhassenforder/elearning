"""Learner Chat Router - SSE Streaming Endpoint for AI Teacher Conversations.

Provides Server-Sent Events (SSE) streaming for learner chat interactions with AI teacher.
Implements company-scoped access control and thread isolation per user/notebook.

Story: 4.1 - Learner Chat Interface & SSE Streaming
"""

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import LearnerContext, get_current_learner
from api.learner_chat_service import (
    generate_proactive_greeting,
    prepare_chat_context,
    validate_learner_access_to_notebook,
)
from open_notebook.graphs.prompt import generate_re_engagement_greeting
from open_notebook.graphs.chat import graph as chat_graph, memory as chat_memory

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ChatHistoryMessage(BaseModel):
    """Single message in chat history."""

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role: 'assistant' or 'user'")
    content: str = Field(..., description="Message content")
    createdAt: str = Field(..., description="ISO 8601 timestamp")


class ChatHistoryResponse(BaseModel):
    """Response model for chat history endpoint."""

    messages: list[ChatHistoryMessage] = Field(..., description="List of historical messages")
    thread_id: str = Field(..., description="Thread ID for this conversation")
    has_more: bool = Field(default=False, description="Whether more messages available (pagination)")



class LearnerChatRequest(BaseModel):
    """Request body for learner chat message."""

    message: str = Field(default="", description="Learner's message content (empty for greeting-only request)")
    request_greeting_only: bool = Field(
        default=False,
        description="Story 4.2: If true, only return greeting without processing message"
    )


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


class SSEObjectiveCheckedEvent(BaseModel):
    """SSE event emitted when AI checks off a learning objective (Story 4.4)."""

    objective_id: str
    objective_text: str
    evidence: str
    total_completed: int
    total_objectives: int
    all_complete: bool


# ============================================================================
# Chat History Endpoint (Story 4.8)
# ============================================================================


@router.get("/chat/learner/{notebook_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    notebook_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip from start"),
    learner: LearnerContext = Depends(get_current_learner),
) -> ChatHistoryResponse:
    """Load chat history for learner's conversation in this module.

    Story 4.8: Persistent chat history endpoint.
    Returns previous messages from the thread checkpoint for this
    user/notebook combination. Used by frontend to initialize Thread component
    with historical messages on page load.

    Pagination: Returns `limit` messages starting from `offset`. Use `has_more`
    flag to determine if more messages exist.

    Args:
        notebook_id: Notebook/module record ID
        limit: Maximum number of messages to return (default: 50, max: 100)
        offset: Number of messages to skip from start (default: 0)
        learner: Authenticated learner context (auto-injected)

    Returns:
        ChatHistoryResponse with messages array, thread ID, and has_more flag

    Raises:
        HTTPException 403: Learner does not have access to notebook
        HTTPException 404: Notebook not found
    """
    logger.info(
        f"Loading chat history for user {learner.user.id} in notebook {notebook_id}"
    )

    try:
        # 1. Validate learner has access to this notebook
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

    # 2. Construct thread ID (same pattern as chat endpoint)
    thread_id = f"user:{learner.user.id}:notebook:{notebook_id}"
    logger.debug(f"Loading history for thread_id: {thread_id}")

    # 3. Load checkpoint from SqliteSaver
    try:
        checkpoint_config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = chat_memory.get(checkpoint_config)

        if not checkpoint_tuple:
            logger.info(f"No history found for thread {thread_id} (first visit)")
            return ChatHistoryResponse(
                messages=[],
                thread_id=thread_id,
                has_more=False
            )

        # Extract messages from checkpoint (SqliteSaver returns dict directly)
        if not isinstance(checkpoint_tuple, dict):
            logger.error(f"Unexpected checkpoint type: {type(checkpoint_tuple)}")
            raise HTTPException(
                status_code=500, detail="Internal error: invalid checkpoint format"
            )

        # SqliteSaver structure: {"channel_values": {"messages": [...]}}
        messages = []
        if "channel_values" in checkpoint_tuple and "messages" in checkpoint_tuple["channel_values"]:
            messages = checkpoint_tuple["channel_values"]["messages"]
        elif "messages" in checkpoint_tuple:
            # Fallback: direct messages key (shouldn't happen with current SqliteSaver)
            messages = checkpoint_tuple["messages"]

        if not messages:
            logger.info(f"Empty message history for thread {thread_id}")
            return ChatHistoryResponse(
                messages=[],
                thread_id=thread_id,
                has_more=False
            )

        # Story 4.8 Task 9: Apply pagination
        total_messages = len(messages)
        has_more = (offset + limit) < total_messages

        # Slice messages for pagination (offset from start, limit count)
        paginated_messages = messages[offset:offset + limit]

        logger.info(
            f"Pagination: total={total_messages}, offset={offset}, "
            f"limit={limit}, returning={len(paginated_messages)}, has_more={has_more}"
        )

        # 4. Transform messages to frontend format (assistant-ui compatible)
        import uuid
        from datetime import datetime

        formatted_messages = []
        for msg in paginated_messages:
            try:
                # Determine role
                from langchain_core.messages import AIMessage

                role = "assistant" if isinstance(msg, AIMessage) else "user"

                # Extract content (handle structured content)
                content = msg.content
                if isinstance(content, list):
                    # Structured content: extract text from blocks
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            text_parts.append(item["text"])
                    content = "\n".join(text_parts) if text_parts else str(content)
                elif not isinstance(content, str):
                    content = str(content)

                # Create message ID if not present
                message_id = getattr(msg, "id", None) or str(uuid.uuid4())

                # Extract timestamp
                created_at = getattr(msg, "additional_kwargs", {}).get(
                    "timestamp", datetime.now().isoformat()
                )
                if not isinstance(created_at, str):
                    created_at = datetime.now().isoformat()

                formatted_messages.append(
                    ChatHistoryMessage(
                        id=message_id,
                        role=role,
                        content=content,
                        createdAt=created_at,
                    )
                )
            except Exception as e:
                # Skip corrupt message but continue processing rest of history
                msg_id = getattr(msg, "id", "unknown")
                logger.warning(
                    f"Skipping corrupt message {msg_id} in thread {thread_id}: {e}"
                )
                continue

        logger.info(
            f"Loaded {len(formatted_messages)} messages for thread {thread_id} "
            f"(page: offset={offset}, limit={limit}, has_more={has_more})"
        )

        return ChatHistoryResponse(
            messages=formatted_messages,
            thread_id=thread_id,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Error loading chat history for thread {thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to load chat history"
        )


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
        notebook = await validate_learner_access_to_notebook(
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
        Story 4.2: Includes first-visit proactive greeting detection and generation.
        """
        try:
            # Thread ID pattern: user:{user_id}:notebook:{notebook_id}
            thread_id = f"user:{learner.user.id}:notebook:{notebook_id}"
            logger.info(f"Using thread_id: {thread_id}")

            # Story 4.2 + 4.8: Check if this is first visit or returning user
            is_first_visit = False
            is_returning_user = False
            try:
                # Get thread state from checkpoint
                thread_state = chat_memory.get({"configurable": {"thread_id": thread_id}})

                # Extract messages from checkpoint (handle dict structure from SqliteSaver)
                messages = []
                if thread_state:
                    if isinstance(thread_state, dict):
                        # SqliteSaver returns dict
                        if "channel_values" in thread_state and "messages" in thread_state["channel_values"]:
                            messages = thread_state["channel_values"]["messages"]
                        elif "messages" in thread_state:
                            messages = thread_state["messages"]
                    elif hasattr(thread_state, "checkpoint"):
                        # CheckpointTuple object
                        checkpoint_data = thread_state.checkpoint
                        if isinstance(checkpoint_data, dict) and "channel_values" in checkpoint_data:
                            messages = checkpoint_data["channel_values"].get("messages", [])

                # Determine user status
                if not thread_state or not messages:
                    is_first_visit = True
                    logger.info(f"First visit detected for thread {thread_id}")
                else:
                    is_returning_user = True
                    logger.info(f"Returning user detected for thread {thread_id} ({len(messages)} messages in history)")
            except Exception as e:
                logger.warning(f"Could not check thread state, assuming first visit: {e}")
                is_first_visit = True

            # Story 4.2 + 4.8: Generate and stream greeting (proactive or re-engagement)
            # Greeting is sent BEFORE processing user's first message
            if is_first_visit or is_returning_user:
                greeting_type = "re-engagement" if is_returning_user else "proactive"
                logger.info(f"Generating {greeting_type} greeting...")
                try:
                    if is_returning_user:
                        # Story 4.8: Re-engagement greeting for returning users
                        # Get learning objectives with status for progress context
                        from open_notebook.domain.learning_objective import LearningObjective
                        objectives = await LearningObjective.get_by_notebook(notebook_id)
                        objectives_with_status = [
                            {
                                "id": str(obj.id),
                                "text": obj.text,
                                "status": obj.status if hasattr(obj, "status") else "not_started"
                            }
                            for obj in objectives
                        ]

                        greeting = await generate_re_engagement_greeting(
                            thread_id=thread_id,
                            learner_profile=learner_profile_dict,
                            objectives_with_status=objectives_with_status,
                            notebook_id=notebook_id,
                        )
                    else:
                        # Story 4.2: Proactive greeting for first-time visitors
                        greeting = await generate_proactive_greeting(
                            notebook_id=notebook_id,
                            learner_profile=learner_profile_dict,
                            notebook=notebook,
                        )

                    # Stream greeting token-by-token for smooth UX
                    # Split into words for token-like streaming effect
                    words = greeting.split()
                    for word in words:
                        text_event = SSETextEvent(delta=word + " ")
                        yield f"event: text\ndata: {text_event.model_dump_json()}\n\n"

                    # Send message complete for greeting
                    greeting_complete_event = SSEMessageCompleteEvent(
                        messageId=f"greeting_{thread_id}",
                        metadata={
                            "thread_id": thread_id,
                            "notebook_id": notebook_id,
                            "type": greeting_type + "_greeting",  # "proactive_greeting" or "re-engagement_greeting"
                            "is_returning_user": is_returning_user,
                        },
                    )
                    yield f"event: message_complete\ndata: {greeting_complete_event.model_dump_json()}\n\n"

                    logger.info(f"{greeting_type.capitalize()} greeting sent successfully")

                except Exception as e:
                    logger.error(f"Failed to generate {greeting_type} greeting: {e}")
                    # Continue with normal chat flow if greeting fails

            # Story 4.2 + 4.8: If greeting-only request, return after sending greeting
            if request.request_greeting_only or ((is_first_visit or is_returning_user) and not request.message.strip()):
                logger.info("Greeting-only request completed")
                return

            # Prepare user message (skip if empty)
            if not request.message.strip():
                logger.warning("Empty message received, skipping graph invocation")
                return

            user_message = HumanMessage(content=request.message)

            # Stream events from chat graph with assembled system prompt
            # Story 4.4: Pass user_id for objective progress tracking
            async for event in chat_graph.astream_events(
                {
                    "messages": [user_message],
                    "notebook": None,  # Will be loaded by graph if needed
                    "context": None,  # RAG context built by graph
                    "context_config": None,
                    "model_override": None,  # Use default model
                    "system_prompt_override": system_prompt,  # Story 4.1: Use assembled prompt
                    "user_id": learner.user.id,  # Story 4.4: For check_off_objective tool
                },
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "user_id": learner.user.id,  # Story 4.4: Pass to tools
                    }
                },
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
                    tool_name = event.get("name", "")

                    tool_result_event = SSEToolResultEvent(
                        id=tool_run_id, result={"output": tool_result}
                    )
                    yield f"event: tool_result\ndata: {tool_result_event.model_dump_json()}\n\n"

                    # Story 4.4: Emit objective_checked event when check_off_objective completes
                    if tool_name == "check_off_objective" and isinstance(tool_result, dict):
                        # Only emit if successful (no error key)
                        if "error" not in tool_result and "objective_id" in tool_result:
                            objective_event = SSEObjectiveCheckedEvent(
                                objective_id=tool_result.get("objective_id", ""),
                                objective_text=tool_result.get("objective_text", ""),
                                evidence=tool_result.get("evidence", ""),
                                total_completed=tool_result.get("total_completed", 0),
                                total_objectives=tool_result.get("total_objectives", 0),
                                all_complete=tool_result.get("all_complete", False),
                            )
                            yield f"event: objective_checked\ndata: {objective_event.model_dump_json()}\n\n"
                            logger.info(
                                f"Emitted objective_checked event: {tool_result.get('total_completed')}/{tool_result.get('total_objectives')}"
                            )

            # Message complete event
            message_complete_event = SSEMessageCompleteEvent(
                messageId=f"msg_{thread_id}_{len(request.message)}",
                metadata={"thread_id": thread_id, "notebook_id": notebook_id},
            )
            yield f"event: message_complete\ndata: {message_complete_event.model_dump_json()}\n\n"

        except Exception as e:
            # Story 7.1: Stream error event to frontend
            # Log full error details but don't leak technical info to client
            logger.error(f"Error during SSE streaming for notebook {notebook_id}: {e}", exc_info=True)
            error_event = {
                "error": "I had trouble processing that",
                "error_type": "service_error",
                "recoverable": True,
                "message": "I had trouble processing that. Let me try again if you'd like to rephrase your question.",
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
