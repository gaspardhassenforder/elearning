/**
 * Error types returned by backend tools and APIs.
 */
export type ErrorType = 'not_found' | 'access_denied' | 'service_error' | 'validation' | 'not_ready' | 'network' | 'timeout' | 'unknown';

/**
 * Structured error response from backend.
 */
export interface StructuredError {
  error?: string;
  error_type?: ErrorType;
  recoverable?: boolean;
  detail?: string;
  message?: string;
}

/**
 * Utility to map backend English error messages to i18n keys.
 */
export const ERROR_MAP: Record<string, string> = {
  "Notebook not found": "apiErrors.notebookNotFound",
  "Source not found": "apiErrors.sourceNotFound",
  "Transformation not found": "apiErrors.transformationNotFound",
  "File upload failed": "apiErrors.fileUploadFailed",
  "URL is required for link type": "apiErrors.urlRequired",
  "Content is required for text type": "apiErrors.contentRequired",
  "Invalid source type": "apiErrors.invalidSourceType",
  "Processing failed": "apiErrors.processingFailed",
  "Failed to queue processing": "apiErrors.failedToQueue",
  "sort_by must be 'created' or 'updated'": "apiErrors.invalidSortBy",
  "sort_order must be 'asc' or 'desc'": "apiErrors.invalidSortOrder",
  "Access to file denied": "apiErrors.accessDenied",
  "File not found on server": "apiErrors.fileNotFoundOnServer",
  "Missing authorization": "apiErrors.unauthorized",
  "Invalid password": "apiErrors.invalidPassword",
  "Invalid authorization header format": "apiErrors.unauthorized",
  "Missing authorization header": "apiErrors.unauthorized",
  "Vector search requires an embedding model": "apiErrors.embeddingModelRequired",
  "Ask feature requires an embedding model": "apiErrors.embeddingModelRequired",
  "Strategy model": "apiErrors.strategyModelNotFound",
  "Answer model": "apiErrors.answerModelNotFound",
  "Final answer model": "apiErrors.finalAnswerModelNotFound",
  "No answer generated": "apiErrors.noAnswerGenerated",
  "No default": "apiErrors.noDefaultModel",
};

/**
 * Translates a backend error message using the ERROR_MAP.
 * If no mapping exists, returns the fallback key or generic error key.
 */
export function getApiErrorKey(errorOrMessage: unknown, fallbackKey?: string): string {
  const message = formatApiError(errorOrMessage);
  
  if (!message) return fallbackKey || "apiErrors.genericError";

  // Try exact match first
  if (ERROR_MAP[message]) {
    return ERROR_MAP[message];
  }

  // Try partial match for dynamic messages (e.g., "File upload failed: ...")
  for (const [key, value] of Object.entries(ERROR_MAP)) {
    if (message.startsWith(key)) {
      return value;
    }
  }

  return fallbackKey || "apiErrors.genericError";
}

/**
 * Formats a raw error from the API into a user-friendly (potentially translated) string.
 */
export function formatApiError(error: unknown): string {
  if (typeof error === 'string') return error;

  const err = error as { response?: { data?: { detail?: string } }, detail?: string, message?: string };
  const detail = err?.response?.data?.detail || err?.detail || err?.message;

  if (typeof detail === 'string') {
    return detail; // We'll handle the actual translation using the key in the hook/component
  }

  return "An unexpected error occurred";
}

/**
 * Learner-specific error type to i18n key mapping.
 * Maps error_type values to learner-friendly i18n keys.
 * Story 7.1: Comprehensive mappings for all error scenarios.
 */
const LEARNER_ERROR_TYPE_MAP: Record<ErrorType, string> = {
  not_found: "learnerErrors.notFound",
  access_denied: "learnerErrors.accessDenied",
  service_error: "learnerErrors.generic",
  validation: "learnerErrors.generic",
  not_ready: "learnerErrors.notReady",
  network: "learnerErrors.networkError",
  timeout: "learnerErrors.timeout",
  unknown: "learnerErrors.generic",
};

/**
 * Learner-specific error message to i18n key mapping.
 * Maps specific backend error messages to learner-friendly i18n keys.
 * Story 7.1: Covers chat, content, artifact, and access error scenarios.
 */
const LEARNER_ERROR_MESSAGE_MAP: Record<string, string> = {
  // Chat errors
  "I had trouble processing that": "learnerErrors.chatError",
  "I couldn't complete that action": "learnerErrors.toolFailed",
  "Connection lost": "learnerErrors.streamingError",

  // Content errors
  "I couldn't find that document": "learnerErrors.notFound",
  "I had trouble accessing that document": "learnerErrors.contentLoadFailed",
  "Couldn't load this module": "learnerErrors.moduleNotAvailable",
  "Couldn't load this content": "learnerErrors.contentLoadFailed",

  // Artifact errors
  "I couldn't find that quiz": "learnerErrors.quizLoadFailed",
  "I had trouble loading that quiz": "learnerErrors.quizLoadFailed",
  "That quiz isn't ready yet": "learnerErrors.notReady",
  "I couldn't find that podcast": "learnerErrors.podcastLoadFailed",
  "I had trouble loading that podcast": "learnerErrors.podcastLoadFailed",
  "That podcast is still being generated": "learnerErrors.notReady",
  "I had trouble generating that": "learnerErrors.artifactGenerationFailed",
  "I couldn't create that for you": "learnerErrors.artifactGenerationFailed",

  // Access errors
  "You don't have access to this content": "learnerErrors.accessDenied",
  "That quiz isn't available for you": "learnerErrors.accessDenied",
  "That podcast isn't available for you": "learnerErrors.accessDenied",
  "Access denied": "learnerErrors.accessDenied",

  // Progress errors
  "I couldn't record your progress": "learnerErrors.generic",
  "I couldn't find that learning objective": "learnerErrors.generic",
};

/**
 * Learner-specific HTTP status code to i18n key mapping.
 */
const LEARNER_STATUS_MAP: Record<number, string> = {
  400: "learnerErrors.generic",
  401: "learnerErrors.sessionExpired",
  403: "learnerErrors.accessDenied",
  404: "learnerErrors.notFound",
  408: "learnerErrors.timeout",
  429: "learnerErrors.generic",
  500: "learnerErrors.generic",
  502: "learnerErrors.generic",
  503: "learnerErrors.generic",
  504: "learnerErrors.timeout",
};

/**
 * Formats an error for learner-facing display.
 * Returns an i18n key for user-friendly error messages.
 *
 * CRITICAL: Never returns raw error messages or technical details.
 * All returned values are i18n keys that map to warm, user-friendly messages.
 *
 * Story 7.1: Enhanced with comprehensive message mapping for specific scenarios.
 *
 * @param error - The error object (AxiosError response data, structured error, or unknown)
 * @returns i18n key for the error message
 */
export function formatLearnerError(error: unknown): string {
  // Handle null/undefined
  if (!error) {
    return "learnerErrors.generic";
  }

  // Handle structured error from backend tools (has error_type)
  if (typeof error === 'object' && error !== null) {
    const structuredError = error as StructuredError;

    // Check for specific error message first (most specific)
    if (structuredError.error && typeof structuredError.error === 'string') {
      // Try exact match
      if (structuredError.error in LEARNER_ERROR_MESSAGE_MAP) {
        return LEARNER_ERROR_MESSAGE_MAP[structuredError.error];
      }
      // Try partial match for dynamic messages
      for (const [key, value] of Object.entries(LEARNER_ERROR_MESSAGE_MAP)) {
        if (structuredError.error.includes(key)) {
          return value;
        }
      }
    }

    // Check for error_type field (from tool responses)
    if (structuredError.error_type && structuredError.error_type in LEARNER_ERROR_TYPE_MAP) {
      return LEARNER_ERROR_TYPE_MAP[structuredError.error_type];
    }

    // Check detail field
    if (structuredError.detail && typeof structuredError.detail === 'string') {
      for (const [key, value] of Object.entries(LEARNER_ERROR_MESSAGE_MAP)) {
        if (structuredError.detail.includes(key)) {
          return value;
        }
      }
    }
  }

  // Handle Axios error response
  const axiosLike = error as {
    response?: { status?: number; data?: StructuredError };
    code?: string;
    message?: string;
  };

  // Check nested response data for error message
  if (axiosLike.response?.data?.error) {
    const errorMsg = axiosLike.response.data.error;
    if (typeof errorMsg === 'string' && errorMsg in LEARNER_ERROR_MESSAGE_MAP) {
      return LEARNER_ERROR_MESSAGE_MAP[errorMsg];
    }
  }

  // Check nested response data for error_type
  if (axiosLike.response?.data?.error_type) {
    const errorType = axiosLike.response.data.error_type;
    if (errorType in LEARNER_ERROR_TYPE_MAP) {
      return LEARNER_ERROR_TYPE_MAP[errorType];
    }
  }

  // Check HTTP status code
  if (axiosLike.response?.status) {
    const status = axiosLike.response.status;
    if (status in LEARNER_STATUS_MAP) {
      return LEARNER_STATUS_MAP[status];
    }
  }

  // Check for network errors (Axios error codes)
  if (axiosLike.code) {
    if (axiosLike.code === 'ECONNABORTED' || axiosLike.code === 'ETIMEDOUT') {
      return "learnerErrors.timeout";
    }
    if (axiosLike.code === 'ERR_NETWORK' || axiosLike.code === 'ERR_INTERNET_DISCONNECTED') {
      return "learnerErrors.networkError";
    }
  }

  // Default fallback
  return "learnerErrors.generic";
}

/**
 * Checks if an error is recoverable (user can retry).
 *
 * @param error - The error object
 * @returns true if the error is recoverable
 */
export function isRecoverableError(error: unknown): boolean {
  if (!error || typeof error !== 'object') {
    return false;
  }

  // Check structured error
  const structuredError = error as StructuredError;
  if (typeof structuredError.recoverable === 'boolean') {
    return structuredError.recoverable;
  }

  // Check nested response data
  const axiosLike = error as { response?: { data?: StructuredError } };
  if (typeof axiosLike.response?.data?.recoverable === 'boolean') {
    return axiosLike.response.data.recoverable;
  }

  // Network errors are typically recoverable
  const errorWithCode = error as { code?: string };
  if (errorWithCode.code === 'ERR_NETWORK' || errorWithCode.code === 'ECONNABORTED') {
    return true;
  }

  // Default: assume not recoverable
  return false;
}
