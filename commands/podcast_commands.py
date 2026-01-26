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
    logger.error(f"Failed to import podcast_creator: {e}")
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
    
    This handles the case where LLMs (especially Gemini) generate dialogue with
    generic speaker names like "Host" or "Interviewer" instead of using the
    configured speaker names.
    
    For single-speaker profiles, any invalid name is mapped to the single valid speaker.
    For multi-speaker profiles, common interviewer names are mapped to the first speaker.
    
    Args:
        transcript_data: The transcript dict with 'transcript' key containing dialogue list
        valid_speakers: List of valid speaker names from the speaker profile
    
    Returns:
        Modified transcript_data with corrected speaker names
    """
    if not transcript_data or "transcript" not in transcript_data:
        return transcript_data
    
    # Common names LLMs use for interviewers/hosts
    common_host_names = {"host", "interviewer", "moderator", "narrator", "speaker", "speaker 1", "speaker 2"}
    
    valid_speakers_lower = {s.lower(): s for s in valid_speakers}
    
    for entry in transcript_data.get("transcript", []):
        if "speaker" not in entry:
            continue
        
        current_speaker = entry["speaker"]
        current_speaker_lower = current_speaker.lower()
        
        # If speaker is valid, no fix needed
        if current_speaker in valid_speakers or current_speaker_lower in valid_speakers_lower:
            # Normalize case if needed
            if current_speaker not in valid_speakers and current_speaker_lower in valid_speakers_lower:
                entry["speaker"] = valid_speakers_lower[current_speaker_lower]
            continue
        
        # For single-speaker profiles, map any invalid name to the single speaker
        if len(valid_speakers) == 1:
            logger.warning(
                f"Fixing invalid speaker name '{current_speaker}' -> '{valid_speakers[0]}' "
                f"(single-speaker profile)"
            )
            entry["speaker"] = valid_speakers[0]
            continue
        
        # For multi-speaker profiles, map common host/interviewer names to first speaker
        if current_speaker_lower in common_host_names:
            logger.warning(
                f"Fixing host/interviewer name '{current_speaker}' -> '{valid_speakers[0]}' "
                f"(multi-speaker profile)"
            )
            entry["speaker"] = valid_speakers[0]
            continue
        
        # For other invalid names in multi-speaker, try fuzzy matching or use first speaker
        logger.warning(
            f"Unknown speaker '{current_speaker}' not in valid speakers {valid_speakers}. "
            f"Mapping to first speaker: '{valid_speakers[0]}'"
        )
        entry["speaker"] = valid_speakers[0]
    
    return transcript_data


# Patch the transcript validation in podcast_creator to fix speaker names before validation
try:
    _original_create_validated_transcript_parser = podcast_core.create_validated_transcript_parser
    
    def _patched_create_validated_transcript_parser(speaker_names: list[str]):
        """
        Patched version that creates a parser with a pre-processing step to fix speaker names.
        """
        from langchain_core.output_parsers import PydanticOutputParser
        from langchain_core.exceptions import OutputParserException
        import json
        
        # Get the original parser
        original_parser = _original_create_validated_transcript_parser(speaker_names)
        
        class FixingSpeakerNamesParser(PydanticOutputParser):
            """Parser that fixes speaker names before validation."""
            
            def __init__(self, original, valid_speakers):
                # Don't call super().__init__() - we're wrapping the original
                self._original = original
                self._valid_speakers = valid_speakers
                self.pydantic_object = original.pydantic_object
            
            def parse(self, text: str):
                """Parse with speaker name fixing."""
                try:
                    # First try the original parser
                    return self._original.parse(text)
                except OutputParserException as e:
                    # If it's a speaker validation error, try to fix it
                    if "Invalid speaker name" in str(e):
                        logger.warning(f"Speaker validation failed, attempting to fix speaker names...")
                        try:
                            # Extract JSON from text
                            cleaned = _strip_thinking_tags_and_extract_json(text)
                            data = json.loads(cleaned)
                            
                            # Fix speaker names
                            fixed_data = _fix_speaker_names_in_transcript(data, self._valid_speakers)
                            
                            # Re-validate with fixed data
                            return self.pydantic_object.model_validate(fixed_data)
                        except Exception as fix_error:
                            logger.error(f"Failed to fix speaker names: {fix_error}")
                            raise e
                    raise
            
            def get_format_instructions(self):
                return self._original.get_format_instructions()
        
        return FixingSpeakerNamesParser(original_parser, speaker_names)
    
    # Apply the patch
    podcast_core.create_validated_transcript_parser = _patched_create_validated_transcript_parser
    logger.info("Applied podcast-creator speaker name fixing patch")
    
except AttributeError:
    logger.warning("Could not find create_validated_transcript_parser in podcast_creator.core - skipping speaker fix patch")
except Exception as e:
    logger.warning(f"Failed to patch create_validated_transcript_parser: {e}")


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
        
        # Check if this is a Gemini model
        is_gemini = (
            (provider and provider.lower() in ['google', 'gemini']) or
            (model_name and 'gemini' in model_name.lower())
        )
        
        if is_gemini and config:
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
                f"Patched Gemini model config to disable thinking: "
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
    logger.info("Applied AIFactory.create_language patch to disable thinking for Gemini models")
    
except ImportError:
    logger.warning("Could not import esperanto.AIFactory - skipping model config patch")
except Exception as e:
    logger.warning(f"Failed to patch AIFactory.create_language: {e}")


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

        result = await create_podcast(
            content=input_data.content,
            briefing=briefing,
            episode_name=input_data.episode_name,
            output_dir=str(output_dir),
            speaker_config=speaker_profile.name,
            episode_profile=episode_profile.name,
        )

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
                logger.warning(f"Failed to update artifact records: {artifact_error}")

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
        logger.error(f"Podcast generation failed: {e}")
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
