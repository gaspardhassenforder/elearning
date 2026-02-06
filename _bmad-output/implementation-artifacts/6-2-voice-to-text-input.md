# Story 6.2: Voice-to-Text Input

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want to use voice input in the chat interface,
So that I can interact with the AI teacher by speaking instead of typing.

## Acceptance Criteria

**AC1: Microphone Button Visibility**
**Given** a learner is in the chat interface
**When** they see the input bar
**Then** a microphone button is visible on the left side of the composer

**AC2: Recording Initiation with Browser Permission**
**Given** the learner clicks the microphone button
**When** recording starts
**Then** a visual recording indicator appears in the input bar (pulsing dot or waveform)
**And** the browser requests microphone permission if not already granted

**AC3: Recording Termination and Transcription**
**Given** the learner is recording
**When** they click the stop button or the microphone button again
**Then** recording stops and the audio is transcribed to text automatically

**AC4: Review and Edit Transcribed Text**
**Given** transcription is complete
**When** the text appears in the input field
**Then** the learner can review and edit the transcribed text before sending

**AC5: Standard Message Submission**
**Given** the learner is satisfied with the transcription
**When** they click Send or press Enter
**Then** the message is sent to the AI teacher as normal text

**AC6: Graceful Degradation for Unsupported Browsers**
**Given** the browser does not support the Speech API or permission is denied
**When** the learner clicks the microphone button
**Then** a friendly message indicates voice input is unavailable

## Tasks / Subtasks

### Task 1: Create Web Speech API Hook (AC: 2, 3, 4, 6)
- [x] 1.1: Create `use-voice-input.ts` hook with TypeScript types for SpeechRecognition API
- [x] 1.2: Implement browser feature detection (SpeechRecognition / webkitSpeechRecognition)
- [x] 1.3: Implement recording state management (isListening, isSupported, transcript)
- [x] 1.4: Configure SpeechRecognition with continuous:false, interimResults:true, lang from i18n
- [x] 1.5: Implement startListening with permission handling and error catching
- [x] 1.6: Implement stopListening with cleanup
- [x] 1.7: Add error handling for permission denied, not supported, and network errors
- [x] 1.8: Test hook with mocked SpeechRecognition API

### Task 2: Add Microphone Button to ChatPanel (AC: 1, 2)
- [x] 2.1: Import `Mic` and `MicOff` icons from lucide-react
- [x] 2.2: Add microphone button to input form (left side of input field)
- [x] 2.3: Style button with `variant="ghost"` and `size="icon"` from Button component
- [x] 2.4: Add pulsing animation CSS for recording state
- [x] 2.5: Wire up startListening/stopListening handlers
- [x] 2.6: Add aria-label for accessibility
- [x] 2.7: Hide button if voice input is not supported

### Task 3: Integrate Transcript into Input Field (AC: 4, 5)
- [x] 3.1: Connect useVoiceInput transcript state to input field value
- [x] 3.2: Allow manual editing of transcribed text
- [x] 3.3: Ensure existing send functionality works with voice-transcribed text
- [x] 3.4: Clear transcript state after message is sent

### Task 4: Add i18n Translations (AC: 6)
- [x] 4.1: Add `learner.chat.voiceInput.*` keys to `en-US/index.ts`
- [x] 4.2: Add French translations to `fr-FR/index.ts`
- [x] 4.3: Include error messages for permission denied, not supported, recording failed

### Task 5: Error Handling and Toast Notifications (AC: 6)
- [x] 5.1: Add toast notification for permission denied with helpful instructions
- [x] 5.2: Add toast notification for browser not supported
- [x] 5.3: Add toast notification for recording errors
- [x] 5.4: Follow project pattern: use warm amber for error states, never red

### Task 6: Testing & Validation (AC: All)
- [x] 6.1: Write unit tests for `use-voice-input.ts` hook (mock SpeechRecognition)
- [x] 6.2: Write component tests for ChatPanel with voice button
- [x] 6.3: Test permission granted flow
- [x] 6.4: Test permission denied flow
- [x] 6.5: Test unsupported browser flow
- [x] 6.6: Test transcript accumulation and editing
- [x] 6.7: Test accessibility (keyboard navigation, screen reader announcements)
- [x] 6.8: Verify all i18n strings in both en-US and fr-FR

## Dev Notes

### Implementation Approach

**Frontend-Only Feature:**
This story requires NO backend changes. The chat API already accepts text input via the existing `/chat/{notebook_id}/ask` endpoint. Voice input is purely a frontend enhancement that:
1. Records audio using browser Web Speech API
2. Transcribes speech to text client-side (browser-native)
3. Populates the existing text input field
4. Uses existing chat submission flow

**Key Technical Decision: Browser-Native Speech Recognition**
- Use browser's built-in `SpeechRecognition` API (no external transcription service needed)
- Zero backend changes required
- Zero additional API costs
- Works offline after initial page load
- Privacy-preserving: audio never leaves the browser

**Alternative Considered but Rejected:**
- External transcription service (OpenAI Whisper, Google Speech-to-Text): Adds complexity, cost, latency, and privacy concerns

### Architecture Patterns and Constraints

**Frontend Technology Stack:**
- Next.js 16 with React 19
- TypeScript strict mode
- Zustand 5.x for permission state (optional)
- TanStack Query 5.83+ (not needed for this story)
- Shadcn/ui components with Tailwind CSS
- i18next 25.7+ for internationalization

**Browser API Requirements:**
- `SpeechRecognition` or `webkitSpeechRecognition` (Chrome, Edge, Safari)
- Feature detection required: `typeof window.SpeechRecognition !== 'undefined'`
- Graceful degradation if API unavailable
- No getUserMedia needed (Speech API handles audio internally)

**Component Integration:**
- Target component: `frontend/src/components/learner/ChatPanel.tsx` (lines 369-395)
- Add microphone button left of text input in existing form
- Use established Button component with `variant="ghost"` and `size="icon"`
- Use lucide-react `Mic` and `MicOff` icons

**State Management:**
- Local component state via `useVoiceInput` hook (isListening, transcript)
- Optional: Zustand store for permission caching (not critical for MVP)
- No TanStack Query needed (no API calls)

### Source Tree Components to Touch

**New Files:**
1. `frontend/src/lib/hooks/use-voice-input.ts` - Web Speech API wrapper hook
2. `frontend/src/lib/hooks/__tests__/use-voice-input.test.ts` - Hook unit tests
3. `frontend/src/components/learner/__tests__/VoiceInput.test.tsx` - Integration tests

**Modified Files:**
1. `frontend/src/components/learner/ChatPanel.tsx` - Add microphone button to input form
2. `frontend/src/lib/locales/en-US/index.ts` - Add voice input strings
3. `frontend/src/lib/locales/fr-FR/index.ts` - Add French voice input strings

**Reference Files (Do NOT modify):**
- `frontend/src/components/ui/button.tsx` - Button component (already supports icon variant)
- `frontend/src/lib/hooks/use-media-query.ts` - Pattern reference for browser API hooks
- `frontend/src/components/learner/InlineAudioPlayer.tsx` - Audio element patterns
- `frontend/src/lib/hooks/use-toast.ts` - Toast notification pattern

### Testing Standards Summary

**Test Framework:**
- Vitest 3.x (NOT Jest)
- React Testing Library
- @testing-library/user-event (prefer over fireEvent)

**Required Test Coverage:**
1. Mock `window.SpeechRecognition` in tests:
   ```typescript
   vi.stubGlobal('SpeechRecognition', vi.fn(() => ({
     start: vi.fn(),
     stop: vi.fn(),
     addEventListener: vi.fn(),
     removeEventListener: vi.fn(),
   })))
   ```
2. Test all acceptance criteria flows
3. Test error states (permission denied, not supported)
4. Test accessibility (keyboard navigation, aria-labels)
5. Verify i18n strings used (not hardcoded English)

**Run Tests:**
```bash
npm run test                    # Run all tests
npm run test -- use-voice-input # Run specific test file
npm run test:ui                 # Interactive test UI
```

### Project Structure Notes

**Alignment with Unified Project Structure:**
- Frontend hooks: `frontend/src/lib/hooks/`
- Frontend components: `frontend/src/components/learner/`
- i18n locales: `frontend/src/lib/locales/{locale}/`
- Tests co-located with components: `__tests__/` subdirectories

**Detected Conflicts or Variances:**
- None. This story follows established patterns from Stories 4.7 (async status), 4.8 (chat enhancements), and 5.2 (side panel components).

### References

#### Web Speech API Documentation
- [MDN SpeechRecognition API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [Browser Support: Chrome 33+, Edge 79+, Safari 14.1+](https://caniuse.com/speech-recognition)
- [Source: PRD.md#FR39-FR41 - Voice Input Requirements]

#### Existing Code Patterns
- Browser API Hook Pattern: [Source: frontend/src/lib/hooks/use-media-query.ts#9-25]
- Chat Input Form: [Source: frontend/src/components/learner/ChatPanel.tsx#369-395]
- Button Component with Icon Variant: [Source: frontend/src/components/ui/button.tsx#7-36]
- Toast Error Handling: [Source: frontend/src/lib/hooks/use-toast.ts#14-24]
- Audio Element Management: [Source: frontend/src/components/learner/InlineAudioPlayer.tsx]

#### Architecture Constraints
- [Source: architecture.md - Frontend Stack Requirements]
- [Source: architecture.md - Browser Compatibility]
- [Source: architecture.md - Accessibility Requirements (WCAG 2.1 AA)]

#### Epic Context
- [Source: epics.md#Epic 6: Platform Navigation & Voice Input]
- [Source: epics.md#Story 6.2: Voice-to-Text Input - Lines 984-1018]

### Critical Implementation Notes

**Prevent Common LLM Developer Mistakes:**

1. **Don't Use MediaRecorder + Transcription API:**
   - WRONG: Record audio → upload to backend → call Whisper API
   - RIGHT: Use browser's native `SpeechRecognition` API (zero backend work)

2. **Feature Detection is MANDATORY:**
   - Check for `SpeechRecognition` support before showing button
   - Handle Safari's `webkitSpeechRecognition` prefix
   - Gracefully hide feature if unavailable

3. **Permission Handling:**
   - Never auto-start recording on mount
   - Browser may prompt for microphone permission on first use
   - Handle permission denial with helpful toast message
   - Don't store permission state in localStorage

4. **TypeScript Types:**
   - `SpeechRecognition` is not in TypeScript DOM lib by default
   - Must declare global interface extensions (see Web Speech API types)
   - Use strict type checking for event handlers

5. **i18n Completeness:**
   - MUST add ALL strings to BOTH en-US and fr-FR
   - Include error messages, status indicators, button labels
   - Never hardcode English text

6. **Accessibility:**
   - Add `aria-label` to microphone button
   - Use `role="status"` for recording indicator
   - Support keyboard navigation (Enter/Space to toggle)
   - Screen reader announcements for status changes

7. **Visual Feedback:**
   - Pulsing animation during recording (use CSS animation)
   - Different icon states: idle (Mic), recording (MicOff or pulsing Mic)
   - Don't rely on color alone for status

8. **Cleanup:**
   - Always cleanup `SpeechRecognition` listeners in `useEffect` return
   - Stop recording on component unmount
   - Clear transcript state after message sent

9. **Testing:**
   - Use Vitest, NOT Jest
   - Mock `window.SpeechRecognition` completely
   - Test all error paths (permission denied, not supported, recording error)
   - Use `@testing-library/user-event` not `fireEvent`

10. **No Backend Changes:**
    - Do NOT create transcription endpoints
    - Do NOT modify chat API
    - Do NOT add audio upload functionality
    - The existing chat submission flow handles voice-transcribed text

### Performance Considerations

**Minimal Performance Impact:**
- No audio file uploads (browser Speech API streams internally)
- No heavy processing on main thread
- Transcription happens in real-time as user speaks
- No memory accumulation (transcript replaces on each result)

**State Updates:**
- Use `useCallback` for start/stop handlers
- Use `useRef` for SpeechRecognition instance
- Don't trigger re-renders on interim results (accumulate in ref)

**Cleanup:**
- Stop recognition on unmount
- Remove event listeners properly
- Clear transcript state after send

### Security Considerations

**Privacy-First Design:**
- Audio never leaves the browser (Speech API is client-side)
- No audio data stored or transmitted
- No API calls for transcription (zero backend data exposure)
- Microphone permission handled by browser (standard permission API)

**No Authentication Required:**
- This is a pure frontend feature using browser APIs
- No backend endpoints needed
- Existing chat authentication covers message submission

### Browser Compatibility

**Supported Browsers:**
- ✅ Chrome 33+ (with `SpeechRecognition`)
- ✅ Edge 79+ (with `SpeechRecognition`)
- ✅ Safari 14.1+ (with `webkitSpeechRecognition`)
- ❌ Firefox (does not support Speech API as of 2026)

**Graceful Degradation:**
- Feature detection hides button if unavailable
- Toast notification explains voice input not supported
- Text input remains fully functional
- No broken UI or errors if unsupported

**Mobile Support:**
- iOS Safari: Supported (14.1+)
- Android Chrome: Supported (33+)
- Mobile UX: Same behavior as desktop

### Known Limitations

1. **Language Support:**
   - Speech API supports 50+ languages
   - Set language based on user's i18n locale (`navigator.language`)
   - Accuracy varies by language and accent

2. **Network Dependency:**
   - Some browsers require internet for Speech API (Google's cloud-based recognition)
   - Offline support varies by browser/platform

3. **Continuous Recording:**
   - Designed for single utterance capture (AC3: stop button)
   - Not continuous dictation mode (by design)

4. **Interim Results:**
   - Enable `interimResults: true` for real-time feedback
   - Final result may differ slightly from interim display

### Previous Story Learnings

**From Story 5.2 (Artifacts Panel - Just Completed):**
- Use Accordion component for expandable UI sections (not applicable here)
- Frontend-only features require comprehensive frontend tests (30+ tests)
- i18n completeness checked in code review (both en-US and fr-FR required)
- Error state UI must be user-friendly with clear messaging

**From Story 4.8 (Persistent Chat History):**
- ChatPanel modifications must preserve existing functionality
- Test all chat flows after modifications
- Use TanStack Query for data fetching (not needed here)
- Scroll behavior and focus management are critical in chat UI

**From Story 4.7 (Async Status Bar):**
- Visual feedback for async operations (similar pattern for recording indicator)
- Use toast notifications for transient status
- Auto-dismiss toasts after action complete

**From Story 4.6 (AI Surfaces Artifacts):**
- Chat integration features must not break existing chat functionality
- Test all ACs with unit and integration tests
- Use established ChatPanel patterns (don't reinvent)

**Key Lesson:**
- Keep chat UI modifications minimal and focused
- Test rigorously with mocks for browser APIs
- Follow existing component composition patterns
- Don't add unnecessary complexity (YAGNI principle)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

<!-- To be filled during implementation with links to conversation logs -->

### Completion Notes List

- [x] All 6 acceptance criteria verified
- [x] 3 new files created (hook, hook tests, integration tests)
- [x] 3 files modified (ChatPanel, en-US, fr-FR)
- [x] All tests passing (24 total: 11 hook tests + 13 component tests)
- [x] Both en-US and fr-FR i18n complete
- [x] Accessibility tested (keyboard nav, screen reader, aria-labels)
- [x] Browser compatibility: Feature detection for Chrome/Edge/Safari
- [x] Code follows established patterns from existing hooks

**Implementation Summary:**
- Browser-native Speech Recognition API used (no external services)
- Zero backend changes required
- Graceful degradation for unsupported browsers
- Complete error handling with user-friendly toast messages
- Pulsing visual feedback during recording
- Full i18n support (en-US and fr-FR)
- Comprehensive test coverage (24 tests, all passing)

### File List

**Created:**
- frontend/src/lib/hooks/use-voice-input.ts
- frontend/src/lib/hooks/__tests__/use-voice-input.test.ts
- frontend/src/components/learner/__tests__/VoiceInput.test.tsx

**Modified:**
- frontend/src/components/learner/ChatPanel.tsx
- frontend/src/lib/locales/en-US/index.ts
- frontend/src/lib/locales/fr-FR/index.ts

---

## 🎯 COMPREHENSIVE DEVELOPER IMPLEMENTATION GUIDE

### Part 1: Web Speech API TypeScript Declarations

**Location:** `frontend/src/lib/hooks/use-voice-input.ts` (top of file)

The browser's `SpeechRecognition` API is not included in TypeScript's standard DOM types. You MUST declare these types:

```typescript
// TypeScript declarations for Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: 'no-speech' | 'aborted' | 'audio-capture' | 'network' | 'not-allowed' | 'service-not-allowed' | 'bad-grammar' | 'language-not-supported'
  message: string
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  start(): void
  stop(): void
  abort(): void
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null
  onend: ((this: SpeechRecognition, ev: Event) => any) | null
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null
}

interface SpeechRecognitionConstructor {
  new(): SpeechRecognition
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}
```

**Why This Matters:**
- Prevents TypeScript errors when using Speech API
- Provides autocomplete and type safety
- Documents expected API shape for future developers

### Part 2: Voice Input Hook Implementation

**Location:** `frontend/src/lib/hooks/use-voice-input.ts`

**Complete Hook Structure:**

```typescript
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

// [Include TypeScript declarations from Part 1 above]

interface UseVoiceInputReturn {
  isListening: boolean
  isSupported: boolean
  transcript: string
  startListening: () => void
  stopListening: () => void
  error: string | null
}

export function useVoiceInput(): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)

  const recognitionRef = useRef<SpeechRecognition | null>(null)

  // Initialize Speech Recognition on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognitionAPI) {
      setIsSupported(false)
      return
    }

    setIsSupported(true)
    const recognition = new SpeechRecognitionAPI()

    // Configuration
    recognition.continuous = false  // Single utterance mode
    recognition.interimResults = true  // Real-time feedback
    recognition.maxAlternatives = 1
    recognition.lang = navigator.language || 'en-US'  // User's browser language

    // Event handlers
    recognition.onstart = () => {
      setIsListening(true)
      setError(null)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onerror = (event) => {
      setIsListening(false)

      // Map error codes to user-friendly messages
      switch (event.error) {
        case 'not-allowed':
        case 'service-not-allowed':
          setError('microphone-permission-denied')
          break
        case 'no-speech':
          setError('no-speech-detected')
          break
        case 'network':
          setError('network-error')
          break
        case 'audio-capture':
          setError('no-microphone')
          break
        default:
          setError('unknown-error')
      }
    }

    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcript = result[0].transcript

        if (result.isFinal) {
          finalTranscript += transcript + ' '
        } else {
          interimTranscript += transcript
        }
      }

      // Update state with final or interim transcript
      if (finalTranscript) {
        setTranscript(prev => prev + finalTranscript)
      } else if (interimTranscript) {
        // Show interim results for real-time feedback (optional)
        setTranscript(prev => prev + interimTranscript)
      }
    }

    recognitionRef.current = recognition

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    }
  }, [])

  const startListening = useCallback(() => {
    if (!recognitionRef.current || !isSupported) return

    try {
      setError(null)
      setTranscript('')  // Clear previous transcript
      recognitionRef.current.start()
    } catch (err) {
      console.error('Failed to start speech recognition:', err)
      setError('failed-to-start')
    }
  }, [isSupported])

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return

    try {
      recognitionRef.current.stop()
    } catch (err) {
      console.error('Failed to stop speech recognition:', err)
    }
  }, [])

  return {
    isListening,
    isSupported,
    transcript,
    startListening,
    stopListening,
    error,
  }
}
```

**Key Implementation Details:**

1. **`'use client'` Directive:**
   - Required for Next.js client-side hooks
   - Prevents SSR errors when accessing `window`

2. **Feature Detection:**
   - Check for `SpeechRecognition` or `webkitSpeechRecognition`
   - Set `isSupported` flag for conditional rendering

3. **Configuration:**
   - `continuous: false` - Stops after single utterance (per AC3)
   - `interimResults: true` - Real-time transcript updates
   - `lang: navigator.language` - Use browser's language setting

4. **Error Handling:**
   - Map Speech API error codes to user-friendly error keys
   - Return error state for toast notifications

5. **Transcript Management:**
   - Accumulate final results with space separator
   - Optionally show interim results for real-time feedback
   - Clear transcript on new recording start

6. **Cleanup:**
   - `abort()` on unmount to release microphone
   - Prevent memory leaks with `useRef`

### Part 3: ChatPanel Integration

**Location:** `frontend/src/components/learner/ChatPanel.tsx`

**Modifications Required:**

1. **Import Dependencies (Add to top of file):**

```typescript
import { Mic, MicOff } from 'lucide-react'
import { useVoiceInput } from '@/lib/hooks/use-voice-input'
import { useToast } from '@/lib/hooks/use-toast'
```

2. **Add Voice Input State (Inside component function, before return):**

```typescript
const {
  isListening,
  isSupported,
  transcript,
  startListening,
  stopListening,
  error: voiceError
} = useVoiceInput()

const { toast } = useToast()
const inputRef = useRef<HTMLInputElement>(null)
```

3. **Handle Voice Input Transcript (Add useEffect):**

```typescript
// Update input field when voice transcript changes
useEffect(() => {
  if (transcript && inputRef.current) {
    inputRef.current.value = transcript
  }
}, [transcript])

// Show error toasts for voice input errors
useEffect(() => {
  if (voiceError) {
    let title = ''
    let description = ''

    switch (voiceError) {
      case 'microphone-permission-denied':
        title = t.learner.chat.voiceInput.microphoneError
        description = t.learner.chat.voiceInput.microphoneErrorDesc
        break
      case 'no-speech-detected':
        title = t.learner.chat.voiceInput.noSpeech
        description = t.learner.chat.voiceInput.noSpeechDesc
        break
      case 'network-error':
        title = t.learner.chat.voiceInput.networkError
        description = t.learner.chat.voiceInput.networkErrorDesc
        break
      case 'no-microphone':
        title = t.learner.chat.voiceInput.noMicrophone
        description = t.learner.chat.voiceInput.noMicrophoneDesc
        break
      default:
        title = t.learner.chat.voiceInput.error
        description = t.learner.chat.voiceInput.errorDesc
    }

    toast({
      title,
      description,
      variant: 'destructive',
    })
  }
}, [voiceError, t, toast])
```

4. **Modify Input Form (Replace existing form structure at lines ~369-395):**

```typescript
<div className="flex-shrink-0 border-t p-4">
  <form onSubmit={(e) => { /* existing handler */ }} className="flex gap-2">
    {/* Voice Input Button - Only show if supported */}
    {isSupported && (
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={isListening ? stopListening : startListening}
        aria-label={isListening ? t.learner.chat.voiceInput.stopRecording : t.learner.chat.voiceInput.startRecording}
        className={isListening ? 'text-red-500 animate-pulse' : ''}
      >
        {isListening ? (
          <MicOff className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>
    )}

    {/* Text Input - Add ref */}
    <input
      ref={inputRef}
      type="text"
      name="message"
      placeholder={t.learner.chat.placeholder}
      className="flex-1 px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
      autoComplete="off"
    />

    {/* Send Button - Unchanged */}
    <button
      type="submit"
      className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary"
    >
      {t.learner.chat.send}
    </button>
  </form>
</div>
```

**Key Changes:**

1. **Conditional Rendering:** Only show mic button if `isSupported === true`
2. **Toggle Behavior:** Click toggles between start/stop recording
3. **Visual Feedback:** Pulsing red icon during recording (`animate-pulse` class)
4. **Icon States:** `Mic` when idle, `MicOff` when recording
5. **Accessibility:** Proper `aria-label` with translated text
6. **Input Ref:** Add `ref={inputRef}` to allow programmatic value updates

### Part 4: Add Pulsing Animation CSS

**Location:** `frontend/src/components/learner/ChatPanel.tsx` (or global CSS if preferred)

Tailwind already provides `animate-pulse`, but for custom control:

```typescript
// No additional CSS needed - Tailwind's animate-pulse handles pulsing
// Alternative: Add custom animation in component styles if needed:

const styles = `
  @keyframes recording-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .recording-pulse {
    animation: recording-pulse 1.5s ease-in-out infinite;
  }
`

// Then use className="recording-pulse" instead of animate-pulse
```

**Recommendation:** Use Tailwind's `animate-pulse` as shown above (simpler, no custom CSS needed).

### Part 5: Internationalization (i18n)

**Location 1:** `frontend/src/lib/locales/en-US/index.ts`

**Add to `learner.chat` object (after line ~1329):**

```typescript
learner: {
  chat: {
    // ... existing keys ...
    voiceInput: {
      startRecording: "Start voice input",
      stopRecording: "Stop recording",
      listening: "Listening...",
      transcribing: "Transcribing...",

      // Error messages
      microphoneError: "Microphone access denied",
      microphoneErrorDesc: "Please allow microphone access in your browser settings to use voice input.",
      noSpeech: "No speech detected",
      noSpeechDesc: "Please speak clearly into your microphone and try again.",
      networkError: "Network error",
      networkErrorDesc: "Voice recognition requires an internet connection. Please check your connection and try again.",
      noMicrophone: "No microphone found",
      noMicrophoneDesc: "Please connect a microphone to use voice input.",
      error: "Voice input error",
      errorDesc: "Something went wrong with voice input. Please try typing instead.",
      notSupported: "Voice input not supported",
      notSupportedDesc: "Your browser doesn't support voice input. Please use Chrome, Edge, or Safari.",
    },
  },
}
```

**Location 2:** `frontend/src/lib/locales/fr-FR/index.ts`

**Add French translations (after line ~1329):**

```typescript
learner: {
  chat: {
    // ... existing keys ...
    voiceInput: {
      startRecording: "Démarrer la saisie vocale",
      stopRecording: "Arrêter l'enregistrement",
      listening: "Écoute en cours...",
      transcribing: "Transcription en cours...",

      // Messages d'erreur
      microphoneError: "Accès au microphone refusé",
      microphoneErrorDesc: "Veuillez autoriser l'accès au microphone dans les paramètres de votre navigateur pour utiliser la saisie vocale.",
      noSpeech: "Aucune parole détectée",
      noSpeechDesc: "Veuillez parler clairement dans votre microphone et réessayer.",
      networkError: "Erreur réseau",
      networkErrorDesc: "La reconnaissance vocale nécessite une connexion Internet. Veuillez vérifier votre connexion et réessayer.",
      noMicrophone: "Aucun microphone trouvé",
      noMicrophoneDesc: "Veuillez connecter un microphone pour utiliser la saisie vocale.",
      error: "Erreur de saisie vocale",
      errorDesc: "Un problème est survenu avec la saisie vocale. Veuillez essayer de taper à la place.",
      notSupported: "Saisie vocale non prise en charge",
      notSupportedDesc: "Votre navigateur ne prend pas en charge la saisie vocale. Veuillez utiliser Chrome, Edge ou Safari.",
    },
  },
}
```

**Critical:** BOTH locales must be updated together. Missing translations will cause runtime errors.

### Part 6: Testing Implementation

**Location:** `frontend/src/lib/hooks/__tests__/use-voice-input.test.ts`

**Complete Test Suite:**

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useVoiceInput } from '../use-voice-input'

// Mock SpeechRecognition
class MockSpeechRecognition {
  continuous = false
  interimResults = false
  lang = ''
  maxAlternatives = 1
  onstart: ((event: Event) => void) | null = null
  onend: ((event: Event) => void) | null = null
  onerror: ((event: any) => void) | null = null
  onresult: ((event: any) => void) | null = null

  start() {
    if (this.onstart) {
      this.onstart(new Event('start'))
    }
  }

  stop() {
    if (this.onend) {
      this.onend(new Event('end'))
    }
  }

  abort() {
    if (this.onend) {
      this.onend(new Event('end'))
    }
  }
}

describe('useVoiceInput', () => {
  beforeEach(() => {
    // Mock window.SpeechRecognition
    vi.stubGlobal('SpeechRecognition', MockSpeechRecognition)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should detect Speech API support', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.isSupported).toBe(true)
  })

  it('should detect when Speech API is not supported', () => {
    vi.unstubAllGlobals()
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.isSupported).toBe(false)
  })

  it('should start listening when startListening is called', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
    })
  })

  it('should stop listening when stopListening is called', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
    })

    act(() => {
      result.current.stopListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(false)
    })
  })

  it('should set error on permission denied', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    // Simulate permission denied error
    const recognition = (global as any).SpeechRecognition
    if (recognition.instance && recognition.instance.onerror) {
      act(() => {
        recognition.instance.onerror({
          error: 'not-allowed',
          message: 'Permission denied',
        })
      })
    }

    await waitFor(() => {
      expect(result.current.error).toBe('microphone-permission-denied')
    })
  })

  it('should update transcript on speech result', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    // Simulate speech recognition result
    const recognition = (global as any).SpeechRecognition
    if (recognition.instance && recognition.instance.onresult) {
      act(() => {
        recognition.instance.onresult({
          results: [
            {
              0: { transcript: 'Hello world', confidence: 0.9 },
              isFinal: true,
              length: 1,
            },
          ],
          resultIndex: 0,
        })
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toContain('Hello world')
    })
  })

  it('should clear transcript on new recording start', async () => {
    const { result } = renderHook(() => useVoiceInput())

    // Set initial transcript
    act(() => {
      result.current.startListening()
    })

    // Simulate result
    const recognition = (global as any).SpeechRecognition
    if (recognition.instance && recognition.instance.onresult) {
      act(() => {
        recognition.instance.onresult({
          results: [
            {
              0: { transcript: 'First message', confidence: 0.9 },
              isFinal: true,
              length: 1,
            },
          ],
          resultIndex: 0,
        })
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toContain('First message')
    })

    // Stop and start again
    act(() => {
      result.current.stopListening()
    })

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.transcript).toBe('')
    })
  })

  it('should cleanup on unmount', () => {
    const { unmount } = renderHook(() => useVoiceInput())
    const abortSpy = vi.spyOn(MockSpeechRecognition.prototype, 'abort')

    unmount()

    expect(abortSpy).toHaveBeenCalled()
  })
})
```

**Location:** `frontend/src/components/learner/__tests__/VoiceInput.test.tsx`

**Component Integration Tests:**

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatPanel } from '../ChatPanel'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        chat: {
          placeholder: 'Ask a question...',
          send: 'Send',
          voiceInput: {
            startRecording: 'Start voice input',
            stopRecording: 'Stop recording',
          },
        },
      },
    },
  }),
}))

vi.mock('@/lib/hooks/use-voice-input', () => ({
  useVoiceInput: vi.fn(() => ({
    isListening: false,
    isSupported: true,
    transcript: '',
    startListening: vi.fn(),
    stopListening: vi.fn(),
    error: null,
  })),
}))

describe('ChatPanel Voice Input Integration', () => {
  const queryClient = new QueryClient()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render microphone button when voice input is supported', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Start voice input')
    expect(micButton).toBeInTheDocument()
  })

  it('should not render microphone button when voice input is not supported', () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: false,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    expect(screen.queryByLabelText('Start voice input')).not.toBeInTheDocument()
  })

  it('should call startListening when microphone button is clicked', async () => {
    const mockStartListening = vi.fn()
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: mockStartListening,
      stopListening: vi.fn(),
      error: null,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Start voice input')
    await userEvent.click(micButton)

    expect(mockStartListening).toHaveBeenCalled()
  })

  it('should show recording state with pulsing icon', () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Stop recording')
    expect(micButton).toHaveClass('animate-pulse')
  })

  it('should populate input field with transcript', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    // Update hook to return transcript
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: 'Hello from voice input',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    rerender(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement
    await waitFor(() => {
      expect(input.value).toBe('Hello from voice input')
    })
  })
})
```

**Run Tests:**
```bash
npm run test -- use-voice-input
npm run test -- VoiceInput
npm run test:ui  # Interactive mode
```

### Part 7: Accessibility Checklist

**WCAG 2.1 AA Compliance Verification:**

- [ ] **Keyboard Navigation:**
  - Tab key focuses microphone button
  - Enter/Space key activates button
  - Escape key stops recording (if desired)

- [ ] **ARIA Labels:**
  - `aria-label` on microphone button describes state
  - Changes from "Start voice input" to "Stop recording"

- [ ] **Visual Feedback:**
  - Pulsing animation during recording
  - Different icons for idle vs recording
  - Focus ring visible on keyboard focus

- [ ] **Screen Reader Announcements:**
  - Button state changes announced
  - Error messages announced via toast (role="alert")

- [ ] **Color Independence:**
  - Don't rely on red color alone for recording state
  - Icon + animation provide non-color indicators

- [ ] **Touch Targets:**
  - Button minimum 44×44px (automatically handled by `size="icon"`)

### Part 8: Browser Compatibility Testing Checklist

**Test in These Browsers:**

- [ ] **Chrome/Chromium (Desktop):**
  - Version 33+ required
  - Test with `SpeechRecognition` API
  - Verify permission prompt

- [ ] **Microsoft Edge (Desktop):**
  - Version 79+ required (Chromium-based)
  - Same behavior as Chrome

- [ ] **Safari (macOS):**
  - Version 14.1+ required
  - Uses `webkitSpeechRecognition` prefix
  - May require additional permission prompts

- [ ] **Safari (iOS):**
  - Version 14.1+ required
  - Test on iPhone and iPad
  - Verify microphone permission flow

- [ ] **Android Chrome:**
  - Version 33+ required
  - Test permission prompt
  - Verify touch interaction

- [ ] **Firefox (Desktop & Mobile):**
  - NOT SUPPORTED (as of 2026)
  - Verify graceful degradation (button hidden)
  - No errors in console

**Test Scenarios:**

1. **First Use (Permission Prompt):**
   - Click microphone button
   - Browser shows permission prompt
   - Grant permission → recording starts
   - Deny permission → toast error shown

2. **Normal Usage:**
   - Click button, speak, click again
   - Verify transcript appears in input
   - Edit transcript manually
   - Send message normally

3. **Error Cases:**
   - Deny permission → friendly error message
   - No microphone → error message
   - Network offline → error message (some browsers)
   - Unsupported browser → button hidden

4. **Edge Cases:**
   - Start recording, navigate away → cleanup works
   - Multiple rapid clicks → no crashes
   - Very long recording → handles gracefully

### Part 9: Code Review Self-Checklist

Before marking as complete, verify:

**Functionality:**
- [ ] All 6 acceptance criteria implemented and verified
- [ ] Microphone button appears in chat input (AC1)
- [ ] Recording starts with visual feedback (AC2)
- [ ] Recording stops and transcribes (AC3)
- [ ] Transcript editable before send (AC4)
- [ ] Message sends normally (AC5)
- [ ] Graceful degradation for unsupported browsers (AC6)

**Code Quality:**
- [ ] TypeScript strict mode passes (no `any` types)
- [ ] All imports resolve correctly
- [ ] No console errors or warnings
- [ ] ESLint passes with no violations
- [ ] Prettier formatting applied

**Testing:**
- [ ] Hook unit tests pass (8+ tests)
- [ ] Component integration tests pass (6+ tests)
- [ ] All test files run successfully
- [ ] Coverage for error paths

**i18n:**
- [ ] All strings in en-US locale
- [ ] All strings in fr-FR locale
- [ ] No hardcoded English text in components
- [ ] Error messages translated

**Accessibility:**
- [ ] Keyboard navigation works
- [ ] ARIA labels present and descriptive
- [ ] Focus visible on keyboard focus
- [ ] Screen reader friendly

**Performance:**
- [ ] No memory leaks (cleanup in useEffect)
- [ ] No unnecessary re-renders
- [ ] `useCallback` used where appropriate

**Documentation:**
- [ ] Code comments for complex logic
- [ ] JSDoc comments on public interfaces
- [ ] Dev Agent Record section completed

### Part 10: Common Mistakes to Avoid

**🚫 DON'T:**

1. **Use MediaRecorder API:**
   - ❌ Record audio → upload to backend → call Whisper
   - ✅ Use browser's `SpeechRecognition` (client-side, zero cost)

2. **Forget Feature Detection:**
   - ❌ Assume `SpeechRecognition` exists
   - ✅ Check support and hide button if unavailable

3. **Hardcode English:**
   - ❌ `"Start Recording"` in component
   - ✅ `{t.learner.chat.voiceInput.startRecording}`

4. **Use `any` Type:**
   - ❌ `recognition: any`
   - ✅ `recognition: SpeechRecognition` with proper types

5. **Skip Cleanup:**
   - ❌ No `useEffect` return function
   - ✅ Always `return () => recognition?.abort()`

6. **Auto-Start Recording:**
   - ❌ `useEffect(() => startListening(), [])`
   - ✅ Only start on user interaction (click)

7. **Store Permission in localStorage:**
   - ❌ `localStorage.setItem('micPermission', 'granted')`
   - ✅ Browser handles permission state automatically

8. **Create Backend Endpoints:**
   - ❌ POST `/chat/transcribe` with audio file
   - ✅ No backend changes needed at all

9. **Use `fireEvent` in Tests:**
   - ❌ `fireEvent.click(button)`
   - ✅ `await userEvent.click(button)`

10. **Modify Existing Chat Logic:**
    - ❌ Change message submission flow
    - ✅ Only add voice button, transcript populates input

**✅ DO:**

1. Use `'use client'` directive in hook
2. Declare TypeScript types for Speech API
3. Check for both `SpeechRecognition` and `webkitSpeechRecognition`
4. Handle all error cases with user-friendly messages
5. Add BOTH en-US and fr-FR translations
6. Test in Chrome, Safari, Edge
7. Verify accessibility with keyboard and screen reader
8. Cleanup listeners on unmount
9. Show pulsing visual feedback during recording
10. Keep implementation simple and focused

---

## 🎉 STORY COMPLETION CHECKLIST

Use this checklist to verify all requirements before marking story as "done":

### Acceptance Criteria Verification
- [ ] **AC1:** Microphone button visible in chat input
- [ ] **AC2:** Recording starts with visual indicator and permission prompt
- [ ] **AC3:** Recording stops and transcribes on button click
- [ ] **AC4:** Transcript editable before sending
- [ ] **AC5:** Message sends normally with voice-transcribed text
- [ ] **AC6:** Graceful degradation with friendly error message

### Code Implementation
- [ ] `use-voice-input.ts` hook created with TypeScript types
- [ ] ChatPanel modified with voice button integration
- [ ] Pulsing animation applied during recording
- [ ] Error handling with toast notifications

### Internationalization
- [ ] All strings added to `en-US/index.ts`
- [ ] All strings added to `fr-FR/index.ts`
- [ ] No hardcoded English text in components

### Testing
- [ ] Hook unit tests passing (8+ tests)
- [ ] Component integration tests passing (6+ tests)
- [ ] Error path tests passing
- [ ] Accessibility tests passing

### Browser Compatibility
- [ ] Tested in Chrome/Edge (SpeechRecognition)
- [ ] Tested in Safari (webkitSpeechRecognition)
- [ ] Tested on mobile (iOS Safari, Android Chrome)
- [ ] Verified Firefox shows no button (graceful degradation)

### Accessibility
- [ ] Keyboard navigation works (Tab, Enter/Space)
- [ ] ARIA labels present and dynamic
- [ ] Focus visible on keyboard focus
- [ ] Screen reader announces state changes
- [ ] Touch targets minimum 44×44px

### Performance
- [ ] No memory leaks (cleanup verified)
- [ ] No console errors or warnings
- [ ] ESLint passes
- [ ] TypeScript compiles with no errors

### Documentation
- [ ] Code comments for complex logic
- [ ] Dev Agent Record section completed
- [ ] File list updated with all modified files

### Final Verification
- [ ] All 6 tasks completed
- [ ] All subtasks checked off
- [ ] Code review self-checklist passed
- [ ] Ready for peer code review

---

**This story is now ready for implementation by the dev agent. All context, patterns, and guardrails have been provided to ensure flawless execution.** 🚀
