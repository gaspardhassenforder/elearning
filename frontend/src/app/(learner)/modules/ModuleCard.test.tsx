import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom'

// Mock the translation hook
const mockTranslation = {
  modules: {
    welcome: 'Welcome, {name}!',
    subtitle: 'Select a module to begin learning',
    startLearning: 'Start Learning',
    sources: '{count} sources',
    noModules: 'No modules assigned yet',
    noModulesDescription: 'Contact your administrator to get started',
    loadError: 'Failed to load modules',
  },
  assignments: {
    locked: 'Locked',
    moduleSelection: 'Module Selection',
  },
}

vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({ t: mockTranslation }),
}))

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock auth store
vi.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: () => ({ user: { username: 'TestUser' } }),
}))

// Mock learner modules hook
const mockUseLearnerModules = vi.fn()
vi.mock('@/lib/hooks/use-learner-modules', () => ({
  useLearnerModules: () => mockUseLearnerModules(),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  BookOpen: () => <div data-testid="book-open-icon">BookOpen</div>,
  GraduationCap: () => <div data-testid="graduation-cap-icon">GraduationCap</div>,
  FileText: () => <div data-testid="file-text-icon">FileText</div>,
  ArrowRight: () => <div data-testid="arrow-right-icon">ArrowRight</div>,
  Lock: () => <div data-testid="lock-icon">Lock</div>,
}))

// Import the page component
import ModulesPage from './page'

describe('ModuleCard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Lock Indicator Rendering', () => {
    it('should display lock badge for locked modules', () => {
      const lockedModule = {
        id: 'notebook:locked',
        name: 'Locked Module',
        description: 'This module is locked',
        is_locked: true,
        source_count: 5,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [lockedModule],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      // Lock badge should be visible
      expect(screen.getByText('Locked')).toBeInTheDocument()
      expect(screen.getByTestId('lock-icon')).toBeInTheDocument()
    })

    it('should NOT display lock badge for unlocked modules', () => {
      const unlockedModule = {
        id: 'notebook:unlocked',
        name: 'Unlocked Module',
        description: 'This module is unlocked',
        is_locked: false,
        source_count: 3,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [unlockedModule],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      // Lock badge should NOT be visible
      expect(screen.queryByText('Locked')).not.toBeInTheDocument()
      expect(screen.queryByTestId('lock-icon')).not.toBeInTheDocument()
    })

    it('should display reduced opacity for locked modules', () => {
      const lockedModule = {
        id: 'notebook:locked',
        name: 'Locked Module',
        description: 'This module is locked',
        is_locked: true,
        source_count: 5,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [lockedModule],
        isLoading: false,
        error: null,
      })

      const { container } = render(<ModulesPage />)

      // Find the card element (it should have opacity-60 class)
      const card = container.querySelector('.opacity-60')
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass('cursor-not-allowed')
    })

    it('should NOT display reduced opacity for unlocked modules', () => {
      const unlockedModule = {
        id: 'notebook:unlocked',
        name: 'Unlocked Module',
        description: 'This module is unlocked',
        is_locked: false,
        source_count: 3,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [unlockedModule],
        isLoading: false,
        error: null,
      })

      const { container } = render(<ModulesPage />)

      // Card should NOT have opacity-60 class
      const card = container.querySelector('.opacity-60')
      expect(card).not.toBeInTheDocument()

      // Card should have hover effect
      const hoverCard = container.querySelector('.hover\\:shadow-md')
      expect(hoverCard).toBeInTheDocument()
    })
  })

  describe('Non-Clickable Behavior for Locked Modules', () => {
    it('should NOT navigate when locked module is clicked', () => {
      const lockedModule = {
        id: 'notebook:locked',
        name: 'Locked Module',
        description: 'This module is locked',
        is_locked: true,
        source_count: 5,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [lockedModule],
        isLoading: false,
        error: null,
      })

      const { container } = render(<ModulesPage />)

      // Find the card and click it
      const card = container.querySelector('.opacity-60')
      expect(card).toBeInTheDocument()

      // Click should NOT trigger navigation
      if (card) {
        fireEvent.click(card)
      }

      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should navigate when unlocked module is clicked', () => {
      const unlockedModule = {
        id: 'notebook:unlocked',
        name: 'Unlocked Module',
        description: 'This module is unlocked',
        is_locked: false,
        source_count: 3,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [unlockedModule],
        isLoading: false,
        error: null,
      })

      const { container } = render(<ModulesPage />)

      // Find the card and click it
      const card = container.querySelector('.hover\\:shadow-md')
      expect(card).toBeInTheDocument()

      if (card) {
        fireEvent.click(card)
      }

      // Should navigate to learning interface
      expect(mockPush).toHaveBeenCalledWith('/learner/learn/notebook:unlocked')
    })

    it('should disable button for locked modules', () => {
      const lockedModule = {
        id: 'notebook:locked',
        name: 'Locked Module',
        description: 'This module is locked',
        is_locked: true,
        source_count: 5,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [lockedModule],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      // Button should be disabled
      const button = screen.getByRole('button', { name: /locked/i })
      expect(button).toBeDisabled()
    })

    it('should NOT disable button for unlocked modules', () => {
      const unlockedModule = {
        id: 'notebook:unlocked',
        name: 'Unlocked Module',
        description: 'This module is unlocked',
        is_locked: false,
        source_count: 3,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [unlockedModule],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      // Button should NOT be disabled
      const button = screen.getByRole('button', { name: /start learning/i })
      expect(button).not.toBeDisabled()
    })

    it('should have pointer-events-none style for locked modules', () => {
      const lockedModule = {
        id: 'notebook:locked',
        name: 'Locked Module',
        description: 'This module is locked',
        is_locked: true,
        source_count: 5,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [lockedModule],
        isLoading: false,
        error: null,
      })

      const { container } = render(<ModulesPage />)

      // Card should have pointer-events: none
      const card = container.querySelector('.opacity-60')
      expect(card).toHaveStyle({ pointerEvents: 'none' })
    })
  })

  describe('Module Information Display', () => {
    it('should display module name and description', () => {
      const module = {
        id: 'notebook:test',
        name: 'Test Module',
        description: 'This is a test module',
        is_locked: false,
        source_count: 7,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [module],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      expect(screen.getByText('Test Module')).toBeInTheDocument()
      expect(screen.getByText('This is a test module')).toBeInTheDocument()
    })

    it('should display source count', () => {
      const module = {
        id: 'notebook:test',
        name: 'Test Module',
        description: 'Test',
        is_locked: false,
        source_count: 7,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [module],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      expect(screen.getByText('7 sources')).toBeInTheDocument()
    })

    it('should handle missing description gracefully', () => {
      const module = {
        id: 'notebook:test',
        name: 'Test Module',
        description: null,
        is_locked: false,
        source_count: 3,
        assigned_at: '2024-01-01T00:00:00',
      }

      mockUseLearnerModules.mockReturnValue({
        data: [module],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      expect(screen.getByText('Test Module')).toBeInTheDocument()
      // Description should not be rendered if null
      expect(screen.queryByRole('paragraph')).not.toBeInTheDocument()
    })
  })

  describe('Multiple Modules Display', () => {
    it('should render multiple modules with mixed lock states', () => {
      const modules = [
        {
          id: 'notebook:locked',
          name: 'Locked Module',
          description: 'Locked',
          is_locked: true,
          source_count: 5,
          assigned_at: '2024-01-01T00:00:00',
        },
        {
          id: 'notebook:unlocked1',
          name: 'Unlocked Module 1',
          description: 'Unlocked',
          is_locked: false,
          source_count: 3,
          assigned_at: '2024-01-02T00:00:00',
        },
        {
          id: 'notebook:unlocked2',
          name: 'Unlocked Module 2',
          description: 'Also unlocked',
          is_locked: false,
          source_count: 8,
          assigned_at: '2024-01-03T00:00:00',
        },
      ]

      mockUseLearnerModules.mockReturnValue({
        data: modules,
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      // All modules should be rendered
      expect(screen.getByText('Locked Module')).toBeInTheDocument()
      expect(screen.getByText('Unlocked Module 1')).toBeInTheDocument()
      expect(screen.getByText('Unlocked Module 2')).toBeInTheDocument()

      // Only one lock badge should be present
      const lockBadges = screen.getAllByText('Locked')
      expect(lockBadges).toHaveLength(1)
    })
  })
})

describe('ModulesPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should display skeleton loaders when loading', () => {
      mockUseLearnerModules.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

      render(<ModulesPage />)

      // Should show skeleton loaders (3 cards)
      const skeletons = screen.getAllByRole('generic').filter((el) =>
        el.className.includes('animate-pulse')
      )
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Error State', () => {
    it('should display error message when load fails', () => {
      mockUseLearnerModules.mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Failed to fetch'),
      })

      render(<ModulesPage />)

      expect(screen.getByText('Failed to load modules')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should display empty state when no modules assigned', () => {
      mockUseLearnerModules.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      })

      render(<ModulesPage />)

      expect(screen.getByText('No modules assigned yet')).toBeInTheDocument()
    })
  })
})
