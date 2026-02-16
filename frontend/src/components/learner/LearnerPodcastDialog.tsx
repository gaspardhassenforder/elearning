'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useEpisodeProfiles, useSpeakerProfiles } from '@/lib/hooks/use-podcasts'
import { useLearnerGeneratePodcast } from '@/lib/hooks/use-learner-artifacts'
import { LearnerSourceSelector } from './LearnerSourceSelector'
import { Headphones } from 'lucide-react'

interface LearnerPodcastDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
}

export function LearnerPodcastDialog({
  open,
  onOpenChange,
  notebookId,
}: LearnerPodcastDialogProps) {
  const { t } = useTranslation()
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])
  const [selectedProfile, setSelectedProfile] = useState<string>('')
  const [episodeName, setEpisodeName] = useState('')
  const [instructions, setInstructions] = useState('')

  const { episodeProfiles, isLoading: profilesLoading } = useEpisodeProfiles()
  const { speakerProfiles } = useSpeakerProfiles(episodeProfiles)
  const generateMutation = useLearnerGeneratePodcast(notebookId)

  // Get the selected episode profile's details
  const selectedEpisodeProfile = episodeProfiles.find((p) => p.name === selectedProfile)
  const linkedSpeakerProfile = speakerProfiles.find(
    (sp) => sp.name === selectedEpisodeProfile?.speaker_config
  )

  const canSubmit =
    selectedSourceIds.length > 0 &&
    selectedProfile &&
    episodeName.trim() &&
    !generateMutation.isPending

  const handleSubmit = () => {
    if (!canSubmit) return
    generateMutation.mutate(
      {
        episode_profile: selectedProfile,
        episode_name: episodeName.trim(),
        source_ids: selectedSourceIds,
        instructions: instructions.trim() || undefined,
      },
      {
        onSuccess: () => {
          // Reset form and close
          setSelectedSourceIds([])
          setSelectedProfile('')
          setEpisodeName('')
          setInstructions('')
          onOpenChange(false)
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Headphones className="h-5 w-5" />
            {t.learner?.createArtifact?.podcast || 'Generate Podcast'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Source Selection */}
          <LearnerSourceSelector
            notebookId={notebookId}
            selectedSourceIds={selectedSourceIds}
            onSelectionChange={setSelectedSourceIds}
          />

          {/* Episode Profile */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.episodeProfile || 'Episode Profile'}</Label>
            {profilesLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <LoadingSpinner /> Loading profiles...
              </div>
            ) : (
              <Select value={selectedProfile} onValueChange={setSelectedProfile}>
                <SelectTrigger>
                  <SelectValue placeholder={t.learner?.createArtifact?.profilePlaceholder || 'Choose a profile...'} />
                </SelectTrigger>
                <SelectContent>
                  {episodeProfiles.map((profile) => (
                    <SelectItem key={profile.id} value={profile.name}>
                      {profile.name}
                      {profile.description ? ` - ${profile.description}` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {/* Profile details badges */}
            {selectedEpisodeProfile && (
              <div className="flex gap-2 flex-wrap">
                <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium">
                  {selectedEpisodeProfile.num_segments} segments
                </span>
                {linkedSpeakerProfile && (
                  <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium">
                    {linkedSpeakerProfile.speakers.length} speaker{linkedSpeakerProfile.speakers.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Episode Name */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.episodeName || 'Episode Name'}</Label>
            <Input
              value={episodeName}
              onChange={(e) => setEpisodeName(e.target.value)}
              placeholder={t.learner?.createArtifact?.episodeNamePlaceholder || 'My custom podcast...'}
            />
          </div>

          {/* Instructions */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.instructions || 'Instructions'}</Label>
            <Textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder={t.learner?.createArtifact?.instructionsPlaceholder || 'Optional: focus on specific topics, tone, etc.'}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.common?.cancel || 'Cancel'}
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {generateMutation.isPending ? (
              <>
                <LoadingSpinner />
                <span className="ml-2">{t.learner?.createArtifact?.generating || 'Generating...'}</span>
              </>
            ) : (
              t.learner?.createArtifact?.generate || 'Generate'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
