import contextvars
import os
import re
import time
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.config import DATA_FOLDER
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.podcasts.models import EpisodeProfile, PodcastEpisode, SpeakerProfile

try:
    from podcast_creator import configure, create_podcast
    import podcast_creator.core as podcast_core
    import podcast_creator.nodes as podcast_nodes
except ImportError as e:
    logger.error("Failed to import podcast_creator: {}", str(e))
    raise ValueError("podcast_creator library not available")

# Compile regex pattern once for better performance - handles both <think> and variations
THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)


def _extract_text_from_content(content: Any) -> str:
    """
    Extract text content from various LLM response formats.
    
    Handles:
    - Plain strings
    - Lists of content blocks (e.g., [{'type': 'text', 'text': '...'}])
    - Other types (converted via str())
    
    This fixes an issue where some providers (like Google Gemini) return
    content as a list of content blocks instead of a plain string.
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Extract text from content blocks (e.g., [{'type': 'text', 'text': '...'}])
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        return '\n'.join(text_parts)
    else:
        return str(content)


def _strip_thinking_tags_and_extract_json(content: str) -> str:
    """
    Strip <think> tags from content and extract JSON.
    
    This handles the case where some models (like Gemini with extended thinking)
    put their entire response including JSON inside <think> tags, or have
    thinking content followed by JSON.
    
    Strategies:
    1. If content has <think> tags, try to find JSON after removing them
    2. If removing tags leaves empty content, try to extract JSON from inside the tags
    3. Look for JSON patterns (starting with { or [) anywhere in the content
    """
    if not isinstance(content, str):
        return str(content) if content is not None else ""
    
    original_content = content

    # Handle unclosed <think> tags (e.g. DeepSeek/Qwen output <think> without </think>)
    if '<think>' in content.lower() and '</think>' not in content.lower():
        stripped = re.sub(r'<think>', '', content, flags=re.IGNORECASE).strip()
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', stripped)
        if json_match:
            logger.warning("Found JSON after removing unclosed <think> tag")
            return json_match.group(1)
        logger.warning("Model produced only thinking content (unclosed <think>), no JSON")
        return stripped

    # First, try standard cleaning - remove <think> blocks
    thinking_matches = THINK_PATTERN.findall(content)
    cleaned_content = THINK_PATTERN.sub("", content).strip()
    
    # Clean up extra whitespace
    cleaned_content = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_content).strip()
    
    # If we have content after cleaning, return it
    if cleaned_content:
        # Try to find JSON in cleaned content
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned_content)
        if json_match:
            return json_match.group(1)
        return cleaned_content
    
    # If cleaned content is empty but we had thinking content,
    # the JSON might be INSIDE the <think> tags
    if thinking_matches:
        for thinking_content in thinking_matches:
            # Look for JSON inside thinking content
            json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', thinking_content)
            if json_match:
                logger.warning(
                    "Found JSON inside <think> tags - model may have put entire response in thinking block"
                )
                return json_match.group(1)
    
    # Last resort: try to find JSON anywhere in original content
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', original_content)
    if json_match:
        logger.warning("Extracted JSON from content using pattern matching")
        return json_match.group(1)
    
    # Return whatever we have
    return cleaned_content or original_content


# Store the original function from core module
_original_clean_thinking_content = podcast_core.clean_thinking_content


def _patched_clean_thinking_content(content: Any) -> str:
    """
    Patched version of clean_thinking_content that handles:
    1. Content blocks from Gemini (list of {'type': 'text', 'text': '...'})
    2. Extended thinking where JSON is inside <think> tags
    3. Standard <think> tag removal
    
    First extracts text from content blocks (if present), then applies
    robust JSON extraction that handles edge cases.
    """
    # First extract text from content blocks if needed
    extracted = _extract_text_from_content(content)
    
    # Then apply robust cleaning that handles JSON inside <think> tags
    result = _strip_thinking_tags_and_extract_json(extracted)
    
    logger.debug(f"Patched clean_thinking_content: input type={type(content).__name__}, output length={len(result)}")
    
    return result


# Apply the monkey-patch to BOTH modules - core and nodes
# The nodes module imports clean_thinking_content directly, so we must patch there too
podcast_core.clean_thinking_content = _patched_clean_thinking_content
podcast_nodes.clean_thinking_content = _patched_clean_thinking_content
logger.info("Applied podcast-creator content block handling patch to core and nodes modules")


def _fix_speaker_names_in_transcript(transcript_data: dict, valid_speakers: list[str]) -> dict:
    """
    Fix invalid speaker names in transcript by mapping them to valid speakers.

    This handles the case where LLMs generate dialogue with generic speaker names
    like "Host", "Interviewer", or "Guest" instead of using the configured names.

    For single-speaker profiles, any invalid name is mapped to the single valid speaker.
    For multi-speaker profiles:
      - Common host/interviewer names map to the first speaker
      - Common guest names map to the second speaker
      - Partial matches (substring of a valid name) map to that speaker
      - Consistent unknown names are tracked so the same invented name always maps
        to the same valid speaker, preserving conversational turns

    Args:
        transcript_data: The transcript dict with 'transcript' key containing dialogue list
        valid_speakers: List of valid speaker names from the speaker profile

    Returns:
        Modified transcript_data with corrected speaker names
    """
    if not transcript_data or "transcript" not in transcript_data:
        return transcript_data

    if not valid_speakers:
        return transcript_data

    # Common generic names LLMs use, categorised by role
    common_host_names = {
        "host", "interviewer", "moderator", "narrator", "anchor",
        "speaker 1", "speaker1",
    }
    common_guest_names = {
        "guest", "expert", "panelist", "speaker 2", "speaker2",
    }

    valid_speakers_lower = {s.lower(): s for s in valid_speakers}

    # Track invented names so each one maps consistently to the same valid speaker
    invented_name_map: dict[str, str] = {}
    # Round-robin counter for truly unknown names in multi-speaker profiles
    unknown_counter = 0

    for entry in transcript_data.get("transcript", []):
        if "speaker" not in entry:
            continue

        current_speaker = entry["speaker"]
        current_speaker_lower = current_speaker.lower().strip()

        # 1. Exact match (case-sensitive)
        if current_speaker in valid_speakers:
            continue

        # 2. Case-insensitive match
        if current_speaker_lower in valid_speakers_lower:
            entry["speaker"] = valid_speakers_lower[current_speaker_lower]
            continue

        # 3. Single-speaker profile: everything maps to the one speaker
        if len(valid_speakers) == 1:
            logger.warning(
                "Fixing speaker '{}' -> '{}' (single-speaker profile)",
                current_speaker, valid_speakers[0],
            )
            entry["speaker"] = valid_speakers[0]
            continue

        # --- Multi-speaker logic below ---

        # 4. Reuse mapping if we've seen this invented name before
        if current_speaker_lower in invented_name_map:
            entry["speaker"] = invented_name_map[current_speaker_lower]
            continue

        mapped = None

        # 5. Partial / substring match against valid names
        #    e.g. "Sarah" matches "Professor Sarah Kim", "Dr. Chen" matches "Dr. Wei Chen"
        for vs_lower, vs_original in valid_speakers_lower.items():
            if current_speaker_lower in vs_lower or vs_lower in current_speaker_lower:
                mapped = vs_original
                logger.warning(
                    "Fixing speaker '{}' -> '{}' (partial match)",
                    current_speaker, mapped,
                )
                break

        # 6. Common host names -> first speaker
        if mapped is None and current_speaker_lower in common_host_names:
            mapped = valid_speakers[0]
            logger.warning(
                "Fixing host/interviewer '{}' -> '{}' (multi-speaker profile)",
                current_speaker, mapped,
            )

        # 7. Common guest names -> second speaker (or first if only one)
        if mapped is None and current_speaker_lower in common_guest_names:
            mapped = valid_speakers[1] if len(valid_speakers) > 1 else valid_speakers[0]
            logger.warning(
                "Fixing guest '{}' -> '{}' (multi-speaker profile)",
                current_speaker, mapped,
            )

        # 8. Truly unknown: round-robin across valid speakers to preserve turns
        if mapped is None:
            mapped = valid_speakers[unknown_counter % len(valid_speakers)]
            unknown_counter += 1
            logger.warning(
                "Unknown speaker '{}' not in {}. Mapping to '{}'",
                current_speaker, valid_speakers, mapped,
            )

        invented_name_map[current_speaker_lower] = mapped
        entry["speaker"] = mapped

    return transcript_data


# Patch the transcript validation in podcast_creator to fix speaker names before validation.
#
# The node calls parser.invoke(text), which goes through:
#   invoke -> _call_with_config -> parse_result -> _parse_obj -> model_validate
# It does NOT call parse() at all. Subclassing PydanticOutputParser and overriding
# parse() alone has no effect. Additionally, skipping super().__init__() breaks the
# Runnable internals that invoke() depends on.
#
# Instead we use a thin delegating wrapper that pre-processes text to fix speaker names
# BEFORE handing it to the original parser. This avoids all inheritance pitfalls.
try:
    _original_create_validated_transcript_parser = podcast_core.create_validated_transcript_parser

    def _patched_create_validated_transcript_parser(speaker_names: list[str]):
        """
        Patched version that wraps the original parser with speaker-name pre-processing.
        """
        import json as _json

        original_parser = _original_create_validated_transcript_parser(speaker_names)

        class FixingSpeakerNamesParser:
            """Delegating wrapper that fixes speaker names before the original parser validates."""

            def __init__(self, original, valid_speakers):
                self._original = original
                self._valid_speakers = valid_speakers
                # Expose attributes that callers or LangChain internals may inspect
                self.pydantic_object = original.pydantic_object

            # ----------------------------------------------------------
            # Pre-processing helper
            # ----------------------------------------------------------
            def _preprocess(self, text: str) -> str:
                """Fix speaker names in JSON text before validation."""
                try:
                    cleaned = _strip_thinking_tags_and_extract_json(text)
                    data = _json.loads(cleaned)
                    fixed = _fix_speaker_names_in_transcript(data, self._valid_speakers)
                    result = _json.dumps(fixed, ensure_ascii=False)
                    logger.debug("Speaker name pre-processing applied successfully")
                    return result
                except Exception as e:
                    logger.warning(
                        "Speaker name pre-processing failed ({}), passing text through: {}",
                        type(e).__name__, str(e)[:200],
                    )
                    return text

            # ----------------------------------------------------------
            # Public API — every method the node or LangChain may call
            # ----------------------------------------------------------
            def invoke(self, input, config=None, **kwargs):
                """Pre-process then delegate to original parser.invoke()."""
                if isinstance(input, str):
                    input = self._preprocess(input)
                return self._original.invoke(input, config=config, **kwargs)

            async def ainvoke(self, input, config=None, **kwargs):
                """Async variant — pre-process then delegate."""
                if isinstance(input, str):
                    input = self._preprocess(input)
                return await self._original.ainvoke(input, config=config, **kwargs)

            def parse(self, text: str):
                """Pre-process then delegate to original parser.parse()."""
                return self._original.parse(self._preprocess(text))

            def parse_result(self, result, *, partial=False):
                """Pre-process Generation texts then delegate to original parser."""
                from langchain_core.outputs import Generation

                if result and isinstance(result, list):
                    fixed_result = []
                    for gen in result:
                        if isinstance(gen, Generation) and isinstance(gen.text, str):
                            fixed_text = self._preprocess(gen.text)
                            fixed_result.append(
                                Generation(text=fixed_text, generation_info=gen.generation_info)
                            )
                        else:
                            fixed_result.append(gen)
                    return self._original.parse_result(fixed_result, partial=partial)
                return self._original.parse_result(result, partial=partial)

            def get_format_instructions(self):
                return self._original.get_format_instructions()

            # Delegate any other attribute access to the original parser
            # (e.g. OutputFixingParser checks, LangChain tracing attributes, etc.)
            def __getattr__(self, name):
                return getattr(self._original, name)

        return FixingSpeakerNamesParser(original_parser, speaker_names)

    # Apply the patch to both the core module and the nodes module.
    # The nodes module imports create_validated_transcript_parser at the top level
    # (from .core import create_validated_transcript_parser), so it holds its own
    # reference that must also be replaced.
    podcast_core.create_validated_transcript_parser = _patched_create_validated_transcript_parser
    podcast_nodes.create_validated_transcript_parser = _patched_create_validated_transcript_parser
    logger.info("Applied podcast-creator speaker name fixing patch to core and nodes modules")

except AttributeError:
    logger.warning("Could not find create_validated_transcript_parser in podcast_creator.core - skipping speaker fix patch")
except Exception as e:
    logger.warning("Failed to patch create_validated_transcript_parser: {}", str(e))


# Patch AIFactory.create_language to disable thinking for Gemini models
try:
    from esperanto import AIFactory
    _original_create_language = AIFactory.create_language
    
    def _patched_create_language(*args, **kwargs):
        """
        Patched AIFactory.create_language that disables extended thinking for Gemini models.
        
        This prevents Gemini from outputting <think> tags that break JSON parsing.
        
        Handles both positional and keyword argument calls:
        - create_language(provider, model_name, config={...})
        - create_language(provider=..., model_name=..., config={...})
        """
        # Extract provider and model_name from args or kwargs
        provider = None
        model_name = None
        config = None
        
        # Handle positional arguments (provider, model_name, ...)
        if len(args) >= 1:
            provider = args[0]
        if len(args) >= 2:
            model_name = args[1]
        if len(args) >= 3:
            config = args[2]
        
        # Override with kwargs if provided
        provider = kwargs.get('provider', provider)
        model_name = kwargs.get('model_name', model_name)
        config = kwargs.get('config', config)
        
        # Check if this is a thinking model (Gemini, DeepSeek, Grok, Qwen)
        is_thinking_model = (
            (provider and provider.lower() in ['google', 'gemini', 'deepseek', 'xai']) or
            (model_name and any(kw in model_name.lower()
             for kw in ['gemini', 'deepseek', 'grok', 'qwen', 'r1']))
        )

        if is_thinking_model and config:
            # Disable extended thinking for Gemini models
            config = config.copy() if isinstance(config, dict) else {}
            
            # Try multiple possible config keys that might disable thinking
            # Different versions of esperanto/Gemini SDK might use different keys
            config['thinking_mode'] = 'disabled'
            config['extended_thinking'] = False
            config['disable_thinking'] = True
            config['thinking'] = False
            
            # For structured output, ensure we're using the right mode
            if 'structured' in config:
                structured = config['structured'].copy() if isinstance(config['structured'], dict) else {}
                structured['thinking'] = False
                structured['extended_thinking'] = False
                structured['thinking_mode'] = 'disabled'
                config['structured'] = structured
            
            logger.debug(
                f"Patched thinking model config to disable thinking: "
                f"provider={provider}, model={model_name}, config_keys={list(config.keys())}"
            )
            
            # Update kwargs with modified config
            if len(args) >= 3:
                # Replace config in args
                args = list(args)
                args[2] = config
                args = tuple(args)
            else:
                kwargs['config'] = config
        
        # Call original function with potentially modified config
        return _original_create_language(*args, **kwargs)
    
    # Apply the patch
    AIFactory.create_language = _patched_create_language
    logger.info("Applied AIFactory.create_language patch to disable thinking for thinking models")
    
except ImportError:
    logger.warning("Could not import esperanto.AIFactory - skipping model config patch")
except Exception as e:
    logger.warning("Failed to patch AIFactory.create_language: {}", str(e))


# Patch generate_single_audio_clip to add retry with backoff for TTS rate limits.
#
# Google's Gemini TTS has a low rate limit (e.g. 10 req/min). The podcast-creator
# fires multiple TTS requests concurrently per batch. When the limit is hit, the
# error message includes "Please retry in Xs", so we parse that delay and wait.
import asyncio as _asyncio

_RETRY_DELAY_PATTERN = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)
_TTS_MAX_RETRIES = int(os.environ.get("TTS_MAX_RETRIES", "5"))
_TTS_DEFAULT_RETRY_DELAY = float(os.environ.get("TTS_DEFAULT_RETRY_DELAY", "15"))

try:
    _original_generate_single_audio_clip = podcast_nodes.generate_single_audio_clip

    # Exception types that are always retryable (network/connection issues).
    # These often have empty str() representations so keyword matching won't work.
    _RETRYABLE_EXCEPTION_TYPES: tuple = ()
    try:
        import httpx
        import httpcore
        _RETRYABLE_EXCEPTION_TYPES = (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.NetworkError,
            httpcore.ConnectError,
            httpcore.TimeoutException,
            httpcore.NetworkError,
            ConnectionError,
            TimeoutError,
            OSError,
        )
    except ImportError:
        _RETRYABLE_EXCEPTION_TYPES = (ConnectionError, TimeoutError, OSError)

    async def _retrying_generate_single_audio_clip(dialogue_info):
        """Wrapper around generate_single_audio_clip with retry on transient TTS errors."""
        import random

        last_error = None
        for attempt in range(1, _TTS_MAX_RETRIES + 1):
            try:
                return await _original_generate_single_audio_clip(dialogue_info)
            except Exception as e:
                # Check by exception type first (covers network/connection errors
                # whose str() is often empty)
                is_retryable = isinstance(e, _RETRYABLE_EXCEPTION_TYPES)

                # Then check by error message keywords
                if not is_retryable:
                    error_msg = str(e).lower()
                    is_retryable = (
                        # Rate limits
                        "quota" in error_msg
                        or "rate" in error_msg
                        or "429" in error_msg
                        or "resource exhausted" in error_msg
                        # Transient server errors
                        or "internal error" in error_msg
                        or "500" in error_msg
                        or "503" in error_msg
                        or "service unavailable" in error_msg
                        or "please retry" in error_msg
                        or "server error" in error_msg
                        or "temporarily unavailable" in error_msg
                        # Connection errors by message
                        or "connect" in error_msg
                        or "timeout" in error_msg
                    )

                if not is_retryable:
                    raise  # Permanent error — don't retry

                last_error = e

                # Parse suggested delay from the error message, or use default
                match = _RETRY_DELAY_PATTERN.search(str(e))
                delay = float(match.group(1)) + 1.0 if match else _TTS_DEFAULT_RETRY_DELAY
                # Add jitter: +0-3s to avoid thundering herd from concurrent clips
                delay += random.uniform(0, 3)

                logger.warning(
                    "TTS error (attempt {}/{}): [{}] {}. Waiting {:.1f}s before retry...",
                    attempt, _TTS_MAX_RETRIES, type(e).__name__, str(e)[:120], delay,
                )
                await _asyncio.sleep(delay)

        # Exhausted all retries
        raise last_error  # type: ignore[misc]

    podcast_nodes.generate_single_audio_clip = _retrying_generate_single_audio_clip
    logger.info("Applied TTS rate-limit retry patch to generate_single_audio_clip")

except AttributeError:
    logger.warning("Could not find generate_single_audio_clip in podcast_creator.nodes - skipping TTS retry patch")
except Exception as e:
    logger.warning("Failed to patch generate_single_audio_clip: {}", str(e))


# ---------------------------------------------------------------------------
# Progress tracking for podcast generation
# ---------------------------------------------------------------------------

# Async-task-scoped context so the patched nodes can report progress
# without race conditions across concurrent podcast generation requests.
_active_command_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    '_active_command_id', default=None
)


async def _update_command_progress(command_id, current: int, total: int, phase: str):
    """Update command record with progress data.

    surreal-commands' CommandResult doesn't have a progress field, but SurrealDB
    is schema-flexible — we UPDATE the command record directly with a progress object.
    """
    try:
        pct = round((current / total) * 100) if total > 0 else 0
        await repo_query(
            "UPDATE $cmd_id SET progress = $progress",
            {
                "cmd_id": ensure_record_id(command_id),
                "progress": {
                    "current": current,
                    "total": total,
                    "percentage": pct,
                    "phase": phase,
                },
            },
        )
    except Exception as e:
        logger.debug(f"Progress update failed (non-fatal): {e}")


# Patch generate_transcript_node for per-segment progress reporting.
# We re-implement the ~30-line loop so we can call _update_command_progress
# after each segment instead of only at start/end.
try:
    from esperanto import AIFactory as _AIFactory_for_transcript

    _original_generate_transcript_node = podcast_nodes.generate_transcript_node

    async def _patched_generate_transcript_node(state, config):
        """Transcript node with per-segment progress reporting."""
        logger.info("Starting transcript generation (patched with progress)")

        assert state.get("outline") is not None, "outline must be provided"
        assert state.get("speaker_profile") is not None, "speaker_profile must be provided"

        configurable = config.get("configurable", {})
        transcript_provider = configurable.get("transcript_provider", "openai")
        transcript_model_name = configurable.get("transcript_model", "gpt-4o-mini")

        transcript_model = _AIFactory_for_transcript.create_language(
            transcript_provider,
            transcript_model_name,
            config={"max_tokens": 5000, "structured": {"type": "json"}},
        ).to_langchain()

        speaker_profile = state["speaker_profile"]
        assert speaker_profile is not None, "speaker_profile must be provided"
        speaker_names = speaker_profile.get_speaker_names()
        validated_transcript_parser = podcast_nodes.create_validated_transcript_parser(speaker_names)

        outline = state["outline"]
        assert outline is not None, "outline must be provided"

        total_segments = len(outline.segments)

        # Report initial progress
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 0, total_segments, "transcript")

        transcript = []
        for i, segment in enumerate(outline.segments):
            logger.info(
                f"Generating transcript for segment {i + 1}/{total_segments}: {segment.name}"
            )

            is_final = i == total_segments - 1
            turns = 3 if segment.size == "short" else 6 if segment.size == "medium" else 10

            data = {
                "briefing": state["briefing"],
                "outline": outline,
                "context": state["content"],
                "segment": segment,
                "is_final": is_final,
                "turns": turns,
                "speakers": speaker_profile.speakers,
                "speaker_names": speaker_names,
                "transcript": transcript,
            }

            transcript_prompt = podcast_nodes.get_transcript_prompter()
            transcript_prompt_rendered = transcript_prompt.render(data)
            transcript_preview = await transcript_model.ainvoke(transcript_prompt_rendered)
            transcript_preview.content = podcast_nodes.clean_thinking_content(
                transcript_preview.content
            )
            result = validated_transcript_parser.invoke(transcript_preview.content)
            transcript.extend(result.transcript)

            # Report per-segment progress
            cmd_id = _active_command_id.get(None)
            if cmd_id:
                await _update_command_progress(
                    cmd_id, i + 1, total_segments, "transcript"
                )

        logger.info(f"Generated transcript with {len(transcript)} dialogue segments")
        return {"transcript": transcript}

    podcast_nodes.generate_transcript_node = _patched_generate_transcript_node
    logger.info("Applied per-segment progress tracking patch to generate_transcript_node")

except Exception as e:
    logger.warning("Failed to patch generate_transcript_node for progress: {}", str(e))

# Patch generate_outline_node to report progress
try:
    _original_generate_outline_node = podcast_nodes.generate_outline_node

    async def _patched_generate_outline_node(state, config):
        """Outline node with progress reporting."""
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 0, 1, "outline")
        result = await _original_generate_outline_node(state, config)
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 1, 1, "outline")
        return result

    podcast_nodes.generate_outline_node = _patched_generate_outline_node
    logger.info("Applied progress tracking patch to generate_outline_node")

except Exception as e:
    logger.warning("Failed to patch generate_outline_node for progress: {}", str(e))

# Patch generate_all_audio_node to report progress
try:
    _original_generate_all_audio_node = podcast_nodes.generate_all_audio_node

    async def _patched_generate_all_audio_node(state, config):
        """Audio generation node with progress reporting."""
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 0, 1, "audio")
        result = await _original_generate_all_audio_node(state, config)
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 1, 1, "audio")
        return result

    podcast_nodes.generate_all_audio_node = _patched_generate_all_audio_node
    logger.info("Applied progress tracking patch to generate_all_audio_node")

except Exception as e:
    logger.warning("Failed to patch generate_all_audio_node for progress: {}", str(e))

# Patch combine_audio_node to report progress
try:
    _original_combine_audio_node = podcast_nodes.combine_audio_node

    async def _patched_combine_audio_node(state, config):
        """Combine audio node with progress reporting."""
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 0, 1, "combining")
        result = await _original_combine_audio_node(state, config)
        cmd_id = _active_command_id.get(None)
        if cmd_id:
            await _update_command_progress(cmd_id, 1, 1, "combining")
        return result

    podcast_nodes.combine_audio_node = _patched_combine_audio_node
    logger.info("Applied progress tracking patch to combine_audio_node")

except Exception as e:
    logger.warning("Failed to patch combine_audio_node for progress: {}", str(e))

# Rebuild the compiled LangGraph graph so it picks up all patched node functions.
# The original graph was compiled at import time with the original function references.
# We need to rebuild it with the current (patched) module attributes.
try:
    import podcast_creator.graph as _podcast_graph
    from langgraph.graph import END, START, StateGraph
    from podcast_creator.state import PodcastState as _PodcastState

    _new_workflow = StateGraph(_PodcastState)
    _new_workflow.add_node("generate_outline", podcast_nodes.generate_outline_node)
    _new_workflow.add_node("generate_transcript", podcast_nodes.generate_transcript_node)
    _new_workflow.add_node("generate_all_audio", podcast_nodes.generate_all_audio_node)
    _new_workflow.add_node("combine_audio", podcast_nodes.combine_audio_node)
    _new_workflow.add_edge(START, "generate_outline")
    _new_workflow.add_edge("generate_outline", "generate_transcript")
    _new_workflow.add_conditional_edges(
        "generate_transcript", podcast_nodes.route_audio_generation, ["generate_all_audio"]
    )
    _new_workflow.add_edge("generate_all_audio", "combine_audio")
    _new_workflow.add_edge("combine_audio", END)
    _podcast_graph.graph = _new_workflow.compile()
    logger.info("Rebuilt podcast graph with all patched node functions")

except Exception as e:
    logger.warning("Failed to rebuild podcast graph with patched nodes: {}", str(e))


def full_model_dump(model):
    if isinstance(model, BaseModel):
        return model.model_dump()
    elif isinstance(model, dict):
        return {k: full_model_dump(v) for k, v in model.items()}
    elif isinstance(model, list):
        return [full_model_dump(item) for item in model]
    else:
        return model


class PodcastGenerationInput(CommandInput):
    episode_profile: str
    speaker_profile: str
    episode_name: str
    content: str
    notebook_ids: Optional[list[str]] = None  # All notebooks that contributed content
    briefing_suffix: Optional[str] = None
    language: Optional[str] = "en"


class PodcastGenerationOutput(CommandOutput):
    success: bool
    episode_id: Optional[str] = None
    audio_file_path: Optional[str] = None
    transcript: Optional[dict] = None
    outline: Optional[dict] = None
    processing_time: float
    error_message: Optional[str] = None


@command("generate_podcast", app="open_notebook")
async def generate_podcast_command(
    input_data: PodcastGenerationInput,
) -> PodcastGenerationOutput:
    """
    Real podcast generation using podcast-creator library with Episode Profiles
    """
    start_time = time.time()

    try:
        logger.info("=" * 80)
        logger.info("PODCAST GENERATION COMMAND STARTED")
        logger.info(f"  Episode Name: {input_data.episode_name}")
        logger.info(f"  Episode Profile: {input_data.episode_profile}")
        logger.info(f"  Speaker Profile: {input_data.speaker_profile}")
        logger.info(f"  Notebook IDs: {input_data.notebook_ids}")
        logger.info(f"  Content Length: {len(input_data.content)} chars")
        logger.info("=" * 80)

        # 1. Load Episode and Speaker profiles from SurrealDB
        episode_profile = await EpisodeProfile.get_by_name(input_data.episode_profile)
        if not episode_profile:
            raise ValueError(
                f"Episode profile '{input_data.episode_profile}' not found"
            )

        speaker_profile = await SpeakerProfile.get_by_name(
            episode_profile.speaker_config
        )
        if not speaker_profile:
            raise ValueError(
                f"Speaker profile '{episode_profile.speaker_config}' not found"
            )

        logger.info(f"Loaded episode profile: {episode_profile.name}")
        logger.info(f"Loaded speaker profile: {speaker_profile.name}")

        # 3. Load all profiles and configure podcast-creator
        episode_profiles = await repo_query("SELECT * FROM episode_profile")
        speaker_profiles = await repo_query("SELECT * FROM speaker_profile")

        # Transform the surrealdb array into a dictionary for podcast-creator
        episode_profiles_dict = {
            profile["name"]: profile for profile in episode_profiles
        }
        speaker_profiles_dict = {
            profile["name"]: profile for profile in speaker_profiles
        }

        # 4. Generate briefing
        briefing = episode_profile.default_briefing
        if input_data.briefing_suffix:
            briefing += f"\n\nAdditional instructions: {input_data.briefing_suffix}"

        # Inject language instruction into briefing
        if input_data.language and input_data.language != "en":
            lang_name = {"fr": "French"}.get(input_data.language, input_data.language)
            briefing = (
                f"IMPORTANT: This entire podcast MUST be in {lang_name}. "
                f"All dialogue, introductions, transitions, and conclusions must be in {lang_name}. "
                f"Speaker names can remain in their original form.\n\n"
                + briefing
            )

        # Create the a record for the episose and associate with the ongoing command
        episode = PodcastEpisode(
            name=input_data.episode_name,
            episode_profile=full_model_dump(episode_profile.model_dump()),
            speaker_profile=full_model_dump(speaker_profile.model_dump()),
            command=ensure_record_id(input_data.execution_context.command_id)
            if input_data.execution_context
            else None,
            briefing=briefing,
            content=input_data.content,
            audio_file=None,
            transcript=None,
            outline=None,
        )
        await episode.save()

        configure("speakers_config", {"profiles": speaker_profiles_dict})
        configure("episode_config", {"profiles": episode_profiles_dict})

        logger.info("Configured podcast-creator with episode and speaker profiles")

        logger.info(f"Generated briefing (length: {len(briefing)} chars)")

        # 5. Create output directory
        output_dir = Path(f"{DATA_FOLDER}/podcasts/episodes/{input_data.episode_name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created output directory: {output_dir}")

        # 6. Generate podcast using podcast-creator
        logger.info("Starting podcast generation with podcast-creator...")

        # Set active command ID for progress reporting in the patched nodes.
        # Uses ContextVar so concurrent async tasks each see their own value.
        cmd_id = (
            str(input_data.execution_context.command_id)
            if input_data.execution_context
            else None
        )
        _active_command_id.set(cmd_id)

        if cmd_id:
            await _update_command_progress(cmd_id, 0, 0, "starting")

        try:
            result = await create_podcast(
                content=input_data.content,
                briefing=briefing,
                episode_name=input_data.episode_name,
                output_dir=str(output_dir),
                speaker_config=speaker_profile.name,
                episode_profile=episode_profile.name,
            )
        finally:
            _active_command_id.set(None)

        episode.audio_file = (
            str(result.get("final_output_file_path")) if result else None
        )
        episode.transcript = {
            "transcript": full_model_dump(result["transcript"]) if result else None
        }
        episode.outline = full_model_dump(result["outline"]) if result else None
        await episode.save()

        # Update ALL artifact records with real episode ID 
        # (artifacts were created at job submission with job_id as placeholder)
        if input_data.notebook_ids and input_data.execution_context:
            try:
                from open_notebook.domain.artifact import Artifact
                # Note: repo_query is already imported at module level
                
                # Find all artifacts that were created with the job_id as artifact_id
                job_id = str(input_data.execution_context.command_id)
                logger.info(f"Looking for artifacts with job_id: {job_id}")
                logger.debug(f"Notebook IDs to check: {input_data.notebook_ids}")
                
                artifacts = await repo_query(
                    "SELECT * FROM artifact WHERE artifact_id = $artifact_id AND artifact_type = 'podcast'",
                    {"artifact_id": job_id}
                )
                logger.debug(f"Found {len(artifacts) if artifacts else 0} artifacts with job_id={job_id}")
                
                if artifacts and len(artifacts) > 0:
                    # Update all existing artifacts with the real episode ID
                    for artifact_data in artifacts:
                        artifact = Artifact(**artifact_data)
                        artifact.artifact_id = str(episode.id)
                        await artifact.save()
                        logger.info(
                            f"Updated artifact {artifact.id} with episode ID {episode.id}"
                        )
                    logger.info(f"Updated {len(artifacts)} artifact(s) with episode ID {episode.id}")
                else:
                    # Fallback: create artifacts if not found (shouldn't happen normally)
                    for nb_id in input_data.notebook_ids:
                        await Artifact.create_for_artifact(
                            notebook_id=nb_id,
                            artifact_type="podcast",
                            artifact_id=str(episode.id),
                            title=input_data.episode_name,
                        )
                    logger.info(
                        f"Created {len(input_data.notebook_ids)} new artifact links for podcast {episode.id}"
                    )
            except Exception as artifact_error:
                logger.warning("Failed to update artifact records: {}", str(artifact_error))

        processing_time = time.time() - start_time
        logger.info(
            f"Successfully generated podcast episode: {episode.id} in {processing_time:.2f}s"
        )

        return PodcastGenerationOutput(
            success=True,
            episode_id=str(episode.id),
            audio_file_path=str(result.get("final_output_file_path"))
            if result
            else None,
            transcript={"transcript": full_model_dump(result["transcript"])}
            if result.get("transcript")
            else None,
            outline=full_model_dump(result["outline"])
            if result.get("outline")
            else None,
            processing_time=processing_time,
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error("Podcast generation failed: {}", str(e))
        logger.exception(e)

        # Check for specific GPT-5 extended thinking issue
        error_msg = str(e)
        if "Invalid json output" in error_msg or "Expecting value" in error_msg:
            # This often happens with GPT-5 models that use extended thinking (<think> tags)
            # and put all output inside thinking blocks
            error_msg += (
                "\n\nNOTE: This error commonly occurs with GPT-5 models that use extended thinking. "
                "The model may be putting all output inside <think> tags, leaving nothing to parse. "
                "Try using gpt-4o, gpt-4o-mini, or gpt-4-turbo instead in your episode profile."
            )

        return PodcastGenerationOutput(
            success=False, processing_time=processing_time, error_message=error_msg
        )
