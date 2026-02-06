import { describe, it, expect } from 'vitest'
import { formatLearnerError, isRecoverableError, type ErrorType } from '../error-handler'

describe('formatLearnerError', () => {
  it('maps known error_type to correct i18n key', () => {
    const errorTypes: Record<ErrorType, string> = {
      not_found: 'learnerErrors.notFound',
      access_denied: 'learnerErrors.accessDenied',
      service_error: 'learnerErrors.generic',
      validation: 'learnerErrors.generic',
      not_ready: 'learnerErrors.notReady',
      network: 'learnerErrors.networkError',
      timeout: 'learnerErrors.timeout',
      unknown: 'learnerErrors.generic',
    }

    for (const [errorType, expectedKey] of Object.entries(errorTypes)) {
      const result = formatLearnerError({ error_type: errorType })
      expect(result).toBe(expectedKey)
    }
  })

  it('returns generic key for unknown/unstructured error', () => {
    expect(formatLearnerError(null)).toBe('learnerErrors.generic')
    expect(formatLearnerError(undefined)).toBe('learnerErrors.generic')
    expect(formatLearnerError('some raw string')).toBe('learnerErrors.generic')
    expect(formatLearnerError(42)).toBe('learnerErrors.generic')
  })

  it('handles nested Axios error structures', () => {
    // Axios 403 error
    const axiosError403 = {
      response: {
        status: 403,
        data: { detail: 'Not authorized' },
      },
    }
    expect(formatLearnerError(axiosError403)).toBe('learnerErrors.accessDenied')

    // Axios 404 error
    const axiosError404 = {
      response: {
        status: 404,
        data: { detail: 'Not found' },
      },
    }
    expect(formatLearnerError(axiosError404)).toBe('learnerErrors.notFound')

    // Axios 500 error
    const axiosError500 = {
      response: {
        status: 500,
        data: { detail: 'Internal Server Error' },
      },
    }
    expect(formatLearnerError(axiosError500)).toBe('learnerErrors.generic')

    // Axios network error
    const networkError = {
      code: 'ERR_NETWORK',
      message: 'Network Error',
    }
    expect(formatLearnerError(networkError)).toBe('learnerErrors.networkError')

    // Axios timeout error
    const timeoutError = {
      code: 'ECONNABORTED',
      message: 'timeout of 10000ms exceeded',
    }
    expect(formatLearnerError(timeoutError)).toBe('learnerErrors.timeout')
  })

  it('never returns raw error messages - always i18n keys', () => {
    // Errors with technical details should still return i18n keys
    const technicalError = {
      error: 'Source source:abc123 not found in database',
      error_type: 'not_found',
      recoverable: true,
    }
    const result = formatLearnerError(technicalError)
    expect(result).toMatch(/^learnerErrors\./)
    expect(result).not.toContain('source:abc123')

    // Nested response data with error_type
    const nestedError = {
      response: {
        status: 422,
        data: {
          error: 'Validation failed for field X',
          error_type: 'validation',
        },
      },
    }
    const nestedResult = formatLearnerError(nestedError)
    expect(nestedResult).toMatch(/^learnerErrors\./)
  })
})

describe('isRecoverableError', () => {
  it('returns true for explicitly recoverable structured errors', () => {
    expect(isRecoverableError({ recoverable: true })).toBe(true)
    expect(isRecoverableError({ recoverable: false })).toBe(false)
  })

  it('returns true for network errors (typically recoverable)', () => {
    expect(isRecoverableError({ code: 'ERR_NETWORK' })).toBe(true)
    expect(isRecoverableError({ code: 'ECONNABORTED' })).toBe(true)
  })

  it('returns false for null/undefined/non-object', () => {
    expect(isRecoverableError(null)).toBe(false)
    expect(isRecoverableError(undefined)).toBe(false)
    expect(isRecoverableError('string')).toBe(false)
  })

  it('checks nested response data for recoverability', () => {
    const axiosError = {
      response: {
        data: { recoverable: true },
      },
    }
    expect(isRecoverableError(axiosError)).toBe(true)
  })
})
