# Story 1.4: Learner Onboarding Questionnaire

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want to complete a short onboarding questionnaire on first login,
So that the AI teacher can personalize my learning experience.

## Acceptance Criteria

1. **Given** a learner logs in for the first time (`onboarding_completed` is false) **When** they are redirected to the platform **Then** they see the onboarding questionnaire screen before accessing modules

2. **Given** the onboarding questionnaire is displayed **When** the learner answers the questions (AI familiarity, job type, job description) **Then** their profile is updated with the responses and `onboarding_completed` is set to true

3. **Given** a learner has completed onboarding **When** they log in again **Then** they skip the questionnaire and go directly to module selection

4. **Given** a learner is on the questionnaire **When** they submit answers **Then** the questionnaire has a conversational, friendly tone (3-4 questions, not a form)

## Tasks / Subtasks

- [ ] Task 1: Create profile update API endpoint (AC: #2)
  - [ ] 1.1: Add `OnboardingSubmit` Pydantic model to `api/models.py` with fields: `ai_familiarity` (string enum: "none", "heard_of_it", "used_occasionally", "use_daily"), `job_type` (string), `job_description` (string)
  - [ ] 1.2: Add `UserProfileResponse` Pydantic model to `api/models.py` returning user profile data including onboarding status
  - [ ] 1.3: Create `api/routers/users.py` with `PUT /users/me/onboarding` endpoint protected by `get_current_user()` dependency
  - [ ] 1.4: Create `api/user_service.py` `complete_onboarding(user_id, ai_familiarity, job_type, job_description)` function
  - [ ] 1.5: In user_service, update User record: set `profile` dict with questionnaire answers, set `onboarding_completed = true`
  - [ ] 1.6: Register users router in `api/main.py`

- [ ] Task 2: Create onboarding page in learner route group (AC: #1, #4)
  - [ ] 2.1: Create `frontend/src/app/(learner)/onboarding/page.tsx` — the onboarding page
  - [ ] 2.2: Create `frontend/src/app/(learner)/layout.tsx` — learner route group layout (minimal shell, no sidebar)
  - [ ] 2.3: Ensure learner layout checks authentication (redirect to `/login` if not authenticated)

- [ ] Task 3: Create OnboardingQuestionnaire component (AC: #2, #4)
  - [ ] 3.1: Create `frontend/src/components/learner/OnboardingQuestionnaire.tsx`
  - [ ] 3.2: Implement conversational, step-by-step UI (NOT a traditional form). One question at a time with smooth transitions.
  - [ ] 3.3: Question 1: "What's your role?" — free text input for job type (e.g., "Project Manager", "Data Analyst")
  - [ ] 3.4: Question 2: "How familiar are you with AI?" — 4 visual choice cards: "Never used it" / "Heard of it" / "Used it occasionally" / "Use it daily"
  - [ ] 3.5: Question 3: "Tell us about your day-to-day work" — textarea for job description (2-3 sentences)
  - [ ] 3.6: Each question appears one at a time. After answering, the next slides in. Previous answers visible above as confirmed text (not editable form fields).
  - [ ] 3.7: Final screen: brief confirmation "All set! Let's get started." with a "Start Learning" button
  - [ ] 3.8: Submit button calls `PUT /users/me/onboarding` with collected answers
  - [ ] 3.9: On successful submission, redirect to `/modules` (module selection screen)

- [ ] Task 4: Add onboarding redirect guard (AC: #1, #3)
  - [ ] 4.1: In the `(learner)/layout.tsx`, after auth check, check if `user.onboarding_completed === false`
  - [ ] 4.2: If onboarding not completed AND current path is NOT `/onboarding`, redirect to `/onboarding`
  - [ ] 4.3: If onboarding IS completed AND current path IS `/onboarding`, redirect to `/modules`
  - [ ] 4.4: Requires the `GET /auth/me` endpoint (from Story 1.1) to return `onboarding_completed` field

- [ ] Task 5: Create API module and hook for onboarding (AC: #2)
  - [ ] 5.1: Create `frontend/src/lib/api/users.ts` with `usersApi.submitOnboarding(data)` function
  - [ ] 5.2: Create `frontend/src/lib/hooks/use-onboarding.ts` with `useSubmitOnboarding()` mutation hook (TanStack Query)
  - [ ] 5.3: On mutation success, invalidate user query to refresh `onboarding_completed` status

- [ ] Task 6: Add i18n keys for onboarding (AC: #4)
  - [ ] 6.1: Add `onboarding` section to `frontend/src/lib/locales/en-US/index.ts`
  - [ ] 6.2: Add `onboarding` section to `frontend/src/lib/locales/fr-FR/index.ts`
  - [ ] 6.3: Keys needed: `title`, `subtitle`, `questionRole`, `questionRolePlaceholder`, `questionAiFamiliarity`, `aiFamiliarityNone`, `aiFamiliarityHeardOfIt`, `aiFamiliarityOccasional`, `aiFamiliarityDaily`, `questionJobDescription`, `jobDescriptionPlaceholder`, `confirmationTitle`, `confirmationSubtitle`, `startLearning`, `next`, `back`

- [ ] Task 7: Write tests (AC: #1, #2, #3)
  - [ ] 7.1: Create `tests/test_onboarding.py`
  - [ ] 7.2: Test `PUT /users/me/onboarding` happy path — profile updated, onboarding_completed set to true
  - [ ] 7.3: Test `PUT /users/me/onboarding` with invalid data — returns 400
  - [ ] 7.4: Test `PUT /users/me/onboarding` without authentication — returns 401
  - [ ] 7.5: Test `GET /auth/me` returns correct `onboarding_completed` status before and after onboarding

## Dev Notes

### Architecture Decisions

- **Conversational UI, NOT a form.** The UX spec is explicit: "Questionnaire feels like conversation. Short, friendly, gets the AI context without feeling like a form." This means one question at a time with smooth transitions, not a traditional multi-field form. The emotional goal is "mild engagement" — conversational tone, fast completion.
- **Backend layering MANDATORY:** Router (`api/routers/users.py`) → Service (`api/user_service.py`) → Domain (`open_notebook/domain/user.py`) → Database. The router never accesses the database directly.
- **Profile stored as flexible object on User model.** The User model (from Story 1.1) has `profile` as `option<object>` FLEXIBLE type. Store questionnaire answers there: `{ "ai_familiarity": "...", "job_type": "...", "job_description": "..." }`.
- **Learner route group.** This story introduces the `(learner)` route group. The layout must be minimal — no admin sidebar, no existing dashboard chrome. Clean, warm, focused.
- **This is a full-stack story.** Backend endpoint + frontend page + component + i18n + redirect guard. All layers must be implemented.

### Critical Implementation Details

**Questionnaire Data Model:**
```python
# Stored in User.profile field (flexible object in SurrealDB)
{
    "ai_familiarity": "used_occasionally",  # "none" | "heard_of_it" | "used_occasionally" | "use_daily"
    "job_type": "Project Manager",           # Free text
    "job_description": "I coordinate teams and track deliverables across multiple projects"  # Free text
}
```

**API Endpoint:**
```python
# api/routers/users.py
@router.put("/users/me/onboarding")
async def complete_onboarding(
    data: OnboardingSubmit,
    current_user: User = Depends(get_current_user)
):
    """Complete learner onboarding questionnaire."""
    if current_user.role != "learner":
        logger.error(f"Non-learner user {current_user.id} attempted onboarding")
        raise HTTPException(status_code=403, detail="Only learners complete onboarding")

    updated_user = await user_service.complete_onboarding(
        user_id=current_user.id,
        ai_familiarity=data.ai_familiarity,
        job_type=data.job_type,
        job_description=data.job_description
    )
    return UserProfileResponse.from_user(updated_user)
```

**Pydantic Models:**
```python
# api/models.py
class OnboardingSubmit(BaseModel):
    ai_familiarity: Literal["none", "heard_of_it", "used_occasionally", "use_daily"]
    job_type: str = Field(..., min_length=1, max_length=100)
    job_description: str = Field(..., min_length=1, max_length=500)

class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    company_id: Optional[str]
    profile: Optional[dict]
    onboarding_completed: bool
```

**Frontend Redirect Logic:**
```typescript
// frontend/src/app/(learner)/layout.tsx
export default function LearnerLayout({ children }) {
  const { user, isLoading } = useCurrentUser()
  const pathname = usePathname()

  if (isLoading) return <LoadingSpinner />
  if (!user) redirect('/login')
  if (user.role !== 'learner') redirect('/notebooks') // admin goes to admin

  if (!user.onboarding_completed && pathname !== '/onboarding') {
    redirect('/onboarding')
  }
  if (user.onboarding_completed && pathname === '/onboarding') {
    redirect('/modules')
  }

  return <LearnerShell>{children}</LearnerShell>
}
```

**Conversational UI Pattern:**
```typescript
// Component shows one question at a time, slides to next
// Step 0: Welcome message "Welcome! Let's get to know you."
// Step 1: "What's your role?" → text input
// Step 2: "How familiar are you with AI?" → 4 visual cards
// Step 3: "Tell us about your day-to-day work" → textarea
// Step 4: "All set! Let's get started." → submit button

const [step, setStep] = useState(0)
const [answers, setAnswers] = useState({
  job_type: '',
  ai_familiarity: '',
  job_description: ''
})
```

### Existing Code Patterns to Follow

**i18n Pattern** (from existing `en-US/index.ts` and `fr-FR/index.ts`):
```typescript
// Add to en-US/index.ts
onboarding: {
  title: "Welcome!",
  subtitle: "Let's get to know you so we can personalize your learning experience.",
  questionRole: "What's your role?",
  questionRolePlaceholder: "e.g. Project Manager, Data Analyst...",
  questionAiFamiliarity: "How familiar are you with AI?",
  aiFamiliarityNone: "Never used it",
  aiFamiliarityHeardOfIt: "Heard of it",
  aiFamiliarityOccasional: "Used it occasionally",
  aiFamiliarityDaily: "Use it daily",
  questionJobDescription: "Tell us about your day-to-day work",
  jobDescriptionPlaceholder: "What do you spend most of your time doing?",
  confirmationTitle: "All set!",
  confirmationSubtitle: "Let's get started with your learning.",
  startLearning: "Start Learning",
  next: "Next",
  back: "Back"
}
```

```typescript
// Add to fr-FR/index.ts
onboarding: {
  title: "Bienvenue !",
  subtitle: "Faisons connaissance pour personnaliser votre parcours d'apprentissage.",
  questionRole: "Quel est votre poste ?",
  questionRolePlaceholder: "ex. Chef de projet, Analyste de donnees...",
  questionAiFamiliarity: "Quelle est votre familiarite avec l'IA ?",
  aiFamiliarityNone: "Jamais utilisee",
  aiFamiliarityHeardOfIt: "J'en ai entendu parler",
  aiFamiliarityOccasional: "Utilisee occasionnellement",
  aiFamiliarityDaily: "Utilisee quotidiennement",
  questionJobDescription: "Parlez-nous de votre quotidien professionnel",
  jobDescriptionPlaceholder: "A quoi consacrez-vous la majorite de votre temps ?",
  confirmationTitle: "C'est parti !",
  confirmationSubtitle: "Commencons votre parcours d'apprentissage.",
  startLearning: "Commencer",
  next: "Suivant",
  back: "Retour"
}
```

**Hook Pattern** (from existing `use-auth.ts`):
```typescript
// frontend/src/lib/hooks/use-onboarding.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/lib/api/users'

export function useSubmitOnboarding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: usersApi.submitOnboarding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    }
  })
}
```

**API Module Pattern** (from existing `sources.ts`, `notebooks.ts`):
```typescript
// frontend/src/lib/api/users.ts
import { apiClient } from './client'

export const usersApi = {
  submitOnboarding: async (data: {
    ai_familiarity: string
    job_type: string
    job_description: string
  }) => {
    const response = await apiClient.put('/users/me/onboarding', data)
    return response.data
  }
}
```

### UX Requirements from Design Specification

**Emotional Journey:**
| Stage | Target Emotion | Design Implication |
|-------|---------------|-------------------|
| Questionnaire | Mild engagement | 3-4 questions, conversational tone, fast |
| Completion | Calm readiness | Simple "All set" confirmation, no fanfare |

**Design Principles:**
- Conversational tone, NOT a form. One question at a time.
- No gamification, no badges, no celebration animations.
- Professional, warm, calm tone. Respect intelligence.
- Inter font for learner interface (if configured), system fonts fallback.
- Warm neutral color palette with CSS custom properties.
- Desktop-only MVP. No mobile responsive needed.
- WCAG 2.1 Level AA: keyboard navigation, focus management, screen reader labels.
- 44x44px minimum touch targets for interactive elements.

**Visual Direction (Design Direction A — Minimal Warmth):**
- Clean, minimal chrome. White/warm-neutral background.
- Subtle shadows, no heavy borders.
- AI familiarity options as visual cards, not a dropdown.
- Smooth transitions between questions (150ms ease).

### Dependencies

**Depends on (must be completed first):**
- **Story 1.1**: User Registration & Login (Backend) — provides User domain model, `get_current_user()` dependency, auth router with `/auth/me` endpoint, migration 18 for user table
- **Story 1.2**: Role-Based Access Control & Route Protection — provides `require_learner()` dependency, frontend middleware.ts for route protection, `(learner)` route group setup

**Note on dependency gap:** Stories 1.2 and 1.3 are still in backlog. This story requires:
- The `get_current_user()` FastAPI dependency (from Story 1.1)
- The `(learner)` route group and its layout (introduced here, but role routing from Story 1.2 directs learners to this group)
- The User model with `onboarding_completed` field (from Story 1.1, migration 18)

If Story 1.2 is not yet implemented when development begins, the developer should:
1. Create the `(learner)` route group and layout as part of this story
2. Implement a simplified auth check (just verify logged in, defer role-based routing to 1.2)
3. Ensure the onboarding page works end-to-end even without full role routing

### Environment Variables

No new environment variables required. Uses existing `JWT_SECRET_KEY` from Story 1.1.

### Anti-Patterns to Avoid

| DO NOT | DO INSTEAD |
|--------|-----------|
| Build a traditional multi-field form | Conversational step-by-step UI, one question at a time |
| Use a dropdown for AI familiarity | Use visual choice cards (4 options) |
| Add celebration animations on completion | Calm "All set" confirmation, professional tone |
| Store onboarding data in localStorage | Store in User.profile via API call |
| Duplicate server state in Zustand | Use TanStack Query for user data |
| Skip French translations | Add BOTH en-US and fr-FR keys |
| Access database from router | Router → Service → Domain → Database |
| Use camelCase in Python | Use snake_case everywhere |
| Create mobile responsive layout | Desktop-only MVP |
| Put learner components in admin folder | `components/learner/OnboardingQuestionnaire.tsx` |

### Project Structure Notes

- **Onboarding page**: `frontend/src/app/(learner)/onboarding/page.tsx` (NEW)
- **Learner layout**: `frontend/src/app/(learner)/layout.tsx` (NEW)
- **OnboardingQuestionnaire component**: `frontend/src/components/learner/OnboardingQuestionnaire.tsx` (NEW)
- **Users API module**: `frontend/src/lib/api/users.ts` (NEW)
- **Onboarding hook**: `frontend/src/lib/hooks/use-onboarding.ts` (NEW)
- **Users router**: `api/routers/users.py` (NEW)
- **User service**: `api/user_service.py` (EXTEND — add `complete_onboarding()`)
- **API models**: `api/models.py` (EXTEND — add `OnboardingSubmit`, `UserProfileResponse`)
- **Main app**: `api/main.py` (EXTEND — register users router)
- **i18n EN**: `frontend/src/lib/locales/en-US/index.ts` (EXTEND)
- **i18n FR**: `frontend/src/lib/locales/fr-FR/index.ts` (EXTEND)
- **Tests**: `tests/test_onboarding.py` (NEW)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — User model with profile field]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Emotional Journey Mapping — Questionnaire stage]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Effortless Interactions — "Questionnaire feels like conversation"]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design Direction A (Minimal Warmth)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Critical Success Moments]
- [Source: _bmad-output/planning-artifacts/prd.md#FR4 — Learner onboarding questionnaire]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey 2 — Sophie's onboarding experience]
- [Source: _bmad-output/implementation-artifacts/1-1-user-registration-and-login-backend.md — User model, auth patterns, migration 18]
- [Source: frontend/src/lib/locales/en-US/index.ts — existing i18n pattern]
- [Source: frontend/src/lib/locales/fr-FR/index.ts — existing i18n pattern]
- [Source: frontend/src/lib/hooks/use-auth.ts — existing hook pattern]
- [Source: frontend/src/lib/api/client.ts — existing API client pattern]
- [Source: frontend/src/app/(auth)/login/page.tsx — existing auth route pattern]
- [Source: frontend/src/app/(dashboard)/layout.tsx — existing protected layout pattern]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
