'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useSubmitOnboarding } from '@/lib/hooks/use-onboarding'
import { useTranslation } from '@/lib/hooks/use-translation'
import { AIFamiliarity } from '@/lib/types/api'
import { Sparkles, Briefcase, MessageSquare } from 'lucide-react'

export default function OnboardingPage() {
  const { t } = useTranslation()
  const router = useRouter()
  const submitOnboarding = useSubmitOnboarding()

  const [formData, setFormData] = useState({
    ai_familiarity: '' as AIFamiliarity | '',
    job_type: '',
    job_description: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.ai_familiarity) {
      newErrors.ai_familiarity = t.onboarding.skipNotAllowed
    }
    if (!formData.job_type.trim()) {
      newErrors.job_type = t.onboarding.skipNotAllowed
    }
    if (formData.job_description.trim().length < 10) {
      newErrors.job_description = t.onboarding.skipNotAllowed
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    try {
      await submitOnboarding.mutateAsync({
        ai_familiarity: formData.ai_familiarity as AIFamiliarity,
        job_type: formData.job_type.trim(),
        job_description: formData.job_description.trim(),
      })
      router.replace('/modules')
    } catch {
      // Error handled by hook
    }
  }

  const aiFamiliarityOptions: { value: AIFamiliarity; label: string }[] = [
    { value: 'never_used', label: t.onboarding.aiFamiliarityOptions.neverUsed },
    { value: 'used_occasionally', label: t.onboarding.aiFamiliarityOptions.usedOccasionally },
    { value: 'use_regularly', label: t.onboarding.aiFamiliarityOptions.useRegularly },
    { value: 'power_user', label: t.onboarding.aiFamiliarityOptions.powerUser },
  ]

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background to-muted/30">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto">
            <Image src="/logo.svg" alt="Open Notebook" width={48} height={48} />
          </div>
          <div>
            <CardTitle className="text-2xl">{t.onboarding.title}</CardTitle>
            <CardDescription className="mt-2">
              {t.onboarding.subtitle}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <p className="text-sm text-muted-foreground text-center">
              {t.onboarding.description}
            </p>

            {/* AI Familiarity */}
            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                {t.onboarding.aiFamiliarity}
              </Label>
              <RadioGroup
                value={formData.ai_familiarity}
                onValueChange={(value) =>
                  setFormData({ ...formData, ai_familiarity: value as AIFamiliarity })
                }
                className="space-y-2"
              >
                {aiFamiliarityOptions.map((option) => (
                  <div key={option.value} className="flex items-center space-x-3">
                    <RadioGroupItem value={option.value} id={option.value} />
                    <Label htmlFor={option.value} className="font-normal cursor-pointer">
                      {option.label}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
              {errors.ai_familiarity && (
                <p className="text-sm text-destructive">{errors.ai_familiarity}</p>
              )}
            </div>

            {/* Job Type */}
            <div className="space-y-2">
              <Label htmlFor="job_type" className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-primary" />
                {t.onboarding.jobType}
              </Label>
              <Input
                id="job_type"
                placeholder={t.onboarding.jobTypePlaceholder}
                value={formData.job_type}
                onChange={(e) => setFormData({ ...formData, job_type: e.target.value })}
              />
              {errors.job_type && (
                <p className="text-sm text-destructive">{errors.job_type}</p>
              )}
            </div>

            {/* Job Description */}
            <div className="space-y-2">
              <Label htmlFor="job_description" className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-primary" />
                {t.onboarding.jobDescription}
              </Label>
              <Textarea
                id="job_description"
                placeholder={t.onboarding.jobDescriptionPlaceholder}
                value={formData.job_description}
                onChange={(e) => setFormData({ ...formData, job_description: e.target.value })}
                rows={3}
              />
              {errors.job_description && (
                <p className="text-sm text-destructive">{errors.job_description}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={submitOnboarding.isPending}
            >
              {submitOnboarding.isPending ? t.onboarding.submitting : t.onboarding.submit}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
