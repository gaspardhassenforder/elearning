import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

export const QUERY_KEYS = {
  notebooks: ['notebooks'] as const,
  notebook: (id: string) => ['notebooks', id] as const,
  notes: (notebookId?: string) => ['notes', notebookId] as const,
  note: (id: string) => ['notes', id] as const,
  sources: (notebookId?: string) => ['sources', notebookId] as const,
  sourcesInfinite: (notebookId: string) => ['sources', 'infinite', notebookId] as const,
  source: (id: string) => ['sources', id] as const,
  settings: ['settings'] as const,
  sourceChatSessions: (sourceId: string) => ['source-chat', sourceId, 'sessions'] as const,
  sourceChatSession: (sourceId: string, sessionId: string) => ['source-chat', sourceId, 'sessions', sessionId] as const,
  notebookChatSessions: (notebookId: string) => ['notebook-chat', notebookId, 'sessions'] as const,
  notebookChatSession: (sessionId: string) => ['notebook-chat', 'sessions', sessionId] as const,
  podcastEpisodes: ['podcasts', 'episodes'] as const,
  podcastEpisode: (episodeId: string) => ['podcasts', 'episodes', episodeId] as const,
  episodeProfiles: ['podcasts', 'episode-profiles'] as const,
  speakerProfiles: ['podcasts', 'speaker-profiles'] as const,
  artifacts: (notebookId: string) => ['artifacts', notebookId] as const,
  quiz: (quizId: string) => ['quiz', quizId] as const,
  quizzes: (notebookId: string) => ['quizzes', notebookId] as const,
  users: ['users'] as const,
  user: (id: string) => ['users', id] as const,
  companies: ['companies'] as const,
  company: (id: string) => ['companies', id] as const,
  assignments: ['assignments'] as const,
  assignmentMatrix: ['assignments', 'matrix'] as const,
  learnerModules: ['learner-modules'] as const,
  learnerModule: (notebookId: string) => ['learner-modules', notebookId] as const,
  // Story 4.4: Learner objectives progress
  learnerObjectivesProgress: (notebookId: string) => ['learning-objectives', 'progress', notebookId] as const,
  // Story 5.1: Source content for document browsing
  sourceContent: (sourceId: string) => ['sources', sourceId, 'content'] as const,
  // Story 5.2: Learner artifacts browsing
  learnerArtifacts: (notebookId: string) => ['learner-artifacts', notebookId] as const,
  learnerArtifactPreview: (artifactId: string) => ['learner-artifacts', 'preview', artifactId] as const,
  transformations: ['transformations'] as const,
  systemPrompt: () => ['system-prompt'] as const,
}
