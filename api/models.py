from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Module Assignment models
class ModuleAssignmentCreate(BaseModel):
    """Create a new module assignment."""

    company_id: str = Field(..., description="Company ID to assign module to")
    notebook_id: str = Field(..., description="Notebook/module ID to assign")


class ModuleAssignmentResponse(BaseModel):
    """Module assignment response with optional warning."""

    id: str
    company_id: str
    notebook_id: str
    is_locked: bool = False
    assigned_at: Optional[str] = None
    assigned_by: Optional[str] = None
    warning: Optional[str] = None  # Warning message for unpublished modules


class AssignmentToggleRequest(BaseModel):
    """Toggle assignment request."""

    company_id: str = Field(..., description="Company ID")
    notebook_id: str = Field(..., description="Notebook/module ID")


class AssignmentToggleResponse(BaseModel):
    """Toggle assignment response."""

    action: str  # "assigned" or "unassigned"
    company_id: str
    notebook_id: str
    assignment_id: Optional[str] = None  # Present when action is "assigned"
    warning: Optional[str] = None  # Warning for unpublished modules


class AssignmentMatrixCell(BaseModel):
    """Single cell in the assignment matrix."""

    is_assigned: bool
    is_locked: bool = False
    assignment_id: Optional[str] = None


class ModuleAssignmentLockRequest(BaseModel):
    """Request body for toggling module lock status."""

    is_locked: bool = Field(
        ..., description="Whether module should be locked (True) or unlocked (False)"
    )


class LearnerModuleResponse(BaseModel):
    """Module representation for learner view (excludes admin fields)."""

    id: str
    name: str
    description: Optional[str] = None
    is_locked: bool
    source_count: int
    assigned_at: str
    # DO NOT include assigned_by — learners don't see admin info


class CompanySummary(BaseModel):
    """Company summary for matrix view."""

    id: str
    name: str
    slug: str


class NotebookSummary(BaseModel):
    """Notebook summary for matrix view."""

    id: str
    name: str
    published: bool = True


class AssignmentMatrixResponse(BaseModel):
    """Assignment matrix for admin UI."""

    companies: List[CompanySummary]
    notebooks: List[NotebookSummary]
    assignments: Dict[str, Dict[str, AssignmentMatrixCell]]  # {company_id: {notebook_id: cell}}


# Auth models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Username (min 3 characters)")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    company_id: Optional[str] = None
    onboarding_completed: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    jwt_enabled: bool


# Admin user management models
class AdminUserCreate(BaseModel):
    """Admin creates a new user with role and optional company."""

    username: str = Field(..., min_length=3, description="Username (min 3 characters)")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    role: Literal["admin", "learner"] = Field(
        "learner", description="User role (admin or learner)"
    )
    company_id: Optional[str] = Field(None, description="Company ID for learners")


class UserUpdate(BaseModel):
    """Update user fields (admin only)."""

    username: Optional[str] = Field(None, min_length=3, description="Username")
    email: Optional[str] = Field(None, description="Email address")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    role: Optional[Literal["admin", "learner"]] = Field(None, description="User role")
    company_id: Optional[str] = Field(None, description="Company ID")
    onboarding_completed: Optional[bool] = Field(
        None, description="Onboarding completion status"
    )


class UserListResponse(BaseModel):
    """User with company name for list views."""

    id: str
    username: str
    email: str
    role: str
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    onboarding_completed: bool = False
    created: str
    updated: str


# Company models
class CompanyCreate(BaseModel):
    """Create a new company."""

    name: str = Field(..., min_length=1, description="Company name")
    slug: Optional[str] = Field(None, min_length=1, description="Unique slug (auto-generated if omitted)")


class CompanyUpdate(BaseModel):
    """Update company fields."""

    name: Optional[str] = Field(None, min_length=1, description="Company name")
    slug: Optional[str] = Field(None, min_length=1, description="Unique slug")


class CompanyResponse(BaseModel):
    """Company response with user and assignment counts."""

    id: str
    name: str
    slug: str
    user_count: int = 0  # Number of users/learners assigned to this company
    assignment_count: int = 0  # Number of module assignments for this company
    created: str
    updated: str


# Onboarding models
class OnboardingSubmit(BaseModel):
    """Learner onboarding questionnaire submission."""

    ai_familiarity: Literal[
        "never_used", "used_occasionally", "use_regularly", "power_user"
    ] = Field(..., description="Level of AI familiarity")
    job_type: str = Field(..., min_length=1, description="Job title or role")
    job_description: str = Field(
        ..., min_length=10, description="Brief description of job responsibilities"
    )


class OnboardingResponse(BaseModel):
    """Response after completing onboarding."""

    success: bool
    message: str
    profile: Dict[str, Any]


# Notebook models
class NotebookCreate(BaseModel):
    name: str = Field(..., description="Name of the notebook")
    description: str = Field(default="", description="Description of the notebook")


class NotebookUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the notebook")
    description: Optional[str] = Field(None, description="Description of the notebook")
    archived: Optional[bool] = Field(
        None, description="Whether the notebook is archived"
    )


class NotebookResponse(BaseModel):
    id: str
    name: str
    description: str
    archived: bool
    published: bool  # Whether the notebook is published (visible to learners)
    created: str
    updated: str
    source_count: int
    note_count: int
    objectives_count: int = 0  # Count of learning objectives (Story 3.3)
    has_prompt: bool = False  # Whether module has custom AI prompt configured (Story 3.4)


# Document Upload models (Story 3.1)
class DocumentUploadResponse(BaseModel):
    """Response after uploading a document to a notebook."""

    id: str = Field(..., description="Source ID")
    title: str = Field(..., description="Document title")
    status: str = Field(..., description="Processing status (processing, completed, error)")
    command_id: Optional[str] = Field(None, description="Async job command ID for status polling")


class DocumentStatusResponse(BaseModel):
    """Status of a document being processed."""

    id: str = Field(..., description="Source ID")
    title: str = Field(..., description="Document title")
    status: str = Field(..., description="Processing status (pending, processing, completed, error)")
    command_id: Optional[str] = Field(None, description="Async job command ID")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    created: Optional[str] = Field(None, description="Creation timestamp")
    updated: Optional[str] = Field(None, description="Last update timestamp")


# Search models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    type: Literal["text", "vector"] = Field("text", description="Search type")
    limit: int = Field(100, description="Maximum number of results", le=1000)
    search_sources: bool = Field(True, description="Include sources in search")
    search_notes: bool = Field(True, description="Include notes in search")
    minimum_score: float = Field(
        0.2, description="Minimum score for vector search", ge=0, le=1
    )


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    search_type: str = Field(..., description="Type of search performed")


class AskRequest(BaseModel):
    question: str = Field(..., description="Question to ask the knowledge base")
    strategy_model: str = Field(..., description="Model ID for query strategy")
    answer_model: str = Field(..., description="Model ID for individual answers")
    final_answer_model: str = Field(..., description="Model ID for final answer")


class AskResponse(BaseModel):
    answer: str = Field(..., description="Final answer from the knowledge base")
    question: str = Field(..., description="Original question")


# Models API models
class ModelCreate(BaseModel):
    name: str = Field(..., description="Model name (e.g., gpt-5-mini, claude, gemini)")
    provider: str = Field(
        ..., description="Provider name (e.g., openai, anthropic, gemini)"
    )
    type: str = Field(
        ...,
        description="Model type (language, embedding, text_to_speech, speech_to_text)",
    )


class ModelResponse(BaseModel):
    id: str
    name: str
    provider: str
    type: str
    created: str
    updated: str


class DefaultModelsResponse(BaseModel):
    default_chat_model: Optional[str] = None
    default_transformation_model: Optional[str] = None
    large_context_model: Optional[str] = None
    default_text_to_speech_model: Optional[str] = None
    default_speech_to_text_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    default_tools_model: Optional[str] = None


class ProviderAvailabilityResponse(BaseModel):
    available: List[str] = Field(..., description="List of available providers")
    unavailable: List[str] = Field(..., description="List of unavailable providers")
    supported_types: Dict[str, List[str]] = Field(
        ..., description="Provider to supported model types mapping"
    )


# Transformations API models
class TransformationCreate(BaseModel):
    name: str = Field(..., description="Transformation name")
    title: str = Field(..., description="Display title for the transformation")
    description: str = Field(
        ..., description="Description of what this transformation does"
    )
    prompt: str = Field(..., description="The transformation prompt")
    apply_default: bool = Field(
        False, description="Whether to apply this transformation by default"
    )


class TransformationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Transformation name")
    title: Optional[str] = Field(
        None, description="Display title for the transformation"
    )
    description: Optional[str] = Field(
        None, description="Description of what this transformation does"
    )
    prompt: Optional[str] = Field(None, description="The transformation prompt")
    apply_default: Optional[bool] = Field(
        None, description="Whether to apply this transformation by default"
    )


class TransformationResponse(BaseModel):
    id: str
    name: str
    title: str
    description: str
    prompt: str
    apply_default: bool
    created: str
    updated: str


class TransformationExecuteRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transformation_id: str = Field(
        ..., description="ID of the transformation to execute"
    )
    input_text: str = Field(..., description="Text to transform")
    model_id: str = Field(..., description="Model ID to use for the transformation")


class TransformationExecuteResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    output: str = Field(..., description="Transformed text")
    transformation_id: str = Field(..., description="ID of the transformation used")
    model_id: str = Field(..., description="Model ID used")


# Default Prompt API models
class DefaultPromptResponse(BaseModel):
    transformation_instructions: str = Field(
        ..., description="Default transformation instructions"
    )


class DefaultPromptUpdate(BaseModel):
    transformation_instructions: str = Field(
        ..., description="Default transformation instructions"
    )


# Notes API models
class NoteCreate(BaseModel):
    title: Optional[str] = Field(None, description="Note title")
    content: str = Field(..., description="Note content")
    note_type: Optional[str] = Field("human", description="Type of note (human, ai)")
    notebook_id: Optional[str] = Field(
        None, description="Notebook ID to add the note to"
    )


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Note title")
    content: Optional[str] = Field(None, description="Note content")
    note_type: Optional[str] = Field(None, description="Type of note (human, ai)")


class NoteResponse(BaseModel):
    id: str
    title: Optional[str]
    content: Optional[str]
    note_type: Optional[str]
    created: str
    updated: str


# Embedding API models
class EmbedRequest(BaseModel):
    item_id: str = Field(..., description="ID of the item to embed")
    item_type: str = Field(..., description="Type of item (source, note)")
    async_processing: bool = Field(
        False, description="Process asynchronously in background"
    )


class EmbedResponse(BaseModel):
    success: bool = Field(..., description="Whether embedding was successful")
    message: str = Field(..., description="Result message")
    item_id: str = Field(..., description="ID of the item that was embedded")
    item_type: str = Field(..., description="Type of item that was embedded")
    command_id: Optional[str] = Field(
        None, description="Command ID for async processing"
    )


# Rebuild request/response models
class RebuildRequest(BaseModel):
    mode: Literal["existing", "all"] = Field(
        ...,
        description="Rebuild mode: 'existing' only re-embeds items with embeddings, 'all' embeds everything",
    )
    include_sources: bool = Field(True, description="Include sources in rebuild")
    include_notes: bool = Field(True, description="Include notes in rebuild")
    include_insights: bool = Field(True, description="Include insights in rebuild")


class RebuildResponse(BaseModel):
    command_id: str = Field(..., description="Command ID to track progress")
    total_items: int = Field(..., description="Estimated number of items to process")
    message: str = Field(..., description="Status message")


class RebuildProgress(BaseModel):
    processed: int = Field(..., description="Number of items processed")
    total: int = Field(..., description="Total items to process")
    percentage: float = Field(..., description="Progress percentage")


class RebuildStats(BaseModel):
    sources: int = Field(0, description="Sources processed")
    notes: int = Field(0, description="Notes processed")
    insights: int = Field(0, description="Insights processed")
    failed: int = Field(0, description="Failed items")


class RebuildStatusResponse(BaseModel):
    command_id: str = Field(..., description="Command ID")
    status: str = Field(..., description="Status: queued, running, completed, failed")
    progress: Optional[RebuildProgress] = None
    stats: Optional[RebuildStats] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


# Settings API models
class SettingsResponse(BaseModel):
    default_content_processing_engine_doc: Optional[str] = None
    default_content_processing_engine_url: Optional[str] = None
    default_embedding_option: Optional[str] = None
    auto_delete_files: Optional[str] = None
    youtube_preferred_languages: Optional[List[str]] = None


class SettingsUpdate(BaseModel):
    default_content_processing_engine_doc: Optional[str] = None
    default_content_processing_engine_url: Optional[str] = None
    default_embedding_option: Optional[str] = None
    auto_delete_files: Optional[str] = None
    youtube_preferred_languages: Optional[List[str]] = None


# Sources API models
class AssetModel(BaseModel):
    file_path: Optional[str] = None
    url: Optional[str] = None


class SourceCreate(BaseModel):
    # Backward compatibility: support old single notebook_id
    notebook_id: Optional[str] = Field(
        None, description="Notebook ID to add the source to (deprecated, use notebooks)"
    )
    # New multi-notebook support
    notebooks: Optional[List[str]] = Field(
        None, description="List of notebook IDs to add the source to"
    )
    # Required fields
    type: str = Field(..., description="Source type: link, upload, or text")
    url: Optional[str] = Field(None, description="URL for link type")
    file_path: Optional[str] = Field(None, description="File path for upload type")
    content: Optional[str] = Field(None, description="Text content for text type")
    title: Optional[str] = Field(None, description="Source title")
    transformations: Optional[List[str]] = Field(
        default_factory=list, description="Transformation IDs to apply"
    )
    embed: bool = Field(False, description="Whether to embed content for vector search")
    delete_source: bool = Field(
        False, description="Whether to delete uploaded file after processing"
    )
    # New async processing support
    async_processing: bool = Field(
        False, description="Whether to process source asynchronously"
    )

    @model_validator(mode="after")
    def validate_notebook_fields(self):
        # Ensure only one of notebook_id or notebooks is provided
        if self.notebook_id is not None and self.notebooks is not None:
            raise ValueError(
                "Cannot specify both 'notebook_id' and 'notebooks'. Use 'notebooks' for multi-notebook support."
            )

        # Convert single notebook_id to notebooks array for internal processing
        if self.notebook_id is not None:
            self.notebooks = [self.notebook_id]
            # Keep notebook_id for backward compatibility in response

        # Set empty array if no notebooks specified (allow sources without notebooks)
        if self.notebooks is None:
            self.notebooks = []

        return self


class SourceUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Source title")
    topics: Optional[List[str]] = Field(None, description="Source topics")


class SourceResponse(BaseModel):
    id: str
    title: Optional[str]
    topics: Optional[List[str]]
    asset: Optional[AssetModel]
    full_text: Optional[str]
    embedded: bool
    embedded_chunks: int
    file_available: Optional[bool] = None
    created: str
    updated: str
    # New fields for async processing
    command_id: Optional[str] = None
    status: Optional[str] = None
    processing_info: Optional[Dict] = None
    # Notebook associations
    notebooks: Optional[List[str]] = None


class SourceListResponse(BaseModel):
    id: str
    title: Optional[str]
    topics: Optional[List[str]]
    asset: Optional[AssetModel]
    embedded: bool  # Boolean flag indicating if source has embeddings
    embedded_chunks: int  # Number of embedded chunks
    insights_count: int
    created: str
    updated: str
    file_available: Optional[bool] = None
    # Status fields for async processing
    command_id: Optional[str] = None
    status: Optional[str] = None
    processing_info: Optional[Dict[str, Any]] = None


# Context API models
class ContextConfig(BaseModel):
    sources: Dict[str, str] = Field(
        default_factory=dict, description="Source inclusion config {source_id: level}"
    )
    notes: Dict[str, str] = Field(
        default_factory=dict, description="Note inclusion config {note_id: level}"
    )


class ContextRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID to get context for")
    context_config: Optional[ContextConfig] = Field(
        None, description="Context configuration"
    )


class ContextResponse(BaseModel):
    notebook_id: str
    sources: List[Dict[str, Any]] = Field(..., description="Source context data")
    notes: List[Dict[str, Any]] = Field(..., description="Note context data")
    total_tokens: Optional[int] = Field(None, description="Estimated token count")


# Insights API models
class SourceInsightResponse(BaseModel):
    id: str
    source_id: str
    insight_type: str
    content: str
    created: str
    updated: str


class SaveAsNoteRequest(BaseModel):
    notebook_id: Optional[str] = Field(None, description="Notebook ID to add note to")


class CreateSourceInsightRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transformation_id: str = Field(..., description="ID of transformation to apply")
    model_id: Optional[str] = Field(
        None, description="Model ID (uses default if not provided)"
    )


# Source status response
class SourceStatusResponse(BaseModel):
    status: Optional[str] = Field(None, description="Processing status")
    message: str = Field(..., description="Descriptive message about the status")
    processing_info: Optional[Dict[str, Any]] = Field(
        None, description="Detailed processing information"
    )
    command_id: Optional[str] = Field(None, description="Command ID if available")


# Error response
class ErrorResponse(BaseModel):
    error: str
    message: str


# Batch artifact generation models (Story 3.2)
class BatchGenerationRequest(BaseModel):
    """Request to generate all artifacts for a notebook."""

    notebook_id: str = Field(..., description="Notebook ID to generate artifacts for")
    options: Optional[Dict[str, Any]] = Field(
        None, description="Optional generation options per artifact type"
    )


class ArtifactGenerationResult(BaseModel):
    """Result of a single artifact generation."""

    status: Literal["pending", "processing", "completed", "error"] = Field(
        ..., description="Generation status"
    )
    id: Optional[str] = Field(None, description="Artifact ID if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchGenerationResponse(BaseModel):
    """Response from batch artifact generation."""

    notebook_id: str
    quiz: ArtifactGenerationResult
    summary: ArtifactGenerationResult
    transformations: Dict[str, Any] = Field(
        default_factory=dict, description="Transformation generation results"
    )
    podcast: Dict[str, Any] = Field(
        default_factory=dict, description="Podcast generation results with command_id"
    )


# Artifact preview models (Story 3.2)
class QuizPreviewResponse(BaseModel):
    """Preview response for quiz artifacts."""

    artifact_type: str = "quiz"
    id: str
    title: str
    question_count: int
    questions: List[Dict[str, Any]] = Field(..., description="Quiz questions with answers")


class PodcastPreviewResponse(BaseModel):
    """Preview response for podcast artifacts."""

    artifact_type: str = "podcast"
    id: str
    title: str
    duration: Optional[str] = Field(None, description="Audio duration")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    transcript: Optional[str] = Field(None, description="Episode transcript")


class SummaryPreviewResponse(BaseModel):
    """Preview response for summary artifacts."""

    artifact_type: str = "summary"
    id: str
    title: str
    word_count: int
    content: str = Field(..., description="Summary markdown content")


class TransformationPreviewResponse(BaseModel):
    """Preview response for transformation artifacts."""

    artifact_type: str = "transformation"
    id: str
    title: str
    word_count: int
    content: str = Field(..., description="Transformed content")
    transformation_name: Optional[str] = Field(
        None, description="Name of the transformation applied"
    )


class ArtifactPreviewResponse(BaseModel):
    """Generic artifact preview response (union type)."""

    artifact_type: Literal["quiz", "podcast", "summary", "transformation"]
    data: Dict[str, Any] = Field(..., description="Type-specific preview data")


# Artifact regeneration models (Story 3.2)
class RegenerateArtifactRequest(BaseModel):
    """Request to regenerate an artifact."""

    options: Optional[Dict[str, Any]] = Field(
        None, description="Optional regeneration options"
    )


class RegenerateArtifactResponse(BaseModel):
    """Response from artifact regeneration."""

    artifact_id: str
    status: Literal["pending", "processing", "completed", "error"]
    message: str
    new_artifact_id: Optional[str] = Field(
        None, description="New artifact ID if regeneration started"
    )
    command_id: Optional[str] = Field(
        None, description="Command ID for async operations"
    )


# Learning Objectives API models (Story 3.3)
class LearningObjectiveCreate(BaseModel):
    """Create a new learning objective."""

    text: str = Field(..., description="Objective text (measurable, action-verb based)")
    order: int = Field(0, description="Display order (0-indexed)")


class LearningObjectiveUpdate(BaseModel):
    """Update an existing learning objective."""

    text: Optional[str] = Field(None, description="New objective text")


class LearningObjectiveResponse(BaseModel):
    """Learning objective response."""

    id: str
    notebook_id: str
    text: str
    order: int
    auto_generated: bool
    created: Optional[str] = None
    updated: Optional[str] = None


class LearningObjectiveReorder(BaseModel):
    """Reorder learning objectives."""

    objectives: List[Dict[str, int]] = Field(
        ..., description="List of {id, order} dicts for reordering"
    )


class BatchGenerationResponse(BaseModel):
    """Response from batch generation operation."""

    status: Literal["pending", "analyzing", "generating", "saving", "completed", "failed"]
    objective_ids: Optional[List[str]] = Field(
        None, description="IDs of generated objectives if completed"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


# Module Prompt API models (Story 3.4)
class ModulePromptUpdate(BaseModel):
    """Update or create module prompt."""

    system_prompt: Optional[str] = Field(
        None,
        description="Jinja2 template for per-module AI teacher customization (None to clear)"
    )


class ModulePromptResponse(BaseModel):
    """Module prompt response."""

    id: Optional[str] = None
    notebook_id: str
    system_prompt: Optional[str] = None
    updated_by: str
    updated_at: Optional[str] = None


# ==============================================================================
# Story 4.1: Learner Chat Interface & SSE Streaming
# ==============================================================================


class LearnerChatRequest(BaseModel):
    """Request body for learner chat message."""

    message: str = Field(..., min_length=1, description="Learner's message content")


class LearnerNotebookSummary(BaseModel):
    """Notebook summary for learner view (excludes admin fields)."""

    id: str
    name: str
    description: Optional[str] = None
    is_locked: bool
    source_count: int


class LearnerSourceDocument(BaseModel):
    """Source document metadata for learner sources panel."""

    id: str
    title: str
    file_type: Optional[str] = None
    size: Optional[int] = None  # File size in bytes


# ==============================================================================
# Story 4.4: Learning Objectives Assessment & Progress Tracking
# ==============================================================================


class LearnerObjectiveProgressResponse(BaseModel):
    """Learner progress on a single learning objective."""

    user_id: str
    objective_id: str
    status: str  # "not_started" | "in_progress" | "completed"
    completed_via: Optional[str] = None  # "conversation" | "quiz"
    evidence: Optional[str] = None
    completed_at: Optional[str] = None


class ObjectiveWithProgress(BaseModel):
    """Learning objective with learner progress."""

    id: str
    notebook_id: str
    text: str
    order: int
    auto_generated: bool
    # Progress fields (null if not started)
    progress_status: Optional[str] = None
    progress_completed_at: Optional[str] = None
    progress_evidence: Optional[str] = None


class SuggestedModule(BaseModel):
    """Suggested module for learner continuation (Story 4.5)."""

    id: str
    title: str
    description: str = ""


class ObjectiveCheckOffResult(BaseModel):
    """Result of check_off_objective tool invocation."""

    objective_id: str
    objective_text: str
    evidence: str
    total_completed: int
    total_objectives: int
    all_complete: bool
    suggested_modules: List[SuggestedModule] = Field(
        default_factory=list,
        description="Suggested next modules when all objectives complete (Story 4.5)"
    )
