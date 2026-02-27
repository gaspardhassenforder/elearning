import operator
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from content_core import extract_content
from content_core.common import ProcessSourceState
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from loguru import logger
from typing_extensions import Annotated, TypedDict

from open_notebook.ai.models import Model, ModelManager
from open_notebook.domain.content_settings import ContentSettings
from open_notebook.domain.notebook import Asset, Source
from open_notebook.domain.transformation import Transformation
from open_notebook.graphs.transformation import graph as transform_graph


VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v", ".m4a", ".mp3", ".wav"}
YOUTUBE_HOSTS = {"youtube.com", "youtu.be", "www.youtube.com"}
_VIDEO_TIMESTAMP_RE = re.compile(r'\[VIDEO_TIMESTAMP:(\d+(?:\.\d+)?)\]')


def is_video_source(content_state) -> bool:
    """Check if the content state represents a video or YouTube source.

    Accepts both dict (initial ProcessSourceState) and Pydantic model
    (ProcessSourceOutput returned by extract_content).
    """
    if isinstance(content_state, dict):
        url = content_state.get("url", "") or ""
        file_path = content_state.get("file_path", "") or ""
    else:
        url = getattr(content_state, "url", None) or ""
        file_path = getattr(content_state, "file_path", None) or ""
    host = urlparse(url).netloc.lower()
    ext = Path(file_path).suffix.lower() if file_path else ""
    return host in YOUTUBE_HOSTS or ext in VIDEO_EXTENSIONS


class SourceState(TypedDict):
    content_state: ProcessSourceState
    apply_transformations: List[Transformation]
    source_id: str
    notebook_ids: List[str]
    source: Source
    transformation: Annotated[list, operator.add]
    embed: bool


class TransformationState(TypedDict):
    source: Source
    transformation: Transformation


async def content_process(state: SourceState) -> dict:
    content_settings = ContentSettings(
        default_content_processing_engine_doc="auto",
        default_content_processing_engine_url="auto",
        default_embedding_option="ask",
        auto_delete_files="yes",
        youtube_preferred_languages=[
            "en",
            "pt",
            "es",
            "de",
            "nl",
            "en-GB",
            "fr",
            "hi",
            "ja",
        ],
    )
    content_state: Dict[str, Any] = state["content_state"]  # type: ignore[assignment]

    content_state["url_engine"] = (
        content_settings.default_content_processing_engine_url or "auto"
    )
    content_state["document_engine"] = (
        content_settings.default_content_processing_engine_doc or "auto"
    )
    content_state["output_format"] = "markdown"

    # Pass YouTube language preferences to content_core for transcript extraction
    if content_settings.youtube_preferred_languages:
        content_state["youtube_preferred_languages"] = content_settings.youtube_preferred_languages

    # Add speech-to-text model configuration from Default Models
    try:
        model_manager = ModelManager()
        defaults = await model_manager.get_defaults()
        if defaults.default_speech_to_text_model:
            stt_model = await Model.get(defaults.default_speech_to_text_model)
            if stt_model:
                content_state["audio_provider"] = stt_model.provider
                content_state["audio_model"] = stt_model.name
                logger.debug(
                    f"Using speech-to-text model: {stt_model.provider}/{stt_model.name}"
                )
    except Exception as e:
        logger.warning("Failed to retrieve speech-to-text model configuration: {}", str(e))
        # Continue without custom audio model (content-core will use its default)

    try:
        processed_state = await extract_content(content_state)
        return {"content_state": processed_state}
    except Exception as e:
        if is_video_source(content_state):
            logger.warning(
                "content_core failed to process video source '{}' — "
                "likely missing system ffmpeg/ffprobe. "
                "video_process will attempt moviepy fallback. Error: {}",
                content_state.get("file_path") or content_state.get("url", ""),
                str(e),
            )
            fp = content_state.get("file_path") or ""
            fallback_state = ProcessSourceState(
                file_path=fp,
                url=content_state.get("url") or "",
                audio_provider=content_state.get("audio_provider"),
                audio_model=content_state.get("audio_model"),
                title=Path(fp).stem if fp else "",
            )
            return {"content_state": fallback_state}
        raise


async def save_source(state: SourceState) -> dict:
    content_state = state["content_state"]

    # Get existing source using the provided source_id
    source = await Source.get(state["source_id"])
    if not source:
        raise ValueError(f"Source with ID {state['source_id']} not found")

    # Update the source with processed content
    source.asset = Asset(url=content_state.url, file_path=content_state.file_path)
    source.full_text = content_state.content

    # Preserve existing title if none provided in processed content
    if content_state.title:
        source.title = content_state.title

    await source.save()

    # NOTE: Notebook associations are created by the API immediately for UI responsiveness
    # No need to create them here to avoid duplicate edges

    if state["embed"]:
        if source.full_text:
            logger.debug("Embedding content for vector search")
            await source.vectorize()
        else:
            logger.warning(
                "Skipping embedding for source {} — no text content extracted", source.id
            )

    return {"source": source}


def trigger_transformations(state: SourceState, config: RunnableConfig) -> List[Send]:
    if len(state["apply_transformations"]) == 0:
        return []

    to_apply = state["apply_transformations"]
    logger.debug(f"Applying transformations {to_apply}")

    return [
        Send(
            "transform_content",
            {
                "source": state["source"],
                "transformation": t,
            },
        )
        for t in to_apply
    ]


async def transform_content(state: TransformationState) -> Optional[dict]:
    source = state["source"]
    content = source.full_text
    if not content:
        return None
    transformation: Transformation = state["transformation"]

    logger.debug(f"Applying transformation {transformation.name}")
    result = await transform_graph.ainvoke(
        dict(input_text=content, transformation=transformation)  # type: ignore[arg-type]
    )
    await source.add_insight(transformation.title, result["output"])
    return {
        "transformation": [
            {
                "output": result["output"],
                "transformation_name": transformation.name,
            }
        ]
    }


async def video_process(state: SourceState) -> dict:
    """Post-process video/YouTube source content to normalize timestamp markers.

    For YouTube sources where content_core returned empty content (pytubefix fallback
    failed), this node directly uses youtube-transcript-api which is more reliable.
    Transcripts are formatted with [VIDEO_TIMESTAMP:SECONDS] markers.

    For content already returned by content_core, normalizes any [MM:SS]/[HH:MM:SS]
    timecodes to the [VIDEO_TIMESTAMP:SECONDS] format.
    """
    content_state = state["content_state"]
    # ProcessSourceOutput is a Pydantic model after extract_content() runs
    full_text = getattr(content_state, "content", None) or ""
    url = getattr(content_state, "url", None) or ""

    # --- YouTube fallback: content_core uses pytubefix which silently fails for many
    # videos. youtube-transcript-api (already installed as a content_core dep) is far
    # more reliable: tries manual → auto-generated → any language with translation.
    if not full_text and url and urlparse(url).netloc.lower() in YOUTUBE_HOSTS:
        logger.info("content_core returned empty transcript for YouTube URL — trying youtube-transcript-api directly")
        full_text = await _fetch_youtube_transcript(url)
        if full_text:
            try:
                updated_state = content_state.model_copy(update={"content": full_text})
            except AttributeError:
                updated_state = content_state.copy(update={"content": full_text})
            logger.info("YouTube transcript fetched successfully via youtube-transcript-api")
            return {"content_state": updated_state}
        else:
            logger.warning("youtube-transcript-api also returned no transcript for {}", url)
            return {}

    # --- Local video fallback: content_core's ffprobe-based pipeline failed.
    # Use moviepy/imageio-ffmpeg (bundled, no system install needed) to transcribe directly.
    file_path = getattr(content_state, "file_path", None) or ""
    if not full_text and file_path:
        ext = Path(file_path).suffix.lower()
        if ext in {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}:
            logger.info(
                "content_core returned no content for local video '{}' — "
                "attempting direct moviepy/STT fallback.",
                file_path,
            )
            transcript = await _extract_local_video_transcript(file_path, content_state)
            if transcript:
                try:
                    updated_state = content_state.model_copy(update={"content": transcript})
                except AttributeError:
                    updated_state = content_state.copy(update={"content": transcript})
                return {"content_state": updated_state}
            else:
                logger.warning(
                    "All extraction methods failed for local video '{}'. "
                    "Source saved with no text. Configure a speech-to-text model in "
                    "Default Models settings for video transcription.",
                    file_path,
                )
                return {}

    # If already has VIDEO_TIMESTAMP markers, nothing to do
    if _VIDEO_TIMESTAMP_RE.search(full_text):
        logger.debug("Video source already has VIDEO_TIMESTAMP markers, skipping normalization")
        return {}

    # Normalize [MM:SS] / [HH:MM:SS] timecodes produced by some content_core engines
    timecode_re = re.compile(r'\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]')

    def timecode_to_seconds(m: re.Match) -> str:
        parts = [int(x) for x in m.groups() if x is not None]
        if len(parts) == 2:
            minutes, seconds = parts
            total = minutes * 60 + seconds
        else:
            hours, minutes, seconds = parts
            total = hours * 3600 + minutes * 60 + seconds
        return f'[VIDEO_TIMESTAMP:{float(total)}]'

    if timecode_re.search(full_text):
        normalized = timecode_re.sub(timecode_to_seconds, full_text)
        logger.info("Normalized timecode markers to VIDEO_TIMESTAMP format")
        try:
            updated_state = content_state.model_copy(update={"content": normalized})
        except AttributeError:
            updated_state = content_state.copy(update={"content": normalized})
        return {"content_state": updated_state}

    logger.debug("No timestamp markers found in video source content")
    return {}


async def _fetch_youtube_transcript(url: str) -> str:
    """Fetch YouTube transcript via youtube-transcript-api with VIDEO_TIMESTAMP markers.

    Tries in order: manual captions in preferred languages → auto-generated in preferred
    languages → any available transcript (with translation as last resort).

    Returns formatted text with [VIDEO_TIMESTAMP:SECONDS] markers, or empty string on failure.
    """
    from urllib.parse import parse_qs

    # Extract video ID from URL
    parsed = urlparse(url)
    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/").split("?")[0]
    else:
        qs = parse_qs(parsed.query)
        video_id = (qs.get("v") or [""])[0]

    if not video_id:
        logger.warning("Could not extract video ID from URL: {}", url)
        return ""

    preferred_languages = ["en", "pt", "es", "de", "nl", "fr", "hi", "ja"]

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)

        transcript = None

        # 1. Manual captions in a preferred language
        try:
            transcript = transcript_list.find_manually_created_transcript(preferred_languages)
            logger.debug("Found manual transcript for {}", video_id)
        except Exception:
            pass

        # 2. Auto-generated captions in a preferred language
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(preferred_languages)
                logger.debug("Found auto-generated transcript for {}", video_id)
            except Exception:
                pass

        # 3. Any available transcript (may need translation)
        if transcript is None:
            available = list(transcript_list)
            if available:
                transcript = available[0]
                logger.debug(
                    "Using first available transcript ({}) for {}", transcript.language, video_id
                )

        if transcript is None:
            logger.warning("No transcript available for video {}", video_id)
            return ""

        entries = transcript.fetch()

        # Format with VIDEO_TIMESTAMP markers so chunking can extract timestamps
        lines = []
        for entry in entries:
            # youtube-transcript-api returns dicts or FetchedTranscript objects
            if isinstance(entry, dict):
                start = entry.get("start", 0)
                text = (entry.get("text") or "").strip()
            else:
                start = getattr(entry, "start", 0)
                text = (getattr(entry, "text", "") or "").strip()

            if text:
                lines.append(f"[VIDEO_TIMESTAMP:{start}]")
                lines.append(text)

        result = "\n".join(lines)
        logger.info(
            "Fetched {} transcript entries ({} chars) for video {}",
            len(entries), len(result), video_id,
        )
        return result

    except Exception as e:
        logger.warning("youtube-transcript-api failed for {}: {}", video_id, str(e))
        return ""


async def _extract_local_video_transcript(file_path: str, content_state) -> str:
    """Extract and transcribe audio from a local video file using moviepy + STT.

    Splits the video into 2-minute segments using moviepy/imageio-ffmpeg (bundled,
    no system ffmpeg needed), transcribes each in parallel, and combines with
    [VIDEO_TIMESTAMP:SECONDS] markers so the viewer can navigate to each segment.
    """
    import asyncio
    import math
    import os
    import tempfile

    from esperanto import AIFactory
    from moviepy import AudioFileClip  # reads via imageio-ffmpeg bundled binary

    audio_provider = getattr(content_state, "audio_provider", None)
    audio_model = getattr(content_state, "audio_model", None)

    if not audio_provider or not audio_model:
        logger.warning(
            "No speech-to-text model configured — cannot transcribe local video '{}'. "
            "Go to Settings → Default Models and configure a Speech-to-Text model "
            "(e.g. openai/whisper-1, groq/whisper-large-v3-turbo).",
            file_path,
        )
        return ""

    SEGMENT_LENGTH_S = 120  # 2-minute segments for good timestamp granularity

    try:
        import wave

        import numpy as np
        from content_core.config import CONFIG

        timeout = (CONFIG.get("speech_to_text") or {}).get("timeout", 3600)
        stt_config = {"timeout": timeout} if timeout else {}
        stt_model = AIFactory.create_speech_to_text(audio_provider, audio_model, stt_config)

        logger.info("Extracting audio segments from local video: {}", file_path)

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Load the entire audio into a numpy array in one shot.
            # subclipped() creates a new FFMPEG reader subprocess per segment (fails without
            # system ffmpeg). Reading everything at once uses imageio-ffmpeg's bundled binary
            # for a single decode pass; all segmentation is then done in numpy.
            clip = AudioFileClip(file_path)
            duration_s = clip.duration
            fps = int(clip.fps)
            full_audio = clip.to_soundarray()  # shape: (n_frames,) or (n_frames, channels)
            clip.close()

            if full_audio.ndim == 1:
                full_audio = full_audio.reshape(-1, 1)
            n_channels = full_audio.shape[1]
            total_frames = full_audio.shape[0]
            frames_per_segment = int(fps * SEGMENT_LENGTH_S)
            n_segments = max(1, math.ceil(total_frames / frames_per_segment))

            segments: list[tuple[float, str]] = []
            for i in range(n_segments):
                start_frame = i * frames_per_segment
                end_frame = min((i + 1) * frames_per_segment, total_frames)
                start_s = i * SEGMENT_LENGTH_S

                seg_audio = full_audio[start_frame:end_frame]
                audio_int16 = (np.clip(seg_audio, -1.0, 1.0) * 32767).astype(np.int16)

                seg_path = os.path.join(tmp_dir, f"seg_{i:03d}.wav")
                with wave.open(seg_path, "w") as wf:
                    wf.setnchannels(n_channels)
                    wf.setsampwidth(2)  # 16-bit PCM
                    wf.setframerate(fps)
                    wf.writeframes(audio_int16.tobytes())

                segments.append((start_s, seg_path))

            logger.debug("Exported {} audio segments ({:.0f}s total)", n_segments, duration_s)

            semaphore = asyncio.Semaphore(3)

            async def _transcribe(seg_path: str) -> str:
                async with semaphore:
                    return (await stt_model.atranscribe(seg_path)).text

            transcriptions = await asyncio.gather(
                *[_transcribe(seg_path) for _, seg_path in segments]
            )

        lines = []
        for (start_s, _), text in zip(segments, transcriptions):
            text = (text or "").strip()
            if text:
                lines.append(f"[VIDEO_TIMESTAMP:{float(start_s)}]")
                lines.append(text)

        transcript = "\n".join(lines)
        if transcript:
            logger.info(
                "Successfully transcribed local video ({} chars, {} segments): {}",
                len(transcript), len(segments), file_path,
            )
        else:
            logger.warning(
                "STT model returned empty transcript for '{}'. "
                "Check that a speech-to-text model is configured in Default Models.",
                file_path,
            )
        return transcript
    except Exception as e:
        logger.error(
            "Failed to extract audio from local video '{}': {}. "
            "Install ffmpeg for reliable video processing: https://ffmpeg.org/download.html",
            file_path, str(e),
        )
        return ""


def route_after_content_process(state: SourceState) -> str:
    content_state = state["content_state"]
    if is_video_source(content_state):
        return "video_process"
    return "save_source"


# Create and compile the workflow
workflow = StateGraph(SourceState)

# Add nodes
workflow.add_node("content_process", content_process)
workflow.add_node("video_process", video_process)
workflow.add_node("save_source", save_source)
workflow.add_node("transform_content", transform_content)
# Define the graph edges
workflow.add_edge(START, "content_process")
workflow.add_conditional_edges(
    "content_process",
    route_after_content_process,
    {"video_process": "video_process", "save_source": "save_source"},
)
workflow.add_edge("video_process", "save_source")
workflow.add_conditional_edges(
    "save_source", trigger_transformations, ["transform_content"]
)
workflow.add_edge("transform_content", END)

# Compile the graph
source_graph = workflow.compile()
