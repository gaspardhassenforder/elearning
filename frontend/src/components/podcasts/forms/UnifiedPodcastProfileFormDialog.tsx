'use client'

import { useCallback, useEffect, useRef } from 'react'
import { Controller, useFieldArray, useForm } from 'react-hook-form'
import type { FieldErrorsImpl } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'

import { EpisodeProfile } from '@/lib/types/podcasts'
import { podcastsApi } from '@/lib/api/podcasts'
import { QUERY_KEYS } from '@/lib/api/query-client'
import {
  useCreateUnifiedPodcastProfile,
  useUpdateUnifiedPodcastProfile,
} from '@/lib/hooks/use-podcasts'
import { useTranslation } from '@/lib/hooks/use-translation'
import { TranslationKeys } from '@/lib/locales'
import { GOOGLE_TTS_VOICE_OPTIONS } from '@/lib/podcasts/google-tts-voices'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'

const speakerRowSchema = (t: TranslationKeys) =>
  z.object({
    name: z.string().min(1, t.common.nameRequired || 'Name is required'),
    voice_id: z.string().min(1, t.podcasts.voiceIdRequired || 'Voice is required'),
    backstory: z.string().min(1, t.podcasts.backstoryRequired || 'Backstory is required'),
    personality: z.string().min(1, t.podcasts.personalityRequired || 'Personality is required'),
  })

const unifiedSchema = (t: TranslationKeys) =>
  z.object({
    name: z.string().min(1, t.podcasts.nameRequired || 'Name is required'),
    description: z.string().optional(),
    speakers: z
      .array(speakerRowSchema(t))
      .min(1, t.podcasts.speakerCountMin || 'At least one speaker is required')
      .max(4, t.podcasts.speakerCountMax || 'You can configure up to 4 speakers'),
    default_briefing: z
      .string()
      .min(1, t.podcasts.defaultBriefingRequired || 'Default briefing is required'),
    num_segments: z
      .number()
      .int(t.podcasts.segmentsInteger || 'Must be an integer')
      .min(3, t.podcasts.segmentsMin || 'At least 3 segments')
      .max(20, t.podcasts.segmentsMax || 'Maximum 20 segments'),
  })

export type UnifiedPodcastProfileFormValues = z.infer<ReturnType<typeof unifiedSchema>>

const EMPTY_SPEAKER = {
  name: '',
  voice_id: 'Kore',
  backstory: '',
  personality: '',
}

interface UnifiedPodcastProfileFormDialogProps {
  mode: 'create' | 'edit'
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: EpisodeProfile
}

export function UnifiedPodcastProfileFormDialog({
  mode,
  open,
  onOpenChange,
  initialData,
}: UnifiedPodcastProfileFormDialogProps) {
  const { t } = useTranslation()
  const createProfile = useCreateUnifiedPodcastProfile()
  const updateProfile = useUpdateUnifiedPodcastProfile()

  const speakerQuery = useQuery({
    queryKey: [
      ...QUERY_KEYS.speakerProfiles,
      'by-name',
      initialData?.speaker_config ?? '',
    ],
    queryFn: () => podcastsApi.getSpeakerProfileByName(initialData!.speaker_config),
    enabled:
      open && mode === 'edit' && Boolean(initialData?.speaker_config),
  })

  const getDefaults = useCallback((): UnifiedPodcastProfileFormValues => {
    if (mode === 'edit' && initialData) {
      if (speakerQuery.data) {
        return {
          name: initialData.name,
          description: initialData.description ?? '',
          speakers:
            speakerQuery.data.speakers?.map((s) => ({
              name: s.name,
              voice_id: s.voice_id,
              backstory: s.backstory,
              personality: s.personality,
            })) ?? [{ ...EMPTY_SPEAKER }],
          default_briefing: initialData.default_briefing,
          num_segments: initialData.num_segments,
        }
      }
      return {
        name: initialData.name,
        description: initialData.description ?? '',
        speakers: [{ ...EMPTY_SPEAKER }],
        default_briefing: initialData.default_briefing,
        num_segments: initialData.num_segments,
      }
    }
    return {
      name: '',
      description: '',
      speakers: [{ ...EMPTY_SPEAKER }],
      default_briefing: '',
      num_segments: 5,
    }
  }, [initialData, mode, speakerQuery.data])

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UnifiedPodcastProfileFormValues>({
    resolver: zodResolver(unifiedSchema(t)),
    defaultValues: getDefaults(),
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'speakers',
  })

  const speakersArrayError = (
    errors.speakers as FieldErrorsImpl<{ root?: { message?: string } }> | undefined
  )?.root?.message

  const hasLoadedSpeaker = useRef(false)

  useEffect(() => {
    if (!open) {
      hasLoadedSpeaker.current = false
      return
    }
    if (mode === 'edit' && initialData) {
      if (speakerQuery.data && !hasLoadedSpeaker.current) {
        hasLoadedSpeaker.current = true
        reset(getDefaults())
      }
      return
    }
    reset(getDefaults())
  }, [open, mode, initialData, speakerQuery.data, reset, getDefaults])

  const onSubmit = async (values: UnifiedPodcastProfileFormValues) => {
    const payload = {
      name: values.name.trim(),
      description: values.description ?? '',
      speakers: values.speakers.map((s) => ({ ...s })),
      default_briefing: values.default_briefing,
      num_segments: values.num_segments,
    }

    try {
      if (mode === 'create') {
        await createProfile.mutateAsync(payload)
      } else if (initialData) {
        await updateProfile.mutateAsync({
          profileId: initialData.id,
          payload,
        })
      }
      onOpenChange(false)
    } catch {
      // mutation hook shows toast; keep dialog open
    }
  }

  const isSubmitting = createProfile.isPending || updateProfile.isPending
  const isEdit = mode === 'edit'
  const waitingSpeaker =
    isEdit && initialData && speakerQuery.isLoading && !speakerQuery.data
  const speakerError = isEdit && initialData && speakerQuery.isError

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? t.podcasts.editEpisodeProfile : t.podcasts.createEpisodeProfile}
          </DialogTitle>
          <DialogDescription>{t.podcasts.unifiedPodcastWizardDesc}</DialogDescription>
        </DialogHeader>

        {speakerError ? (
          <Alert variant="destructive">
            <AlertTitle>{t.podcasts.unifiedLoadSpeakerErrorTitle}</AlertTitle>
            <AlertDescription>{t.podcasts.unifiedLoadSpeakerErrorDesc}</AlertDescription>
          </Alert>
        ) : null}

        {waitingSpeaker ? (
          <p className="text-sm text-muted-foreground">{t.podcasts.unifiedLoadingSpeakers}</p>
        ) : null}

        {!waitingSpeaker && !speakerError ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 pt-2">
            <div className="rounded-md border border-dashed bg-muted/30 p-3 text-xs text-muted-foreground">
              {t.podcasts.unifiedEngineNote}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="up-name">{t.podcasts.profileName} *</Label>
                <Input
                  id="up-name"
                  placeholder={t.podcasts.profileNamePlaceholder}
                  {...register('name')}
                  autoComplete="off"
                />
                {errors.name ? (
                  <p className="text-xs text-red-600">{errors.name.message}</p>
                ) : null}
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="up-desc">{t.common.description}</Label>
                <Textarea
                  id="up-desc"
                  rows={2}
                  placeholder={t.podcasts.descriptionPlaceholder}
                  {...register('description')}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="up-segments">{t.podcasts.segments} *</Label>
                <Input
                  id="up-segments"
                  type="number"
                  min={3}
                  max={20}
                  {...register('num_segments', { valueAsNumber: true })}
                />
                {errors.num_segments ? (
                  <p className="text-xs text-red-600">{errors.num_segments.message}</p>
                ) : null}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="up-briefing">{t.podcasts.defaultBriefingTitle} *</Label>
              <Textarea
                id="up-briefing"
                rows={4}
                placeholder={t.podcasts.defaultBriefingPlaceholder}
                {...register('default_briefing')}
              />
              {errors.default_briefing ? (
                <p className="text-xs text-red-600">{errors.default_briefing.message}</p>
              ) : null}
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    {t.podcasts.speakers}
                  </h3>
                  <p className="text-xs text-muted-foreground">{t.podcasts.unifiedSpeakersDesc}</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => append({ ...EMPTY_SPEAKER })}
                  disabled={fields.length >= 4}
                >
                  <Plus className="mr-2 h-4 w-4" /> {t.podcasts.addSpeaker}
                </Button>
              </div>
              <Separator />

              {fields.map((field, index) => (
                <div key={field.id} className="rounded-lg border p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold">
                      {t.podcasts.speakerNumber.replace('{number}', String(index + 1))}
                    </p>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(index)}
                      disabled={fields.length <= 1}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" /> {t.common.remove}
                    </Button>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor={`up-sp-name-${index}`}>{t.common.name} *</Label>
                      <Input
                        id={`up-sp-name-${index}`}
                        {...register(`speakers.${index}.name` as const)}
                        placeholder={t.podcasts.hostPlaceholder.replace(
                          '{number}',
                          String(index + 1)
                        )}
                        autoComplete="off"
                      />
                      {errors.speakers?.[index]?.name ? (
                        <p className="text-xs text-red-600">
                          {errors.speakers[index]?.name?.message}
                        </p>
                      ) : null}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`up-voice-${index}`}>{t.podcasts.googleVoiceLabel} *</Label>
                      <Controller
                        control={control}
                        name={`speakers.${index}.voice_id`}
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger id={`up-voice-${index}`}>
                              <SelectValue placeholder={t.podcasts.googleVoicePlaceholder} />
                            </SelectTrigger>
                            <SelectContent>
                              {GOOGLE_TTS_VOICE_OPTIONS.map((opt) => (
                                <SelectItem key={opt.value} value={opt.value}>
                                  {opt.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                      {errors.speakers?.[index]?.voice_id ? (
                        <p className="text-xs text-red-600">
                          {errors.speakers[index]?.voice_id?.message}
                        </p>
                      ) : null}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`up-back-${index}`}>{t.podcasts.backstory} *</Label>
                    <Textarea
                      id={`up-back-${index}`}
                      rows={2}
                      placeholder={t.podcasts.backstoryPlaceholder}
                      {...register(`speakers.${index}.backstory` as const)}
                      autoComplete="off"
                    />
                    {errors.speakers?.[index]?.backstory ? (
                      <p className="text-xs text-red-600">
                        {errors.speakers[index]?.backstory?.message}
                      </p>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`up-pers-${index}`}>{t.podcasts.personality} *</Label>
                    <Textarea
                      id={`up-pers-${index}`}
                      rows={2}
                      placeholder={t.podcasts.personalityPlaceholder}
                      {...register(`speakers.${index}.personality` as const)}
                      autoComplete="off"
                    />
                    {errors.speakers?.[index]?.personality ? (
                      <p className="text-xs text-red-600">
                        {errors.speakers[index]?.personality?.message}
                      </p>
                    ) : null}
                  </div>
                </div>
              ))}

              {speakersArrayError ? (
                <p className="text-xs text-red-600">{speakersArrayError}</p>
              ) : null}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                {t.common.cancel}
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || waitingSpeaker || Boolean(speakerError)}
              >
                {isSubmitting
                  ? t.common.saving
                  : isEdit
                    ? t.common.saveChanges
                    : t.podcasts.createProfile}
              </Button>
            </div>
          </form>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
