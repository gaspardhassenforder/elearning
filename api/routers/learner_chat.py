"""Learner Chat Router - SSE Streaming Endpoint for AI Teacher Conversations.

Provides Server-Sent Events (SSE) streaming for learner chat interactions with AI teacher.
Implements company-scoped access control and thread isolation per user/notebook.

Story: 4.1 - Learner Chat Interface & SSE Streaming
"""

import asyncio
import json
import time
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from loguru import logger
from pydantic import BaseModel, Field
from typing import Optional

from api.auth import LearnerContext, get_current_learner
from api.learner_chat_service import (
    extract_learner_profile,
    build_intro_message,
    generate_quick_replies,
    get_learner_objectives_with_status,
    get_lesson_steps_with_status,
    init_thread_context,
    validate_learner_access_to_notebook,
)
from open_notebook.graphs.chat import get_async_graph, get_async_memory
from open_notebook.utils import extract_text_from_response
from open_notebook.observability.langsmith_handler import get_langsmith_callback
from open_notebook.observability.langgraph_context_callback import ContextLoggingCallback
from open_notebook.observability.token_tracking_callback import TokenTrackingCallback

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ToolCallData(BaseModel):
    """Tool call with result, for inline artifact rendering on history reload."""

    id: str = Field(..., description="Tool call ID")
    toolName: str = Field(..., description="Name of the tool called")
    args: dict = Field(default_factory=dict, description="Arguments passed to the tool")
    result: Optional[dict] = Field(None, description="Tool result data for frontend rendering")


class ChatHistoryMessage(BaseModel):
    """Single message in chat history."""

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role: 'assistant' or 'user'")
    content: str = Field(..., description="Message content")
    createdAt: str = Field(..., description="ISO 8601 timestamp")
    toolCalls: Optional[list[ToolCallData]] = Field(
        None, description="Tool calls with results for inline artifact rendering"
    )


class ChatHistoryResponse(BaseModel):
    """Response model for chat history endpoint."""

    messages: list[ChatHistoryMessage] = Field(..., description="List of historical messages")
    thread_id: str = Field(..., description="Thread ID for this conversation")
    has_more: bool = Field(default=False, description="Whether more messages available (pagination)")



class LearnerChatRequest(BaseModel):
    """Request body for learner chat message."""

    message: str = Field(default="", description="Learner's message content (empty triggers first-visit greeting)")
    language: str = Field(
        default="en-US",
        description="UI language code (e.g., 'en-US', 'fr-FR') for AI response language"
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


class SSEToolStatusEvent(BaseModel):
    """SSE tool status event for user-facing progress indicators."""

    status: str
    tool_name: str


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


class SSEQuickRepliesEvent(BaseModel):
    """SSE event with LLM-generated contextual quick-reply suggestions."""

    replies: list[str]


# ============================================================================
# Chat Reset Endpoint
# ============================================================================


@router.delete("/chat/learner/{notebook_id}")
async def reset_learner_chat(
    notebook_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Reset learner chat conversation (clear thread checkpoint).

    Clears the thread checkpoint so the learner starts a fresh conversation.
    The frontend uses this when the user clicks "New conversation".

    Args:
        notebook_id: Notebook/module record ID
        learner: Authenticated learner context (auto-injected)

    Returns:
        JSON with status and thread_id

    Raises:
        HTTPException 403: Learner does not have access to notebook
        HTTPException 500: Failed to reset chat
    """
    await validate_learner_access_to_notebook(
        notebook_id=notebook_id, learner_context=learner
    )

    thread_id = f"{learner.user.id}:{notebook_id}"
    logger.info(f"Resetting chat for thread {thread_id}")

    try:
        async_memory = await get_async_memory()
        # Delete checkpoint rows directly from SQLite for this thread
        async with async_memory.lock:
            await async_memory.conn.execute(
                "DELETE FROM checkpoints WHERE thread_id = ?",
                (thread_id,),
            )
            await async_memory.conn.execute(
                "DELETE FROM writes WHERE thread_id = ?",
                (thread_id,),
            )
            await async_memory.conn.commit()
        logger.info(f"Chat reset successfully for thread {thread_id}")
        return {"status": "ok", "thread_id": thread_id}
    except Exception as e:
        logger.error("Failed to reset chat for thread {}: {}", thread_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to reset chat")


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
            "Error validating learner access to notebook {}: {}", notebook_id, str(e)
        )
        raise HTTPException(
            status_code=500, detail="Failed to validate notebook access"
        )

    # 2. Construct thread ID (same pattern as chat endpoint)
    thread_id = f"{learner.user.id}:{notebook_id}"
    logger.debug(f"Loading history for thread_id: {thread_id}")

    # 3. Load checkpoint from SqliteSaver
    try:
        checkpoint_config = {"configurable": {"thread_id": thread_id}}
        async_memory = await get_async_memory()
        checkpoint_tuple = await async_memory.aget(checkpoint_config)

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

        # Filter hidden messages (first-visit intro) BEFORE pagination
        visible_messages = [
            msg for msg in messages
            if not (isinstance(msg, HumanMessage) and getattr(msg, "additional_kwargs", {}).get("hidden", False))
        ]

        # Story 4.8 Task 9: Apply pagination on visible messages
        total_messages = len(visible_messages)
        has_more = (offset + limit) < total_messages

        # Slice messages for pagination (offset from start, limit count)
        paginated_messages = visible_messages[offset:offset + limit]

        logger.info(
            f"Pagination: total={total_messages}, offset={offset}, "
            f"limit={limit}, returning={len(paginated_messages)}, has_more={has_more}"
        )

        # 4. Transform messages to frontend format (assistant-ui compatible)
        # ToolMessages are used to reconstruct tool call results for inline artifacts.
        # The AsyncSqliteSaver checkpoint still stores them for LLM context.
        import uuid
        from datetime import datetime

        formatted_messages = []
        # Buffer of tool calls waiting for their ToolMessage results.
        # Key: tool_call_id, Value: ToolCallData (result=None until ToolMessage matched).
        tool_call_buffer: dict[str, ToolCallData] = {}

        for msg in paginated_messages:
            # ToolMessage: extract result and match to pending tool call in buffer
            if isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, "tool_call_id", None)
                if tool_call_id and tool_call_id in tool_call_buffer:
                    pending = tool_call_buffer[tool_call_id]
                    try:
                        # content_and_artifact tools (e.g. surface_document) store the
                        # frontend-ready dict in .artifact; regular tools store JSON in .content
                        if hasattr(msg, "artifact") and msg.artifact:
                            result = msg.artifact
                        elif pending.toolName == "surface_document":
                            # ToolMessage.artifact may not survive checkpoint serialization.
                            # Reconstruct from tool call args (stored on AIMessage) + DB lookup.
                            source_id = (pending.args or {}).get("source_id")
                            if source_id:
                                try:
                                    import os
                                    from open_notebook.domain.notebook import Source
                                    source = await Source.get(source_id)
                                    if source:
                                        file_type = "document"
                                        if source.asset and source.asset.file_path:
                                            _, ext = os.path.splitext(source.asset.file_path)
                                            file_type = ext.lstrip('.') if ext else "file"
                                        elif source.asset and source.asset.url:
                                            file_type = "url"
                                        result = {
                                            "source_id": source_id,
                                            "title": source.title or "Untitled Document",
                                            "source_type": file_type,
                                            "excerpt": (pending.args or {}).get("excerpt_text", ""),
                                            "relevance": (pending.args or {}).get("relevance_reason", ""),
                                            "page_number": (pending.args or {}).get("page_number"),
                                            "timestamp_seconds": (pending.args or {}).get("timestamp_seconds"),
                                            "asset_url": source.asset.url if source.asset else None,
                                            "asset_file_path": source.asset.file_path if source.asset else None,
                                        }
                                    else:
                                        result = {}
                                except Exception as recon_err:
                                    logger.warning(
                                        "Could not reconstruct surface_document artifact for {}: {}",
                                        source_id, str(recon_err),
                                    )
                                    result = {}
                            else:
                                result = {}
                        elif isinstance(msg.content, str) and msg.content:
                            result = json.loads(msg.content)
                        else:
                            result = {}
                    except (json.JSONDecodeError, TypeError):
                        result = {"content": str(msg.content) if msg.content else ""}
                    tool_call_buffer[tool_call_id] = ToolCallData(
                        id=pending.id,
                        toolName=pending.toolName,
                        args=pending.args,
                        result=result,
                    )
                continue

            # AIMessage with tool_calls: collect stubs into buffer
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    tc_id = tc.get("id") or str(uuid.uuid4())
                    if tc_id not in tool_call_buffer:
                        tool_call_buffer[tc_id] = ToolCallData(
                            id=tc_id,
                            toolName=tc["name"],
                            args=tc.get("args", {}),
                            result=None,
                        )
                # Skip intermediate AIMessages that have only tool_calls (no user-facing text)
                if not msg.content:
                    continue

            try:
                # Determine role
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

                # Attach all completed tool calls to assistant messages, then clear buffer
                tool_calls_for_msg = None
                if role == "assistant" and tool_call_buffer:
                    completed = [tc for tc in tool_call_buffer.values() if tc.result is not None]
                    tool_calls_for_msg = completed if completed else None
                    tool_call_buffer = {}

                formatted_messages.append(
                    ChatHistoryMessage(
                        id=message_id,
                        role=role,
                        content=content,
                        createdAt=created_at,
                        toolCalls=tool_calls_for_msg,
                    )
                )
            except Exception as e:
                # Skip corrupt message but continue processing rest of history
                msg_id = getattr(msg, "id", "unknown")
                logger.warning(
                    "Skipping corrupt message {} in thread {}: {}", msg_id, thread_id, str(e)
                )
                continue

        # Merge consecutive assistant messages (from ReAct multi-turn LLM invocations).
        # During streaming, all text deltas accumulate into one bubble; history must match.
        # Also merge their toolCalls arrays so inline artifacts are preserved.
        merged_messages = []
        for msg in formatted_messages:
            if (merged_messages
                    and msg.role == "assistant"
                    and merged_messages[-1].role == "assistant"):
                prev = merged_messages[-1]
                combined_tool_calls = None
                if prev.toolCalls or msg.toolCalls:
                    combined_tool_calls = (prev.toolCalls or []) + (msg.toolCalls or [])
                merged_messages[-1] = ChatHistoryMessage(
                    id=prev.id,
                    role="assistant",
                    content=(prev.content or "") + (msg.content or ""),
                    createdAt=prev.createdAt,
                    toolCalls=combined_tool_calls,
                )
            else:
                merged_messages.append(msg)

        logger.info(
            f"Loaded {len(merged_messages)} messages for thread {thread_id} "
            f"(page: offset={offset}, limit={limit}, has_more={has_more})"
        )

        return ChatHistoryResponse(
            messages=merged_messages,
            thread_id=thread_id,
            has_more=has_more
        )

    except Exception as e:
        logger.error("Error loading chat history for thread {}: {}", thread_id, str(e), exc_info=True)
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
            "Error validating learner access to notebook {}: {}", notebook_id, str(e)
        )
        raise HTTPException(
            status_code=500, detail="Failed to validate notebook access"
        )

    # 2. Thread-aware context init:
    #    - New thread: run full init (11 queries), build system_prompt once
    #    - Existing thread: run lightweight reconciliation (4 queries), reuse checkpointed system_prompt
    thread_id = f"{learner.user.id}:{notebook_id}"

    try:
        async_memory = await get_async_memory()
        thread_state = await async_memory.aget({"configurable": {"thread_id": thread_id}})

        # Extract channel_values from checkpoint (SqliteSaver returns dict)
        channel_values = {}
        if thread_state:
            if isinstance(thread_state, dict):
                channel_values = thread_state.get("channel_values", {})
            elif hasattr(thread_state, "checkpoint"):
                checkpoint_data = thread_state.checkpoint
                if isinstance(checkpoint_data, dict):
                    channel_values = checkpoint_data.get("channel_values", {})

        is_new_thread = not channel_values or not channel_values.get("system_prompt")
        existing_messages = channel_values.get("messages", [])
        is_first_visit = not existing_messages

    except Exception as e:
        logger.warning("Could not read thread checkpoint, treating as new thread: {}", str(e))
        is_new_thread = True
        is_first_visit = True

    try:
        if is_new_thread:
            # Full init — build system prompt once (runs all context queries)
            system_prompt, learner_profile_dict, objectives, lesson_steps = await init_thread_context(
                notebook_id=notebook_id, learner=learner, language=request.language
            )
            logger.info(
                f"New thread: system prompt built ({len(system_prompt)} chars) for notebook {notebook_id}"
            )
        else:
            # Lightweight reconciliation — refresh progress status only (4 queries)
            # system_prompt lives in checkpoint and will be reused by the graph
            system_prompt = None
            learner_profile_dict = extract_learner_profile(learner)
            objectives, (lesson_steps, _) = await asyncio.gather(
                get_learner_objectives_with_status(notebook_id, learner.user.id),
                get_lesson_steps_with_status(notebook_id, learner.user.id),
            )
            logger.info(
                f"Existing thread: reconciled {len(objectives)} objectives, {len(lesson_steps)} steps for notebook {notebook_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error preparing chat context for notebook {}: {}", notebook_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to prepare chat context")

    # 3. Define SSE event generator
    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events from LangGraph streaming output.

        Translates LangGraph events to assistant-ui SSE protocol format.
        Includes first-visit proactive greeting detection and generation.
        """
        try:
            logger.info(f"Using thread_id: {thread_id}")

            # Determine user message for this turn.
            # First visit + empty message: inject hidden intro to trigger natural greeting.
            # Returning user + empty message: nothing to do (history loaded via /history).
            # Normal turn: use request.message.
            if is_first_visit and not request.message.strip():
                intro_text = build_intro_message(learner_profile_dict, request.language)
                user_message = HumanMessage(content=intro_text, additional_kwargs={"hidden": True})
                logger.info(f"First visit: injecting hidden intro message for thread {thread_id}")
            elif not request.message.strip():
                logger.info(f"Returning user with empty message on thread {thread_id} — no action")
                return
            else:
                user_message = HumanMessage(content=request.message)

            # Create LangSmith callback for tracing (or None if not configured)
            langsmith_callback = get_langsmith_callback(
                user_id=learner.user.id,
                company_id=learner.company_id,
                notebook_id=notebook_id,
                workflow_name="learner_chat",
                run_name=f"chat:{thread_id}",
            )

            # Add context logging callback for error diagnostics
            context_callback = ContextLoggingCallback()

            # Add token tracking callback for usage monitoring
            token_callback = TokenTrackingCallback(
                user_id=learner.user.id,
                company_id=learner.company_id,
                notebook_id=notebook_id,
                operation_type="chat",
            )

            callbacks = [context_callback, token_callback]
            if langsmith_callback:
                callbacks.append(langsmith_callback)

            # Human-readable status messages for tool_status SSE events
            _TOOL_STATUS_MAP = {
                "search_knowledge_base": "Searching knowledge base...",
                "surface_document": "Loading document...",
                "surface_quiz": "Loading quiz...",
                "surface_podcast": "Loading podcast...",
                "generate_artifact": "Generating content...",
            }

            # Collect AI response text for quick_replies generation
            collected_ai_text: list[str] = []

            # Heartbeat: track time of last SSE event to prevent proxy timeouts
            last_event_time = time.monotonic()

            # Build initial state — pass system_prompt only for new threads
            # (existing threads reuse the system_prompt stored in the checkpoint)
            initial_state = {
                "messages": [user_message],
                "objectives": objectives,
                "lesson_steps": lesson_steps,
                "user_id": learner.user.id,
            }
            if is_new_thread and system_prompt:
                initial_state["system_prompt"] = system_prompt

            # Stream events from chat graph
            # ReAct loop: agent -> tools -> agent -> ... (up to MAX_TOOL_ITERATIONS)
            async_graph = await get_async_graph()
            async for event in async_graph.astream_events(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "user_id": learner.user.id,
                        "notebook_id": notebook_id,
                        "company_id": learner.company_id,
                    },
                    "callbacks": callbacks,
                },
                version="v2",
            ):
                event_type = event.get("event")

                # Text chunk from LLM (fires multiple times in ReAct loop)
                if event_type == "on_chat_model_stream":
                    chunk_data = event.get("data", {})
                    chunk = chunk_data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        text_content = extract_text_from_response(chunk.content)
                        if text_content:
                            collected_ai_text.append(text_content)
                            text_event = SSETextEvent(delta=text_content)
                            yield f"event: text\ndata: {text_event.model_dump_json()}\n\n"
                            last_event_time = time.monotonic()

                # Tool call start — emit tool_call + tool_status events
                elif event_type == "on_tool_start":
                    tool_data = event.get("data", {})
                    tool_name = event.get("name", "unknown")
                    tool_input = tool_data.get("input", {})
                    tool_run_id = event.get("run_id", f"call_{event.get('name', 'unknown')}")

                    tool_call_event = SSEToolCallEvent(
                        id=tool_run_id, toolName=tool_name, args=tool_input
                    )
                    yield f"event: tool_call\ndata: {tool_call_event.model_dump_json()}\n\n"

                    status_text = _TOOL_STATUS_MAP.get(tool_name)
                    if status_text:
                        status_event = SSEToolStatusEvent(
                            status=status_text, tool_name=tool_name
                        )
                        yield f"event: tool_status\ndata: {status_event.model_dump_json()}\n\n"
                    last_event_time = time.monotonic()

                # Tool call end (result) — handle content_and_artifact tools
                elif event_type == "on_tool_end":
                    tool_output = event.get("data", {}).get("output")
                    tool_run_id = event.get("run_id", "call_result")
                    tool_name = event.get("name", "")

                    # For content_and_artifact tools (surface_document), extract artifact for frontend
                    if hasattr(tool_output, "artifact") and tool_output.artifact:
                        result_for_frontend = tool_output.artifact
                    elif hasattr(tool_output, "content"):
                        try:
                            result_for_frontend = json.loads(tool_output.content) if isinstance(tool_output.content, str) else tool_output.content
                        except (json.JSONDecodeError, TypeError):
                            result_for_frontend = {"content": str(tool_output.content) if tool_output.content else ""}
                    elif isinstance(tool_output, dict):
                        result_for_frontend = tool_output
                    else:
                        result_for_frontend = {"content": str(tool_output) if tool_output else ""}

                    if isinstance(result_for_frontend, list):
                        result_for_frontend = {"items": result_for_frontend}

                    tool_result_event = SSEToolResultEvent(
                        id=tool_run_id, result=result_for_frontend
                    )
                    yield f"event: tool_result\ndata: {tool_result_event.model_dump_json()}\n\n"
                    last_event_time = time.monotonic()

                # Custom stream events from get_stream_writer() in tools
                elif event_type == "on_custom_event":
                    custom_data = event.get("data", {})
                    if custom_data.get("type") == "tool_progress":
                        status_event = SSEToolStatusEvent(
                            status=custom_data.get("status", ""),
                            tool_name=custom_data.get("tool", ""),
                        )
                        yield f"event: tool_status\ndata: {status_event.model_dump_json()}\n\n"
                        last_event_time = time.monotonic()

                # Heartbeat: prevent proxy/connection timeouts during long tool calls
                if time.monotonic() - last_event_time > 10:
                    yield ": heartbeat\n\n"
                    last_event_time = time.monotonic()

            # Emit message_complete so frontend can re-enable input
            message_complete_event = SSEMessageCompleteEvent(
                messageId=f"msg_{thread_id}_{len(request.message)}",
                metadata={"thread_id": thread_id, "notebook_id": notebook_id},
            )
            yield f"event: message_complete\ndata: {message_complete_event.model_dump_json()}\n\n"

            # Generate quick replies in background and emit when ready
            ai_response_text = "".join(collected_ai_text)
            quick_replies_task = asyncio.create_task(
                generate_quick_replies(
                    user_message=request.message if request.message.strip() else ai_response_text,
                    ai_response=ai_response_text,
                    language=request.language,
                )
            )
            # Wait briefly for quick replies (up to 15s)
            try:
                replies = await asyncio.wait_for(quick_replies_task, timeout=15.0)
                if replies:
                    quick_replies_event = SSEQuickRepliesEvent(replies=replies)
                    yield f"event: quick_replies\ndata: {quick_replies_event.model_dump_json()}\n\n"
            except asyncio.TimeoutError:
                quick_replies_task.cancel()
                logger.warning("Quick replies timed out for thread {}", thread_id)
            except Exception as e:
                logger.warning("Quick replies failed for thread {}: {}", thread_id, str(e))

        except Exception as e:
            # Stream error event to frontend
            logger.error("Error during SSE streaming for notebook {}: {}", notebook_id, str(e), exc_info=True)
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
