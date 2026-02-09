# Story 7.6: User & Company Data Deletion

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform operator**,
I want to completely delete all data for a specific user or company,
So that the platform supports GDPR-aware data management.

## Acceptance Criteria

**AC1:** Given an admin requests deletion of a user
When the deletion is executed
Then all user data is removed: profile, conversations (LangGraph checkpoints), learning progress, quiz results, token usage records
And no orphaned records remain

**AC2:** Given an admin requests deletion of a company
When the deletion is executed
Then all company data is removed: company record, all member users (and their data per above), all module assignments
And the admin is warned and must confirm before proceeding

**AC3:** Given a deletion request
When it targets a company with active learners
Then a confirmation prompt lists the number of users and records that will be deleted

## Tasks / Subtasks

- [ ] Task 1: User Cascade Deletion Domain Layer (AC: 1)
  - [ ] Create `open_notebook/domain/user_deletion.py` module
  - [ ] Implement `delete_user_cascade(user_id: str) -> UserDeletionReport` function
  - [ ] Delete LearnerObjectiveProgress records: `DELETE learner_objective_progress WHERE user_id = $user_id`
  - [ ] Delete LangGraph checkpoints: Query SQLite checkpoint DB, delete threads matching `user:{user_id}:*`
  - [ ] Delete ModuleAssignment records: `DELETE module_assignment WHERE company_id = $company_id AND assigned_by = $user_id`
  - [ ] Delete user-created artifacts (quizzes, notes): `DELETE quiz WHERE user_id = $user_id`, `DELETE note WHERE user_id = $user_id`
  - [ ] Delete User record: `user.delete()`
  - [ ] Return `UserDeletionReport` with counts of deleted records per type
  - [ ] Handle missing user gracefully (404)
  - [ ] Test cascade deletion with mock data

- [ ] Task 2: Company Cascade Deletion Domain Layer (AC: 2, 3)
  - [ ] Create `get_company_deletion_summary(company_id: str) -> CompanyDeletionSummary` function
  - [ ] Query all users with `company_id = $company_id`
  - [ ] Query all module assignments: `COUNT module_assignment WHERE company_id = $company_id`
  - [ ] Return summary: `CompanyDeletionSummary(user_count, assignment_count, affected_notebooks)`
  - [ ] Implement `delete_company_cascade(company_id: str) -> CompanyDeletionReport` function
  - [ ] Delete all member users via `delete_user_cascade()` for each user (cascade user data)
  - [ ] Delete all ModuleAssignment records: `DELETE module_assignment WHERE company_id = $company_id`
  - [ ] Delete Company record: `company.delete()`
  - [ ] Return `CompanyDeletionReport` with aggregate counts
  - [ ] Handle missing company gracefully (404)
  - [ ] Test cascade deletion with multiple users

- [ ] Task 3: LangGraph Checkpoint Deletion Utility (AC: 1)
  - [ ] Create `open_notebook/observability/checkpoint_cleanup.py` module
  - [ ] Implement `delete_user_checkpoints(user_id: str) -> int` function
  - [ ] Connect to LangGraph SQLite checkpoint DB: `sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)`
  - [ ] Query checkpoints table for thread_ids matching pattern: `user:{user_id}:notebook:%`
  - [ ] Delete matching checkpoint records (LangGraph internal tables)
  - [ ] Return count of deleted checkpoint threads
  - [ ] Handle SQLite connection errors gracefully (log warning, continue)
  - [ ] Test checkpoint deletion with seeded data
  - [ ] Add utility function: `list_user_checkpoint_threads(user_id: str) -> List[str]` for debugging

- [ ] Task 4: Admin API Endpoint - User Deletion (AC: 1)
  - [ ] Create `DELETE /admin/users/{user_id}` endpoint in `api/routers/users.py`
  - [ ] Require `require_admin()` dependency for auth
  - [ ] Call `delete_user_cascade(user_id)` from domain layer
  - [ ] Return 200 with `UserDeletionReport` response model
  - [ ] Return 404 if user not found
  - [ ] Add structured logging: `logger.info(f"User {user_id} deleted", extra={"user_id": user_id, "admin_id": admin.id})`
  - [ ] Test endpoint with authenticated admin user
  - [ ] Test endpoint rejects non-admin users (403)
  - [ ] Test 404 response for non-existent user

- [ ] Task 5: Admin API Endpoint - Company Deletion Preview (AC: 3)
  - [ ] Create `GET /admin/companies/{company_id}/deletion-summary` endpoint in `api/routers/companies.py`
  - [ ] Require `require_admin()` dependency
  - [ ] Call `get_company_deletion_summary(company_id)` from domain layer
  - [ ] Return `CompanyDeletionSummary` response model with counts
  - [ ] Return 404 if company not found
  - [ ] Test endpoint returns accurate counts
  - [ ] Test response includes affected_notebooks list

- [ ] Task 6: Admin API Endpoint - Company Deletion (AC: 2, 3)
  - [ ] Create `DELETE /admin/companies/{company_id}` endpoint in `api/routers/companies.py`
  - [ ] Require `require_admin()` dependency
  - [ ] Add query parameter: `?confirm=true` (required to proceed)
  - [ ] If `confirm=false` or missing: Return 400 with error: "Must confirm deletion"
  - [ ] Call `delete_company_cascade(company_id)` from domain layer
  - [ ] Return 200 with `CompanyDeletionReport` response model
  - [ ] Return 404 if company not found
  - [ ] Add structured logging: `logger.warning(f"Company {company_id} deleted", extra={"company_id": company_id, "admin_id": admin.id})`
  - [ ] Test endpoint with `confirm=true`
  - [ ] Test endpoint rejects without confirmation (400)
  - [ ] Test cascade deletion removes all company data

- [ ] Task 7: Pydantic Response Models (AC: 1, 2, 3)
  - [ ] Create `api/models/deletion_models.py` module
  - [ ] Define `UserDeletionReport` model: `user_id, deleted_progress_records, deleted_checkpoints, deleted_artifacts, total_deleted`
  - [ ] Define `CompanyDeletionSummary` model: `company_id, user_count, assignment_count, affected_notebooks: List[str]`
  - [ ] Define `CompanyDeletionReport` model: `company_id, deleted_users, deleted_assignments, deleted_companies, total_deleted`
  - [ ] Add docstrings for all models
  - [ ] Test model validation with example data

- [ ] Task 8: Audit Logging for Deletions (AC: 1, 2)
  - [ ] Add structured log entries to all deletion operations
  - [ ] User deletion log: `logger.warning(f"User deletion cascade", extra={"user_id": ..., "admin_id": ..., "report": ...})`
  - [ ] Company deletion log: `logger.error(f"Company deletion cascade", extra={"company_id": ..., "admin_id": ..., "report": ...})`
  - [ ] Include deletion report in log extra data
  - [ ] Test audit logs appear in Loguru output
  - [ ] Test log severity levels (WARNING for user, ERROR for company)

- [ ] Task 9: Backend Testing - Cascade Deletion (All ACs)
  - [ ] Unit tests: `tests/test_user_deletion.py` - Test `delete_user_cascade()` function
  - [ ] Unit tests: `tests/test_company_deletion.py` - Test `delete_company_cascade()` function
  - [ ] Unit tests: `tests/test_checkpoint_cleanup.py` - Test LangGraph checkpoint deletion
  - [ ] Integration tests: Test full user deletion via API endpoint
  - [ ] Integration tests: Test full company deletion via API endpoint
  - [ ] Test orphan record detection (verify no orphans remain)
  - [ ] Test deletion summary accuracy
  - [ ] Minimum 15 tests total (5 unit + 10 integration)
  - [ ] All tests passing with 100% coverage of deletion functions

- [ ] Task 10: Update Sprint Status & Story File (All ACs)
  - [ ] Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: Story 7.6 status to "review"
  - [ ] Update this story file with completion notes
  - [ ] Add Dev Agent Record section with agent model, file list, completion notes
  - [ ] Document any edge cases or known limitations

## Dev Notes

### Story Overview

This is **Story 7.6 in Epic 7: Error Handling, Observability & Data Privacy**. It implements comprehensive data deletion for users and companies to support GDPR-aware data management and the "right to be forgotten."

**Key Deliverables:**
- User cascade deletion: Removes all user data across SurrealDB + LangGraph SQLite checkpoints
- Company cascade deletion: Removes company + all member users + all module assignments
- Deletion preview/confirmation for companies (prevent accidental mass deletion)
- Comprehensive deletion reports with record counts per type
- Admin-only API endpoints with audit logging

**Critical Context:**
- **FR48** (Complete user data deletion support)
- **FR49** (Complete company data deletion support)
- **NFR7** (Learner data isolated per company at application level)
- Builds on Story 2.1 (Company management), 1.2 (User model, RBAC), 4.8 (Chat history persistence)
- Complements Story 7.5 (Data isolation audit - ensures no cross-company leakage before deletion)
- **CRITICAL**: No cascade deletion currently exists in codebase - all relationships must be handled manually

### Architecture Patterns (MANDATORY)

**Current Deletion Gaps (From Explore Agent Analysis):**

The codebase has **NO automatic cascade deletion** except for Source → source_embedding/source_insight (database event). This story must implement application-level cascade for:

```
User Deletion Must Remove:
├── learner_objective_progress (learning progress records)
├── LangGraph checkpoints (SQLite: thread_id = "user:{user_id}:*")
├── module_assignment (if user is assigned_by admin)
├── quiz (user-created quizzes)
├── note (user-created notes)
└── user (final record deletion)

Company Deletion Must Remove:
├── All member users (via delete_user_cascade for each)
│   └── (triggers all User cascades above for each user)
├── module_assignment (company-to-notebook links)
└── company (final record deletion)
```

**Cascade Deletion Service Pattern:**

```python
# open_notebook/domain/user_deletion.py

from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
from open_notebook.database.repository import repo_query, repo_delete
from open_notebook.domain.user import User
from open_notebook.domain.learner_objective_progress import LearnerObjectiveProgress
from open_notebook.observability.checkpoint_cleanup import delete_user_checkpoints

class UserDeletionReport(BaseModel):
    """Report of deleted records during user cascade deletion."""
    user_id: str
    deleted_progress_records: int = 0
    deleted_checkpoints: int = 0
    deleted_quiz_records: int = 0
    deleted_note_records: int = 0
    deleted_assignment_records: int = 0
    total_deleted: int = 0

async def delete_user_cascade(user_id: str) -> UserDeletionReport:
    """
    Delete user and all associated data (GDPR-compliant cascade).

    Cascades to:
    - learner_objective_progress (learning progress)
    - LangGraph checkpoints (conversation history)
    - module_assignment (if user is assigned_by admin)
    - quiz (user-created quizzes)
    - note (user-created notes)

    Args:
        user_id: User record ID (e.g., "user:alice")

    Returns:
        UserDeletionReport with counts of deleted records

    Raises:
        ValueError: If user not found
    """
    # Validate user exists
    user = await User.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    report = UserDeletionReport(user_id=user_id)

    # Delete learner progress records
    progress_result = await repo_query(
        "DELETE learner_objective_progress WHERE user_id = $uid RETURN BEFORE",
        {"uid": user_id}
    )
    report.deleted_progress_records = len(progress_result) if progress_result else 0

    # Delete LangGraph checkpoints (SQLite)
    try:
        report.deleted_checkpoints = delete_user_checkpoints(user_id)
    except Exception as e:
        logger.warning(f"Failed to delete checkpoints for {user_id}: {e}")
        # Continue deletion even if checkpoints fail

    # Delete user-created quizzes
    quiz_result = await repo_query(
        "DELETE quiz WHERE created_by = $uid RETURN BEFORE",
        {"uid": user_id}
    )
    report.deleted_quiz_records = len(quiz_result) if quiz_result else 0

    # Delete user-created notes
    note_result = await repo_query(
        "DELETE note WHERE user_id = $uid RETURN BEFORE",
        {"uid": user_id}
    )
    report.deleted_note_records = len(note_result) if note_result else 0

    # Delete module assignments where user is the assigner
    assignment_result = await repo_query(
        "DELETE module_assignment WHERE assigned_by = $uid RETURN BEFORE",
        {"uid": user_id}
    )
    report.deleted_assignment_records = len(assignment_result) if assignment_result else 0

    # Delete user record
    await user.delete()

    # Calculate total
    report.total_deleted = (
        report.deleted_progress_records +
        report.deleted_checkpoints +
        report.deleted_quiz_records +
        report.deleted_note_records +
        report.deleted_assignment_records +
        1  # User record itself
    )

    logger.warning(
        f"User deletion cascade completed",
        extra={
            "user_id": user_id,
            "report": report.model_dump()
        }
    )

    return report
```

**Company Deletion Service Pattern:**

```python
# open_notebook/domain/company_deletion.py

from typing import List
from pydantic import BaseModel
from loguru import logger
from open_notebook.database.repository import repo_query
from open_notebook.domain.company import Company
from open_notebook.domain.user_deletion import delete_user_cascade, UserDeletionReport

class CompanyDeletionSummary(BaseModel):
    """Preview of what will be deleted."""
    company_id: str
    company_name: str
    user_count: int
    assignment_count: int
    affected_notebooks: List[str]

class CompanyDeletionReport(BaseModel):
    """Report of deleted records during company cascade deletion."""
    company_id: str
    deleted_users: int = 0
    deleted_user_data_records: int = 0  # Aggregate from user cascades
    deleted_assignments: int = 0
    total_deleted: int = 0
    user_deletion_reports: List[UserDeletionReport] = []

async def get_company_deletion_summary(company_id: str) -> CompanyDeletionSummary:
    """
    Get preview of what will be deleted if company is removed.

    Args:
        company_id: Company record ID

    Returns:
        CompanyDeletionSummary with counts and affected resources

    Raises:
        ValueError: If company not found
    """
    company = await Company.get(company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    # Count member users
    user_count = await company.get_member_count()

    # Count module assignments
    assignments = await repo_query(
        "SELECT notebook_id FROM module_assignment WHERE company_id = $cid",
        {"cid": company_id}
    )
    assignment_count = len(assignments) if assignments else 0
    affected_notebooks = [a.get("notebook_id") for a in assignments] if assignments else []

    return CompanyDeletionSummary(
        company_id=company_id,
        company_name=company.name,
        user_count=user_count,
        assignment_count=assignment_count,
        affected_notebooks=affected_notebooks,
    )

async def delete_company_cascade(company_id: str) -> CompanyDeletionReport:
    """
    Delete company and all associated data (GDPR-compliant cascade).

    Cascades to:
    - All member users (via delete_user_cascade for each)
    - module_assignment records
    - company record

    Args:
        company_id: Company record ID

    Returns:
        CompanyDeletionReport with aggregate counts

    Raises:
        ValueError: If company not found
    """
    company = await Company.get(company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    report = CompanyDeletionReport(company_id=company_id)

    # Get all member users
    users = await repo_query(
        "SELECT id FROM user WHERE company_id = $cid",
        {"cid": company_id}
    )

    # Delete each user (triggers user cascade)
    if users:
        for user_record in users:
            user_id = user_record.get("id")
            try:
                user_report = await delete_user_cascade(user_id)
                report.user_deletion_reports.append(user_report)
                report.deleted_users += 1
                report.deleted_user_data_records += user_report.total_deleted
            except Exception as e:
                logger.error(f"Failed to delete user {user_id} during company cascade: {e}")
                # Continue with other users

    # Delete module assignments
    assignment_result = await repo_query(
        "DELETE module_assignment WHERE company_id = $cid RETURN BEFORE",
        {"cid": company_id}
    )
    report.deleted_assignments = len(assignment_result) if assignment_result else 0

    # Delete company record
    await company.delete()

    # Calculate total
    report.total_deleted = (
        report.deleted_user_data_records +
        report.deleted_assignments +
        1  # Company record itself
    )

    logger.error(
        f"Company deletion cascade completed",
        extra={
            "company_id": company_id,
            "report": report.model_dump()
        }
    )

    return report
```

**LangGraph Checkpoint Deletion Utility:**

```python
# open_notebook/observability/checkpoint_cleanup.py

import sqlite3
from typing import List
from loguru import logger
from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE

def delete_user_checkpoints(user_id: str) -> int:
    """
    Delete all LangGraph conversation checkpoints for a user.

    Thread ID pattern: user:{user_id}:notebook:{notebook_id}

    Args:
        user_id: User record ID (e.g., "user:alice")

    Returns:
        Number of checkpoint threads deleted

    Note:
        Gracefully handles SQLite connection errors (logs warning, returns 0)
    """
    try:
        conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)
        cursor = conn.cursor()

        # LangGraph stores checkpoints in 'checkpoints' table with thread_id column
        # Thread pattern: "user:{user_id}:notebook:{notebook_id}"
        thread_pattern = f"user:{user_id}:%"

        # Query matching threads
        cursor.execute(
            "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?",
            (thread_pattern,)
        )
        threads = cursor.fetchall()
        thread_count = len(threads)

        # Delete matching checkpoints
        cursor.execute(
            "DELETE FROM checkpoints WHERE thread_id LIKE ?",
            (thread_pattern,)
        )

        conn.commit()
        conn.close()

        logger.info(f"Deleted {thread_count} checkpoint threads for user {user_id}")
        return thread_count

    except sqlite3.Error as e:
        logger.warning(f"Failed to delete checkpoints for {user_id}: {e}")
        return 0

def list_user_checkpoint_threads(user_id: str) -> List[str]:
    """
    List all checkpoint thread IDs for a user (for debugging).

    Args:
        user_id: User record ID

    Returns:
        List of thread_id strings
    """
    try:
        conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE)
        cursor = conn.cursor()

        thread_pattern = f"user:{user_id}:%"
        cursor.execute(
            "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?",
            (thread_pattern,)
        )
        threads = [row[0] for row in cursor.fetchall()]

        conn.close()
        return threads

    except sqlite3.Error as e:
        logger.error(f"Failed to list checkpoints for {user_id}: {e}")
        return []
```

**Admin API Endpoint Pattern - User Deletion:**

```python
# api/routers/users.py

from fastapi import APIRouter, Depends, HTTPException
from open_notebook.domain.user_deletion import delete_user_cascade, UserDeletionReport
from api.auth import require_admin
from loguru import logger

router = APIRouter()

@router.delete(
    "/admin/users/{user_id}",
    response_model=UserDeletionReport,
    summary="Delete User (Cascade)",
    description="Delete user and all associated data (GDPR-compliant). Removes progress, checkpoints, artifacts.",
)
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
):
    """
    Delete user and cascade to all related data.

    **Deleted Data:**
    - learner_objective_progress records
    - LangGraph conversation checkpoints (SQLite)
    - User-created quizzes
    - User-created notes
    - Module assignments where user is assigner
    - User record

    **Returns:**
    - 200: UserDeletionReport with counts of deleted records
    - 404: User not found
    - 403: Requires admin privileges
    """
    try:
        report = await delete_user_cascade(user_id)

        logger.info(
            f"User deleted by admin",
            extra={
                "user_id": user_id,
                "admin_id": admin.id,
                "report": report.model_dump()
            }
        )

        return report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Admin API Endpoint Pattern - Company Deletion:**

```python
# api/routers/companies.py

from fastapi import APIRouter, Depends, HTTPException, Query
from open_notebook.domain.company_deletion import (
    get_company_deletion_summary,
    delete_company_cascade,
    CompanyDeletionSummary,
    CompanyDeletionReport,
)
from api.auth import require_admin
from loguru import logger

router = APIRouter()

@router.get(
    "/admin/companies/{company_id}/deletion-summary",
    response_model=CompanyDeletionSummary,
    summary="Preview Company Deletion",
    description="Get counts of data that will be deleted if company is removed (no action taken).",
)
async def preview_company_deletion(
    company_id: str,
    admin: User = Depends(require_admin),
):
    """
    Preview what will be deleted if company is removed.

    **Returns:**
    - 200: CompanyDeletionSummary with counts and affected resources
    - 404: Company not found
    """
    try:
        summary = await get_company_deletion_summary(company_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete(
    "/admin/companies/{company_id}",
    response_model=CompanyDeletionReport,
    summary="Delete Company (Cascade)",
    description="Delete company and ALL associated data (users, assignments). Requires confirmation.",
)
async def delete_company(
    company_id: str,
    confirm: bool = Query(False, description="Must be true to proceed with deletion"),
    admin: User = Depends(require_admin),
):
    """
    Delete company and cascade to all related data.

    **WARNING: This is a destructive operation!**

    **Deleted Data:**
    - All member users (via user cascade for each)
    - All module assignments
    - Company record

    **Query Parameters:**
    - confirm: Must be true to proceed (safety check)

    **Returns:**
    - 200: CompanyDeletionReport with aggregate counts
    - 400: Confirmation required
    - 404: Company not found
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm deletion with ?confirm=true query parameter"
        )

    try:
        report = await delete_company_cascade(company_id)

        logger.warning(
            f"Company deleted by admin",
            extra={
                "company_id": company_id,
                "admin_id": admin.id,
                "report": report.model_dump()
            }
        )

        return report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Project Structure Notes

**New Files Created:**
```
open_notebook/domain/
├── user_deletion.py                # NEW: User cascade deletion service
└── company_deletion.py             # NEW: Company cascade deletion service

open_notebook/observability/
└── checkpoint_cleanup.py           # NEW: LangGraph checkpoint deletion utility

api/models/
└── deletion_models.py              # NEW: Pydantic models for deletion reports (imported by routers)

api/routers/
├── users.py                        # MODIFIED: Add DELETE /admin/users/{user_id} endpoint
└── companies.py                    # MODIFIED: Add DELETE endpoints and preview endpoint
```

**Modified Files:**
```
api/routers/
├── users.py                        # Add DELETE /admin/users/{user_id} endpoint
└── companies.py                    # Add DELETE /admin/companies/{company_id} + preview endpoint
```

**NO CHANGES TO:**
- Database migrations (no new tables needed - using existing data model)
- Frontend (admin-only backend feature)
- LangGraph workflows
- Domain models (User, Company, etc. - no schema changes)

### Data Relationships to Cascade

**Complete Cascade Map (From Explore Agent Analysis):**

```
User Deletion:
user:{user_id}
├── learner_objective_progress (WHERE user_id = $user_id)
│   └── SurrealDB table: learner_objective_progress
├── LangGraph checkpoints (WHERE thread_id LIKE "user:{user_id}:%")
│   └── SQLite DB: /data/sqlite-db/checkpoints.sqlite → checkpoints table
├── Quiz records (WHERE created_by = $user_id)
│   └── SurrealDB table: quiz
├── Note records (WHERE user_id = $user_id)
│   └── SurrealDB table: note
├── Module assignments (WHERE assigned_by = $user_id)
│   └── SurrealDB table: module_assignment
└── User record (DELETE user:{user_id})
    └── SurrealDB table: user

Company Deletion:
company:{company_id}
├── All member users (WHERE company_id = $company_id)
│   ├── User 1 → triggers full user cascade above
│   ├── User 2 → triggers full user cascade above
│   └── User N → triggers full user cascade above
├── Module assignments (WHERE company_id = $company_id)
│   └── SurrealDB table: module_assignment
└── Company record (DELETE company:{company_id})
    └── SurrealDB table: company
```

**Records NOT Deleted (Intentionally):**
- **Notebooks**: Modules remain even if company/users deleted (admin content)
- **Sources**: Source documents remain (admin content)
- **LearningObjective**: Learning objectives remain (admin content)
- **ModulePrompt**: Module prompts remain (admin content)
- **Podcast/Quiz (admin-created)**: Admin-generated artifacts remain

**Why Selective Cascade?**
- User/company data = learner-specific, must be deletable for GDPR
- Module content = admin-created, reusable across companies, preserved

### Error Handling & Edge Cases

**User Deletion Edge Cases:**

1. **User not found**: Return 404 with clear error message
2. **Checkpoint deletion fails**: Log warning, continue with other deletions (non-blocking)
3. **Partial cascade failure**: Log error for specific record type, continue with others
4. **User is last admin**: No check - allow deletion (platform assumes multiple admins exist)

**Company Deletion Edge Cases:**

1. **Company not found**: Return 404 with clear error message
2. **Deletion without confirmation**: Return 400 with error: "Must confirm deletion"
3. **User cascade fails mid-operation**: Log error for failed user, continue with remaining users
4. **Large company (100+ users)**: No timeout - async deletion handles long-running operations

**Audit Logging:**

All deletions trigger structured logs:
- **User deletion**: `logger.warning()` with user_id, admin_id, deletion report
- **Company deletion**: `logger.error()` with company_id, admin_id, deletion report (higher severity)
- Logs include full `UserDeletionReport` / `CompanyDeletionReport` in extra data

### Testing Strategy

**Unit Tests (open_notebook/domain/):**

```python
# tests/test_user_deletion.py

async def test_delete_user_cascade_removes_all_data():
    """User deletion removes progress, checkpoints, artifacts, user record"""

async def test_delete_user_cascade_handles_missing_user():
    """Returns ValueError for non-existent user"""

async def test_delete_user_cascade_report_counts():
    """Deletion report includes accurate record counts"""

async def test_delete_user_cascade_continues_on_checkpoint_failure():
    """Checkpoint deletion failure doesn't block other deletions"""

# tests/test_company_deletion.py

async def test_delete_company_cascade_removes_all_users():
    """Company deletion cascades to all member users"""

async def test_get_company_deletion_summary_returns_accurate_counts():
    """Preview shows correct user/assignment counts"""

async def test_delete_company_cascade_handles_user_failure():
    """Continues deleting other users if one fails"""

# tests/test_checkpoint_cleanup.py

def test_delete_user_checkpoints_removes_matching_threads():
    """Checkpoint deletion removes threads matching pattern"""

def test_delete_user_checkpoints_handles_sqlite_error():
    """Returns 0 on SQLite connection error (graceful failure)"""

def test_list_user_checkpoint_threads_returns_thread_ids():
    """Lists all checkpoint threads for debugging"""
```

**Integration Tests (tests/):**

```python
# tests/test_user_deletion_api.py

async def test_delete_user_endpoint_returns_deletion_report():
    """DELETE /admin/users/{user_id} returns UserDeletionReport"""

async def test_delete_user_endpoint_requires_admin():
    """Returns 403 for non-admin users"""

async def test_delete_user_endpoint_returns_404_for_missing_user():
    """Returns 404 for non-existent user"""

async def test_delete_user_removes_checkpoint_from_sqlite():
    """Verify checkpoint deletion in SQLite DB"""

# tests/test_company_deletion_api.py

async def test_company_deletion_preview_returns_summary():
    """GET /admin/companies/{id}/deletion-summary returns CompanyDeletionSummary"""

async def test_delete_company_requires_confirmation():
    """Returns 400 without ?confirm=true"""

async def test_delete_company_cascades_to_all_users():
    """Verify all member users deleted"""

async def test_delete_company_removes_module_assignments():
    """Verify module_assignment records deleted"""

async def test_delete_company_audit_log_created():
    """Verify structured log entry with ERROR severity"""
```

**Manual Validation:**

1. Create test user with progress records + checkpoints
2. Call `DELETE /admin/users/{user_id}`
3. Verify UserDeletionReport shows correct counts
4. Query SurrealDB: Verify no orphaned learner_objective_progress records
5. Query SQLite: Verify no checkpoint threads remain
6. Create test company with 3 users
7. Call `GET /admin/companies/{id}/deletion-summary`
8. Verify summary shows 3 users, N assignments
9. Call `DELETE /admin/companies/{id}?confirm=true`
10. Verify CompanyDeletionReport shows all 3 users deleted

### Security & Privacy Considerations

**GDPR Compliance:**
- ✅ Right to be forgotten: Complete data removal (no soft delete)
- ✅ Audit trail: Structured logs capture who deleted what and when
- ✅ Confirmation for mass deletion: Company deletion requires explicit confirmation
- ✅ Data portability: User data deleted, not exported (future enhancement)

**Admin Authorization:**
- All deletion endpoints protected by `require_admin()` dependency
- No self-service deletion for learners (admin-initiated only)
- Audit logs include admin user ID for accountability

**Data Isolation:**
- Company deletion removes ALL member users (no cross-company leakage)
- Cascade deletion ensures no orphaned records remain
- Checkpoint deletion uses thread_id pattern matching (guaranteed isolation)

### Performance Considerations

**User Deletion:**
- Single-user deletion: < 1s (typical: 10-50 records)
- Checkpoint deletion: SQLite query + delete (< 100ms)
- No blocking on checkpoint failure (non-critical)

**Company Deletion:**
- Large company (100 users): ~10-30s (10 cascades per user)
- Serial user deletion (no parallelization to avoid race conditions)
- No timeout - async endpoint handles long-running operations

**Database Load:**
- Multiple DELETE queries per cascade (not atomic transaction)
- No locking issues (isolated by user_id/company_id)
- Checkpoint deletion: Single SQLite connection (thread-safe)

### Future Enhancements (Post-MVP)

**Advanced Deletion Features:**
- Data export before deletion (GDPR "right to data portability")
- Soft delete with anonymization (archive instead of destroy)
- Batch deletion UI (select multiple users/companies)
- Deletion scheduling (queue deletions for off-peak hours)

**Audit Improvements:**
- Deletion history table (permanent record of who deleted what)
- Undo deletion (restore from backup)
- Deletion notifications (email admin after large company deletion)

### References

**Epic & Story Context:**
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 7: Error Handling, Observability & Data Privacy]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.6: User & Company Data Deletion]
- FR48: Complete user data deletion support
- FR49: Complete company data deletion support
- NFR7: Learner data isolated per company at application level

**Architecture Requirements:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- User model: user_id, username, email, role, company_id, profile, onboarding_completed
- Company model: company_id, name, slug
- LearnerObjectiveProgress: user_id, objective_id, status, completed_via, evidence
- ModuleAssignment: company_id, notebook_id, is_locked, assigned_by
- TokenUsage: Does NOT exist yet (Story 7.7 - future implementation)

**Existing Patterns:**
- [Source: open_notebook/domain/user.py] - User model with company_id foreign key
- [Source: open_notebook/domain/company.py] - Company model with get_member_count() method
- [Source: api/company_service.py#delete_company] - Existing delete with blocking validation (no cascade)
- [Source: open_notebook/database/migrations/1.surrealql] - Database event for Source cascade (reference pattern)
- [Source: open_notebook/config.py] - LANGGRAPH_CHECKPOINT_FILE path for SQLite checkpoints

**Related Stories:**
- Story 1.2: Role-Based Access Control (RBAC dependencies created)
- Story 2.1: Company Management (Company model, get_member_count method)
- Story 4.8: Persistent Chat History (LangGraph checkpoint patterns, thread_id format)
- Story 7.2: Structured Contextual Error Logging (audit logging patterns)
- Story 7.3: Admin Error Notifications (notification service, structured logging)
- Story 7.5: Per-Company Data Isolation Audit (precondition - verify no cross-company leakage)
- Story 7.7: Token Usage Tracking (future - TokenUsage model cascade, NOT in this story)

**Existing Code Patterns:**
- [Source: open_notebook/database/repository.py#repo_delete] - Simple record deletion (no cascade)
- [Source: open_notebook/domain/base.py#delete] - ObjectModel.delete() method pattern
- [Source: api/routers/sources.py#delete_source] - Admin-only DELETE endpoint pattern
- [Source: tests/test_domain.py] - Unit test structure for domain layer

**Key Learnings from Explore Agents:**
- NO automatic cascade exists except Source → embeddings/insights
- User model has NO deletion validation (GDPR gap)
- Company service blocks deletion if users exist (opposite of required cascade)
- LangGraph checkpoints stored in SQLite with thread_id: `user:{user_id}:notebook:{notebook_id}`
- Checkpoint cleanup requires direct SQLite access (no LangGraph API)
- Module assignments use assigned_by field (user_id) - must be cleaned up on user deletion
- Quiz/Note models have user_id/created_by fields - must be cascaded

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

