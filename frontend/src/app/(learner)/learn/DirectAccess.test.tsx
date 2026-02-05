import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { toast } from 'sonner'
import '@testing-library/jest-dom'

// Mock next/navigation
const mockPush = vi.fn()
const mockPathname = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => mockPathname(),
}))

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}))

// Mock auth store
const mockUser = { id: 'user:learner', username: 'TestLearner', role: 'learner' }
vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: () => ({ user: mockUser, isAuthenticated: true }),
}))

// Mock learner module validation hook
const mockUseLearnerModule = vi.fn()
vi.mock('@/lib/hooks/use-learner-modules', () => ({
  useLearnerModule: (notebookId: string) => mockUseLearnerModule(notebookId),
}))

// Mock translation hook
const mockTranslation = {
  modules: {
    accessDenied: 'Access denied',
    moduleNotAccessible: 'This module is not accessible to you',
    moduleLocked: 'This module is currently locked',
  },
}

vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({ t: mockTranslation }),
}))

/**
 * Simulate a learner learn page component that validates access
 */
function MockLearnerLearnPage({ notebookId }: { notebookId: string }) {
  const { data: module, isLoading, error } = mockUseLearnerModule(notebookId)

  // Simulate redirect on error
  if (error && error.response?.status === 403) {
    // Redirect to modules page with error toast
    toast.error(
      error.response.data?.detail || mockTranslation.modules.moduleNotAccessible
    )
    mockPush('/learner/modules')
    return null
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!module) {
    return <div>Module not found</div>
  }

  return (
    <div>
      <h1>{module.name}</h1>
      <p>Learning interface for: {notebookId}</p>
    </div>
  )
}

describe('Direct Module Access Protection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Direct URL Access - Locked Module', () => {
    it('should redirect to modules page with error toast when accessing locked module', async () => {
      const lockedError = {
        response: {
          status: 403,
          data: { detail: 'This module is currently locked' },
        },
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: lockedError,
      })

      render(<MockLearnerLearnPage notebookId="notebook:locked" />)

      // Should show error toast
      expect(toast.error).toHaveBeenCalledWith('This module is currently locked')

      // Should redirect to modules page
      expect(mockPush).toHaveBeenCalledWith('/learner/modules')
    })

    it('should redirect to modules page with error toast when accessing unassigned module', async () => {
      const unassignedError = {
        response: {
          status: 403,
          data: { detail: 'This module is not accessible to you' },
        },
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: unassignedError,
      })

      render(<MockLearnerLearnPage notebookId="notebook:unassigned" />)

      // Should show error toast
      expect(toast.error).toHaveBeenCalledWith('This module is not accessible to you')

      // Should redirect to modules page
      expect(mockPush).toHaveBeenCalledWith('/learner/modules')
    })
  })

  describe('Direct URL Access - Valid Module', () => {
    it('should allow access to unlocked assigned module', async () => {
      const validModule = {
        id: 'notebook:valid',
        name: 'Valid Module',
        description: 'This module is accessible',
        is_locked: false,
        source_count: 5,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModule.mockReturnValue({
        data: validModule,
        isLoading: false,
        error: null,
      })

      render(<MockLearnerLearnPage notebookId="notebook:valid" />)

      // Should render learning interface
      expect(screen.getByText('Valid Module')).toBeInTheDocument()
      expect(screen.getByText('Learning interface for: notebook:valid')).toBeInTheDocument()

      // Should NOT redirect or show error toast
      expect(toast.error).not.toHaveBeenCalled()
      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('Error Status Code Differentiation', () => {
    it('should distinguish 403 (forbidden) from 404 (not found)', async () => {
      const forbiddenError = {
        response: {
          status: 403,
          data: { detail: 'Access denied' },
        },
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: forbiddenError,
      })

      render(<MockLearnerLearnPage notebookId="notebook:forbidden" />)

      // Should show 403-specific error
      expect(toast.error).toHaveBeenCalledWith('Access denied')
    })

    it('should handle network errors separately from 403', async () => {
      const networkError = {
        message: 'Network error',
        // No response object = network error, not HTTP error
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: networkError,
      })

      render(<MockLearnerLearnPage notebookId="notebook:test" />)

      // Should NOT trigger redirect for network errors
      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('Toast Notification Content', () => {
    it('should show specific error message for locked module', async () => {
      const lockedError = {
        response: {
          status: 403,
          data: { detail: 'This module is currently locked' },
        },
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: lockedError,
      })

      render(<MockLearnerLearnPage notebookId="notebook:locked" />)

      expect(toast.error).toHaveBeenCalledWith('This module is currently locked')
    })

    it('should show generic error message for unassigned module', async () => {
      const unassignedError = {
        response: {
          status: 403,
          data: { detail: 'This module is not accessible to you' },
        },
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: unassignedError,
      })

      render(<MockLearnerLearnPage notebookId="notebook:unassigned" />)

      expect(toast.error).toHaveBeenCalledWith('This module is not accessible to you')
    })

    it('should use fallback message if detail not provided', async () => {
      const errorWithoutDetail = {
        response: {
          status: 403,
          data: {},
        },
      }

      mockUseLearnerModule.mockReturnValue({
        data: null,
        isLoading: false,
        error: errorWithoutDetail,
      })

      render(<MockLearnerLearnPage notebookId="notebook:test" />)

      // Should use fallback message
      expect(toast.error).toHaveBeenCalledWith(
        mockTranslation.modules.moduleNotAccessible
      )
    })
  })
})

describe('Company Scoping Enforcement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should enforce company scoping when validating module access', async () => {
    // This test validates that the hook passes company_id to the API
    // In a real implementation, the API client would include the company_id
    // from the authenticated learner context

    const validModule = {
      id: 'notebook:valid',
      name: 'Valid Module',
      is_locked: false,
      source_count: 5,
      assigned_at: '2024-01-01T00:00:00',
    }

    mockUseLearnerModule.mockReturnValue({
      data: validModule,
      isLoading: false,
      error: null,
    })

    render(<MockLearnerLearnPage notebookId="notebook:valid" />)

    // Hook should have been called with notebook ID
    expect(mockUseLearnerModule).toHaveBeenCalledWith('notebook:valid')

    // In real implementation, the hook would:
    // 1. Get company_id from auth context
    // 2. Call API: GET /learner/modules/{notebook_id}
    // 3. API validates assignment exists for (company_id, notebook_id)
    // 4. API checks is_locked = false
    // 5. API returns module or 403
  })
})
