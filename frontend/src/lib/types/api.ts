export interface NotebookResponse {
  id: string
  name: string
  description: string
  archived: boolean
  published: boolean
  created: string
  updated: string
  source_count: number
  note_count: number
  objectives_count: number
  has_prompt: boolean
}

export interface NoteResponse {
  id: string
  title: string | null
  content: string | null
  note_type: string | null
  created: string
  updated: string
}

export interface SourceListResponse {
  id: string
  title: string | null
  topics?: string[]                  // Make optional to match Python API
  asset: {
    file_path?: string
    url?: string
  } | null
  embedded: boolean
  embedded_chunks: number            // ADD: From Python API
  insights_count: number
  created: string
  updated: string
  file_available?: boolean
  // ADD: Async processing fields from Python API
  command_id?: string
  status?: string
  processing_info?: Record<string, unknown>
}

export interface SourceDetailResponse extends SourceListResponse {
  full_text: string
  notebooks?: string[]  // List of notebook IDs this source is linked to
}

export type SourceResponse = SourceDetailResponse

export interface SourceStatusResponse {
  status?: string
  message: string
  processing_info?: Record<string, unknown>
  command_id?: string
}

export interface SettingsResponse {
  default_content_processing_engine_doc?: string
  default_content_processing_engine_url?: string
  default_embedding_option?: string
  auto_delete_files?: string
  youtube_preferred_languages?: string[]
}

export interface CreateNotebookRequest {
  name: string
  description?: string
}

export interface UpdateNotebookRequest {
  name?: string
  description?: string
  archived?: boolean
}

export interface CreateNoteRequest {
  title?: string
  content: string
  note_type?: string
  notebook_id?: string
}

export interface CreateSourceRequest {
  // Backward compatibility: support old single notebook_id
  notebook_id?: string
  // New multi-notebook support
  notebooks?: string[]
  // Required fields
  type: 'link' | 'upload' | 'text'
  url?: string
  file_path?: string
  content?: string
  title?: string
  transformations?: string[]
  embed?: boolean
  delete_source?: boolean
  // New async processing support
  async_processing?: boolean
}

export interface UpdateNoteRequest {
  title?: string
  content?: string
  note_type?: string
}

export interface UpdateSourceRequest {
  title?: string
  type?: 'link' | 'upload' | 'text'
  url?: string
  content?: string
}

export interface APIError {
  detail: string
}

// Source Chat Types
// Base session interface with common fields
export interface BaseChatSession {
  id: string
  title: string
  created: string
  updated: string
  message_count?: number
  model_override?: string | null
}

export interface SourceChatSession extends BaseChatSession {
  source_id: string
  model_override?: string
}

export interface SourceChatMessage {
  id: string
  type: 'human' | 'ai'
  content: string
  timestamp?: string
}

export interface SourceChatContextIndicator {
  sources: string[]
  insights: string[]
  notes: string[]
}

export interface SourceChatSessionWithMessages extends SourceChatSession {
  messages: SourceChatMessage[]
  context_indicators?: SourceChatContextIndicator
}

export interface CreateSourceChatSessionRequest {
  source_id: string
  title?: string
  model_override?: string
}

export interface UpdateSourceChatSessionRequest {
  title?: string
  model_override?: string
}

export interface SendMessageRequest {
  message: string
  model_override?: string
}

export interface SourceChatStreamEvent {
  type: 'user_message' | 'ai_message' | 'context_indicators' | 'complete' | 'error'
  content?: string
  data?: unknown
  message?: string
  timestamp?: string
}

// Notebook Chat Types
export interface NotebookChatSession extends BaseChatSession {
  notebook_id: string
}

export interface NotebookChatMessage {
  id: string
  type: 'human' | 'ai'
  content: string
  timestamp?: string
}

export interface NotebookChatSessionWithMessages extends NotebookChatSession {
  messages: NotebookChatMessage[]
}

export interface CreateNotebookChatSessionRequest {
  notebook_id: string
  title?: string
  model_override?: string
}

export interface UpdateNotebookChatSessionRequest {
  title?: string
  model_override?: string | null
}

export interface SendNotebookChatMessageRequest {
  session_id: string
  message: string
  context: {
    sources: Array<Record<string, unknown>>
    notes: Array<Record<string, unknown>>
  }
  model_override?: string
}

export interface BuildContextRequest {
  notebook_id: string
  context_config: {
    sources: Record<string, string>
    notes: Record<string, string>
  }
}

export interface BuildContextResponse {
  context: {
    sources: Array<Record<string, unknown>>
    notes: Array<Record<string, unknown>>
  }
  token_count: number
  char_count: number
}

// User management types
export interface UserListResponse {
  id: string
  username: string
  email: string
  role: 'admin' | 'learner'
  company_id: string | null
  company_name: string | null
  onboarding_completed: boolean
  created: string
  updated: string
}

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  role: 'admin' | 'learner'
  company_id?: string
}

export interface UpdateUserRequest {
  username?: string
  email?: string
  password?: string
  role?: 'admin' | 'learner'
  company_id?: string | null
  onboarding_completed?: boolean
}

// Company management types
export interface CompanyResponse {
  id: string
  name: string
  slug: string
  description: string | null
  user_count: number
  assignment_count: number
  created: string
  updated: string
}

export interface CreateCompanyRequest {
  name: string
  slug: string
  description?: string
}

export interface UpdateCompanyRequest {
  name?: string
  slug?: string
  description?: string
}

// Onboarding types
export type AIFamiliarity = 'never_used' | 'used_occasionally' | 'use_regularly' | 'power_user'

export interface OnboardingSubmit {
  ai_familiarity: AIFamiliarity
  job_type: string
  job_description: string
}

export interface OnboardingResponse {
  success: boolean
  message: string
  profile: {
    ai_familiarity: AIFamiliarity
    job_type: string
    job_description: string
  }
}

// Module Assignment types
export interface ModuleAssignmentResponse {
  id: string
  company_id: string
  notebook_id: string
  is_locked: boolean
  assigned_at: string | null
  assigned_by: string | null
  warning: string | null
}

export interface AssignmentToggleResponse {
  action: 'assigned' | 'unassigned'
  company_id: string
  notebook_id: string
  assignment_id?: string
  warning?: string
}

export interface AssignmentMatrixCell {
  is_assigned: boolean
  is_locked: boolean
  assignment_id: string | null
}

export interface CompanySummary {
  id: string
  name: string
  slug: string
}

export interface NotebookSummary {
  id: string
  name: string
  published: boolean
}

export interface AssignmentMatrixResponse {
  companies: CompanySummary[]
  notebooks: NotebookSummary[]
  assignments: Record<string, Record<string, AssignmentMatrixCell>>
}

// Learner module types (Story 2.3: Module Lock/Unlock)
export interface LearnerModule {
  id: string
  name: string
  description: string | null
  is_locked: boolean
  source_count: number
  assigned_at: string
}

// Learning Objectives types (Story 3.3: Learning Objectives Configuration)
export interface LearningObjectiveResponse {
  id: string
  notebook_id: string
  text: string
  order: number
  auto_generated: boolean
  created: string
  updated: string
}

export interface CreateLearningObjectiveRequest {
  text: string
  order?: number
}

export interface UpdateLearningObjectiveRequest {
  text?: string
}

export interface ReorderLearningObjectivesRequest {
  objectives: Array<{
    id: string
    order: number
  }>
}

export interface BatchGenerationResponse {
  status: 'completed' | 'error'
  objective_ids?: string[]
  error?: string
}

// Module Prompt types (Story 3.4: AI Teacher Prompt Configuration)
export interface ModulePrompt {
  id: string
  notebook_id: string
  system_prompt: string | null
  updated_by: string
  updated_at: string
}

export interface ModulePromptUpdate {
  system_prompt: string | null
}
