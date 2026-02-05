"""
Tests for assignment service functions.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set JWT secret for tests before importing modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from fastapi import HTTPException

from api.assignment_service import (
    assign_module,
    unassign_module,
    list_assignments,
    get_assignment_matrix,
    toggle_assignment,
)


class TestAssignModule:
    """Test module assignment."""

    @pytest.mark.asyncio
    async def test_assign_module_success(self):
        """Module assignment should succeed with valid company and notebook."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Test Company"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"
        mock_notebook.name = "Test Notebook"
        mock_notebook.published = True

        mock_assignment = MagicMock()
        mock_assignment.id = "module_assignment:abc"
        mock_assignment.company_id = "company:test123"
        mock_assignment.notebook_id = "notebook:test456"
        mock_assignment.is_locked = False
        mock_assignment.assigned_at = "2024-01-01T00:00:00"
        mock_assignment.assigned_by = "user:admin"
        mock_assignment.save = AsyncMock()

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.get_by_company_and_notebook = AsyncMock(return_value=None)
            MockAssignment.return_value = mock_assignment

            assignment, warning = await assign_module(
                company_id="company:test123",
                notebook_id="notebook:test456",
                assigned_by="user:admin",
            )

            assert assignment.company_id == "company:test123"
            assert assignment.notebook_id == "notebook:test456"
            assert warning is None  # Published module has no warning
            mock_assignment.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_module_unpublished_warning(self):
        """Module assignment to unpublished notebook should return warning."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"
        mock_notebook.published = False  # Unpublished

        mock_assignment = MagicMock()
        mock_assignment.id = "module_assignment:abc"
        mock_assignment.company_id = "company:test123"
        mock_assignment.notebook_id = "notebook:test456"
        mock_assignment.is_locked = False
        mock_assignment.save = AsyncMock()

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.get_by_company_and_notebook = AsyncMock(return_value=None)
            MockAssignment.return_value = mock_assignment

            assignment, warning = await assign_module(
                company_id="company:test123",
                notebook_id="notebook:test456",
            )

            assert warning is not None
            assert "not published" in warning

    @pytest.mark.asyncio
    async def test_assign_module_already_exists(self):
        """Module assignment should return existing assignment if already assigned."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"
        mock_notebook.published = True

        mock_existing_assignment = MagicMock()
        mock_existing_assignment.id = "module_assignment:existing"
        mock_existing_assignment.company_id = "company:test123"
        mock_existing_assignment.notebook_id = "notebook:test456"
        mock_existing_assignment.is_locked = False

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.get_by_company_and_notebook = AsyncMock(
                return_value=mock_existing_assignment
            )

            assignment, warning = await assign_module(
                company_id="company:test123",
                notebook_id="notebook:test456",
            )

            # Should return existing, not create new
            assert assignment.id == "module_assignment:existing"

    @pytest.mark.asyncio
    async def test_assign_module_company_not_found(self):
        """Module assignment should fail if company not found."""
        with patch("api.assignment_service.Company") as MockCompany:
            MockCompany.get = AsyncMock(side_effect=Exception("Not found"))

            with pytest.raises(HTTPException) as exc_info:
                await assign_module(
                    company_id="company:nonexistent",
                    notebook_id="notebook:test456",
                )
            assert exc_info.value.status_code == 404
            assert "Company not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_assign_module_notebook_not_found(self):
        """Module assignment should fail if notebook not found."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(side_effect=Exception("Not found"))

            with pytest.raises(HTTPException) as exc_info:
                await assign_module(
                    company_id="company:test123",
                    notebook_id="notebook:nonexistent",
                )
            assert exc_info.value.status_code == 404
            assert "Module not found" in exc_info.value.detail


class TestUnassignModule:
    """Test module unassignment."""

    @pytest.mark.asyncio
    async def test_unassign_module_success(self):
        """Module unassignment should succeed when assignment exists."""
        mock_assignment = MagicMock()
        mock_assignment.id = "module_assignment:existing"

        with patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockAssignment.get_by_company_and_notebook = AsyncMock(
                return_value=mock_assignment
            )
            MockAssignment.delete_assignment = AsyncMock(return_value=True)

            result = await unassign_module(
                company_id="company:test123",
                notebook_id="notebook:test456",
            )

            assert result is True
            MockAssignment.delete_assignment.assert_called_once()

    @pytest.mark.asyncio
    async def test_unassign_module_not_found(self):
        """Module unassignment should fail if assignment not found."""
        with patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockAssignment.get_by_company_and_notebook = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await unassign_module(
                    company_id="company:test123",
                    notebook_id="notebook:nonexistent",
                )
            assert exc_info.value.status_code == 404
            assert "Assignment not found" in exc_info.value.detail


class TestListAssignments:
    """Test listing assignments."""

    @pytest.mark.asyncio
    async def test_list_assignments_success(self):
        """List assignments should return all assignments."""
        mock_assignment1 = MagicMock()
        mock_assignment1.id = "module_assignment:1"
        mock_assignment1.company_id = "company:1"
        mock_assignment1.notebook_id = "notebook:1"

        mock_assignment2 = MagicMock()
        mock_assignment2.id = "module_assignment:2"
        mock_assignment2.company_id = "company:2"
        mock_assignment2.notebook_id = "notebook:1"

        with patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockAssignment.get_all_assignments = AsyncMock(
                return_value=[mock_assignment1, mock_assignment2]
            )

            assignments = await list_assignments()

            assert len(assignments) == 2
            assert assignments[0].company_id == "company:1"
            assert assignments[1].company_id == "company:2"


class TestGetAssignmentMatrix:
    """Test assignment matrix generation."""

    @pytest.mark.asyncio
    async def test_get_assignment_matrix_success(self):
        """Assignment matrix should contain companies, notebooks, and assignment status."""
        mock_company1 = MagicMock()
        mock_company1.id = "company:1"
        mock_company1.name = "Company 1"
        mock_company1.slug = "company-1"

        mock_company2 = MagicMock()
        mock_company2.id = "company:2"
        mock_company2.name = "Company 2"
        mock_company2.slug = "company-2"

        mock_notebook1 = MagicMock()
        mock_notebook1.id = "notebook:1"
        mock_notebook1.name = "Notebook 1"
        mock_notebook1.published = True

        mock_notebook2 = MagicMock()
        mock_notebook2.id = "notebook:2"
        mock_notebook2.name = "Notebook 2"
        mock_notebook2.published = False

        mock_assignment = MagicMock()
        mock_assignment.id = "module_assignment:1"
        mock_assignment.company_id = "company:1"
        mock_assignment.notebook_id = "notebook:1"
        mock_assignment.is_locked = False

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get_all = AsyncMock(return_value=[mock_company1, mock_company2])
            MockNotebook.get_all = AsyncMock(return_value=[mock_notebook1, mock_notebook2])
            MockAssignment.get_all_assignments = AsyncMock(return_value=[mock_assignment])

            matrix = await get_assignment_matrix()

            assert len(matrix["companies"]) == 2
            assert len(matrix["notebooks"]) == 2

            # Check company 1 has assignment to notebook 1
            assert matrix["assignments"]["company:1"]["notebook:1"]["is_assigned"] is True
            assert matrix["assignments"]["company:1"]["notebook:2"]["is_assigned"] is False

            # Check company 2 has no assignments
            assert matrix["assignments"]["company:2"]["notebook:1"]["is_assigned"] is False
            assert matrix["assignments"]["company:2"]["notebook:2"]["is_assigned"] is False

            # Check notebook published status
            notebook1_summary = next(n for n in matrix["notebooks"] if n["id"] == "notebook:1")
            notebook2_summary = next(n for n in matrix["notebooks"] if n["id"] == "notebook:2")
            assert notebook1_summary["published"] is True
            assert notebook2_summary["published"] is False


class TestToggleAssignment:
    """Test toggle assignment functionality."""

    @pytest.mark.asyncio
    async def test_toggle_assignment_creates_when_not_exists(self):
        """Toggle should create assignment when it doesn't exist."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"
        mock_notebook.published = True

        mock_new_assignment = MagicMock()
        mock_new_assignment.id = "module_assignment:new"
        mock_new_assignment.company_id = "company:test123"
        mock_new_assignment.notebook_id = "notebook:test456"
        mock_new_assignment.is_locked = False
        mock_new_assignment.save = AsyncMock()

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.get_by_company_and_notebook = AsyncMock(return_value=None)
            MockAssignment.return_value = mock_new_assignment

            result = await toggle_assignment(
                company_id="company:test123",
                notebook_id="notebook:test456",
                assigned_by="user:admin",
            )

            assert result["action"] == "assigned"
            assert result["company_id"] == "company:test123"
            assert result["notebook_id"] == "notebook:test456"

    @pytest.mark.asyncio
    async def test_toggle_assignment_deletes_when_exists(self):
        """Toggle should delete assignment when it exists."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"

        mock_existing_assignment = MagicMock()
        mock_existing_assignment.id = "module_assignment:existing"
        mock_existing_assignment.company_id = "company:test123"
        mock_existing_assignment.notebook_id = "notebook:test456"

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.get_by_company_and_notebook = AsyncMock(
                return_value=mock_existing_assignment
            )
            MockAssignment.delete_assignment = AsyncMock(return_value=True)

            result = await toggle_assignment(
                company_id="company:test123",
                notebook_id="notebook:test456",
            )

            assert result["action"] == "unassigned"
            assert result["company_id"] == "company:test123"
            assert result["notebook_id"] == "notebook:test456"
            MockAssignment.delete_assignment.assert_called_once()


class TestToggleModuleLock:
    """Test module lock toggle functionality (Story 2.3)."""

    @pytest.mark.asyncio
    async def test_toggle_module_lock_success(self):
        """Toggle lock should update assignment lock status."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"
        mock_notebook.published = True

        mock_assignment = MagicMock()
        mock_assignment.id = "module_assignment:existing"
        mock_assignment.company_id = "company:test123"
        mock_assignment.notebook_id = "notebook:test456"
        mock_assignment.is_locked = True

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.toggle_lock = AsyncMock(return_value=mock_assignment)

            from api.assignment_service import toggle_module_lock
            assignment, warning = await toggle_module_lock(
                company_id="company:test123",
                notebook_id="notebook:test456",
                is_locked=True,
                toggled_by="user:admin",
            )

            assert assignment.is_locked is True
            assert warning is None  # Published module has no warning
            MockAssignment.toggle_lock.assert_called_once_with(
                "company:test123", "notebook:test456", True
            )

    @pytest.mark.asyncio
    async def test_toggle_module_lock_idempotency(self):
        """Toggle lock multiple times with same value should be idempotent."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"
        mock_notebook.published = True

        mock_assignment = MagicMock()
        mock_assignment.id = "module_assignment:existing"
        mock_assignment.is_locked = True

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.toggle_lock = AsyncMock(return_value=mock_assignment)

            from api.assignment_service import toggle_module_lock

            # First lock
            assignment1, _ = await toggle_module_lock(
                "company:test123", "notebook:test456", True
            )
            assert assignment1.is_locked is True

            # Lock again (idempotent)
            assignment2, _ = await toggle_module_lock(
                "company:test123", "notebook:test456", True
            )
            assert assignment2.is_locked is True

            # Should call toggle_lock twice with same arguments
            assert MockAssignment.toggle_lock.call_count == 2

    @pytest.mark.asyncio
    async def test_toggle_module_lock_assignment_not_found(self):
        """Toggle lock should fail with 404 if assignment doesn't exist."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test456"

        with patch("api.assignment_service.Company") as MockCompany, \
             patch("api.assignment_service.Notebook") as MockNotebook, \
             patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockCompany.get = AsyncMock(return_value=mock_company)
            MockNotebook.get = AsyncMock(return_value=mock_notebook)
            MockAssignment.toggle_lock = AsyncMock(return_value=None)

            from api.assignment_service import toggle_module_lock

            with pytest.raises(HTTPException) as exc_info:
                await toggle_module_lock(
                    "company:test123", "notebook:nonexistent", True
                )
            assert exc_info.value.status_code == 404
            assert "Assignment not found" in exc_info.value.detail


class TestGetLearnerModules:
    """Test learner module visibility (Story 2.3)."""

    @pytest.mark.asyncio
    async def test_get_learner_modules_filters_locked(self):
        """Learners should only see unlocked modules."""
        # Mock unlocked assignment with published notebook
        mock_assignment = MagicMock()
        mock_assignment.notebook_id = "notebook:unlocked"
        mock_assignment.is_locked = False
        mock_assignment.assigned_at = "2024-01-01T00:00:00"
        mock_assignment.notebook_data = {
            "id": "notebook:unlocked",
            "name": "Unlocked Module",
            "description": "This is unlocked",
            "published": True,
            "source_count": 5,
        }

        with patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockAssignment.get_unlocked_for_company = AsyncMock(
                return_value=[mock_assignment]
            )

            from api.assignment_service import get_learner_modules
            modules = await get_learner_modules("company:test123")

            assert len(modules) == 1
            # modules is a list of LearnerModuleResponse objects, not dicts
            assert modules[0].id == "notebook:unlocked"
            assert modules[0].is_locked is False

    @pytest.mark.asyncio
    async def test_get_learner_modules_filters_unpublished(self):
        """Learners should NOT see unpublished modules (Story 3.5 prep)."""
        # Mock assignments: one published, one unpublished
        mock_published = MagicMock()
        mock_published.notebook_id = "notebook:published"
        mock_published.is_locked = False
        mock_published.assigned_at = "2024-01-01T00:00:00"
        mock_published.notebook_data = {
            "name": "Published Module",
            "description": None,
            "published": True,
            "source_count": 3,
        }

        mock_unpublished = MagicMock()
        mock_unpublished.notebook_id = "notebook:unpublished"
        mock_unpublished.is_locked = False
        mock_unpublished.assigned_at = "2024-01-02T00:00:00"
        mock_unpublished.notebook_data = {
            "name": "Unpublished Module",
            "description": None,
            "published": False,  # Not published
            "source_count": 2,
        }

        with patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockAssignment.get_unlocked_for_company = AsyncMock(
                return_value=[mock_published, mock_unpublished]
            )

            from api.assignment_service import get_learner_modules
            modules = await get_learner_modules("company:test123")

            # Should only return published module
            assert len(modules) == 1
            # modules is a list of LearnerModuleResponse objects, not dicts
            assert modules[0].id == "notebook:published"

    @pytest.mark.asyncio
    async def test_get_learner_modules_company_scoping(self):
        """Learner modules should be scoped to learner's company."""
        # This test validates that the correct company_id is passed to domain layer
        with patch("api.assignment_service.ModuleAssignment") as MockAssignment:
            MockAssignment.get_unlocked_for_company = AsyncMock(return_value=[])

            from api.assignment_service import get_learner_modules
            await get_learner_modules("company:specific")

            # Verify domain method called with correct company_id
            MockAssignment.get_unlocked_for_company.assert_called_once_with(
                "company:specific"
            )


class TestDirectModuleAccess:
    """Test direct URL access protection for learners (Story 2.3)."""

    @pytest.mark.asyncio
    async def test_direct_access_locked_module_403(self):
        """Learner accessing locked module directly should get 403."""
        mock_assignment = MagicMock()
        mock_assignment.is_locked = True

        # Patch at the import site in the learner router
        with patch("api.routers.learner.ModuleAssignment") as MockAssignment:
            MockAssignment.get_by_company_and_notebook = AsyncMock(
                return_value=mock_assignment
            )

            from api.routers.learner import get_learner_module
            from api.auth import LearnerContext
            from open_notebook.domain.user import User

            # User model requires password_hash field
            mock_user = User(
                username="learner",
                email="learner@test.com",
                role="learner",
                password_hash="fake_hash"
            )
            mock_user.id = "user:learner"
            learner_context = LearnerContext(user=mock_user, company_id="company:test123")

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_module("notebook:locked", learner_context)

            assert exc_info.value.status_code == 403
            assert "locked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_direct_access_unassigned_module_403(self):
        """Learner accessing unassigned module should get 403."""
        # Patch at the import site in the learner router
        with patch("api.routers.learner.ModuleAssignment") as MockAssignment:
            MockAssignment.get_by_company_and_notebook = AsyncMock(return_value=None)

            from api.routers.learner import get_learner_module
            from api.auth import LearnerContext
            from open_notebook.domain.user import User

            # User model requires password_hash field
            mock_user = User(
                username="learner",
                email="learner@test.com",
                role="learner",
                password_hash="fake_hash"
            )
            mock_user.id = "user:learner"
            learner_context = LearnerContext(user=mock_user, company_id="company:test123")

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_module("notebook:unassigned", learner_context)

            assert exc_info.value.status_code == 403
            assert "not accessible" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_direct_access_valid_module_success(self):
        """Learner accessing unlocked assigned module should succeed."""
        mock_assignment = MagicMock()
        mock_assignment.is_locked = False  # Explicitly set to False
        mock_assignment.assigned_at = "2024-01-01T00:00:00"

        mock_notebook = MagicMock()
        mock_notebook.name = "Test Module"
        mock_notebook.description = "Test Description"
        mock_notebook.sources = ["source:1", "source:2"]
        mock_notebook.published = True  # Published module

        # Patch at the import site in the learner router
        with patch("api.routers.learner.ModuleAssignment") as MockAssignment, \
             patch("api.routers.learner.Notebook") as MockNotebook:
            MockAssignment.get_by_company_and_notebook = AsyncMock(
                return_value=mock_assignment
            )
            MockNotebook.get = AsyncMock(return_value=mock_notebook)

            from api.routers.learner import get_learner_module
            from api.auth import LearnerContext
            from open_notebook.domain.user import User

            # User model requires password_hash field
            mock_user = User(
                username="learner",
                email="learner@test.com",
                role="learner",
                password_hash="fake_hash"
            )
            mock_user.id = "user:learner"
            learner_context = LearnerContext(user=mock_user, company_id="company:test123")

            result = await get_learner_module("notebook:valid", learner_context)

            assert result.id == "notebook:valid"
            assert result.name == "Test Module"
            assert result.is_locked is False
            assert result.source_count == 2

    @pytest.mark.asyncio
    async def test_direct_access_unpublished_module_403(self):
        """Learner accessing unpublished module should get 403."""
        mock_assignment = MagicMock()
        mock_assignment.is_locked = False
        mock_assignment.assigned_at = "2024-01-01T00:00:00"

        mock_notebook = MagicMock()
        mock_notebook.name = "Unpublished Module"
        mock_notebook.description = "Not published yet"
        mock_notebook.sources = ["source:1"]
        mock_notebook.published = False  # NOT published

        # Patch at the import site in the learner router
        with patch("api.routers.learner.ModuleAssignment") as MockAssignment, \
             patch("api.routers.learner.Notebook") as MockNotebook:
            MockAssignment.get_by_company_and_notebook = AsyncMock(
                return_value=mock_assignment
            )
            MockNotebook.get = AsyncMock(return_value=mock_notebook)

            from api.routers.learner import get_learner_module
            from api.auth import LearnerContext
            from open_notebook.domain.user import User

            # User model requires password_hash field
            mock_user = User(
                username="learner",
                email="learner@test.com",
                role="learner",
                password_hash="fake_hash"
            )
            mock_user.id = "user:learner"
            learner_context = LearnerContext(user=mock_user, company_id="company:test123")

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_module("notebook:unpublished", learner_context)

            assert exc_info.value.status_code == 403
            assert "not accessible" in exc_info.value.detail.lower()
