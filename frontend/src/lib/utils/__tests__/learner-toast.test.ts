import { describe, it, expect, vi, beforeEach } from 'vitest'
import { learnerToast } from '../learner-toast'

// Mock sonner
vi.mock('sonner', () => ({
  toast: Object.assign(
    vi.fn(),
    {
      error: vi.fn(),
      success: vi.fn(),
      warning: vi.fn(),
    }
  ),
}))

import { toast } from 'sonner'

describe('learnerToast', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('applies amber styling to error toasts (never red)', () => {
    learnerToast.error('Something went wrong')

    expect(toast.error).toHaveBeenCalledOnce()
    expect(toast.error).toHaveBeenCalledWith(
      'Something went wrong',
      expect.objectContaining({
        style: expect.objectContaining({
          backgroundColor: '#FEF3C7', // amber-100
          borderColor: '#F59E0B', // amber-500
          color: '#B45309', // amber-700
        }),
        className: 'learner-toast-error',
      })
    )
  })

  it('applies amber styling to warning toasts', () => {
    learnerToast.warning('Heads up')

    expect(toast.warning).toHaveBeenCalledOnce()
    expect(toast.warning).toHaveBeenCalledWith(
      'Heads up',
      expect.objectContaining({
        style: expect.objectContaining({
          backgroundColor: '#FEF3C7',
          borderColor: '#F59E0B',
          color: '#B45309',
        }),
        className: 'learner-toast-warning',
      })
    )
  })

  it('passes duration and description options', () => {
    learnerToast.error('Error message', {
      duration: 8000,
      description: 'More details here',
    })

    expect(toast.error).toHaveBeenCalledWith(
      'Error message',
      expect.objectContaining({
        duration: 8000,
        description: 'More details here',
      })
    )
  })

  it('uses default 5s duration for errors and 3s for success', () => {
    learnerToast.error('Error')
    expect(toast.error).toHaveBeenCalledWith(
      'Error',
      expect.objectContaining({ duration: 5000 })
    )

    learnerToast.success('Done')
    expect(toast.success).toHaveBeenCalledWith(
      'Done',
      expect.objectContaining({ duration: 3000 })
    )
  })
})
