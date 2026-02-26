import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api/auth'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { OnboardingSubmit } from '@/lib/types/api'
import { useAuthStore } from '@/lib/stores/auth-store'

export function useSubmitOnboarding() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()
  const { fetchCurrentUser } = useAuthStore()
  const router = useRouter()

  return useMutation({
    mutationFn: (data: OnboardingSubmit) => authApi.submitOnboarding(data),
    onSuccess: async () => {
      // Refresh user data in auth store to get updated onboarding_completed status
      await fetchCurrentUser()
      // Invalidate any cached user queries
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
      toast({
        title: t.common.success,
        description: t.onboarding.success,
      })
      // Navigate only after the store is updated, so the layout guard
      // sees onboarding_completed=true and doesn't bounce back to /onboarding
      router.replace('/modules')
    },
    onError: () => {
      toast({
        title: t.common.error,
        description: t.onboarding.error,
        variant: 'destructive',
      })
    },
  })
}
