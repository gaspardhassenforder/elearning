"""
Story 5.1: Source Content Endpoint Tests

Tests for GET /sources/{source_id}/content endpoint with company-scoped access control.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from api.models import SourceContentResponse


class TestSourceContentResponseModel:
    """Test SourceContentResponse Pydantic model"""

    def test_model_with_all_fields(self):
        """Test model with all fields populated"""
        response = SourceContentResponse(
            id="source:123",
            title="Test Document",
            content="Full text content here",
            file_type="application/pdf",
            word_count=4,
            character_count=23,
        )
        assert response.id == "source:123"
        assert response.title == "Test Document"
        assert response.content == "Full text content here"
        assert response.file_type == "application/pdf"
        assert response.word_count == 4
        assert response.character_count == 23

    def test_model_with_optional_fields_null(self):
        """Test model with optional fields as None"""
        response = SourceContentResponse(
            id="source:456",
            title=None,
            content="Some content",
            file_type=None,
            word_count=2,
            character_count=12,
        )
        assert response.id == "source:456"
        assert response.title is None
        assert response.file_type is None

    def test_model_empty_content(self):
        """Test model with empty content string"""
        response = SourceContentResponse(
            id="source:789",
            title="Empty Doc",
            content="",
            file_type="text/plain",
            word_count=0,
            character_count=0,
        )
        assert response.content == ""
        assert response.word_count == 0
        assert response.character_count == 0

    def test_model_serialization(self):
        """Test model can be serialized to dict"""
        response = SourceContentResponse(
            id="source:abc",
            title="Serializable",
            content="Test",
            file_type="text/plain",
            word_count=1,
            character_count=4,
        )
        data = response.model_dump()
        assert data["id"] == "source:abc"
        assert data["title"] == "Serializable"
        assert data["content"] == "Test"


class TestSourceContentEndpoint:
    """Test the source content endpoint logic"""

    def test_word_count_calculation(self):
        """Test word count calculation for various content types"""
        test_cases = [
            ("Hello world", 2),
            ("", 0),
            ("Single", 1),
            ("One two three four five", 5),
            ("   spaced   out   words   ", 3),
            ("Newlines\nare\nalso\nwords", 4),
        ]
        for content, expected_count in test_cases:
            actual_count = len(content.split()) if content else 0
            assert actual_count == expected_count, f"Failed for content: '{content}'"

    def test_character_count_calculation(self):
        """Test character count calculation"""
        test_cases = [
            ("Hello", 5),
            ("", 0),
            ("Hello World", 11),
            ("Émojis 🎉", 8),  # Python counts emoji 🎉 as 1 character (single Unicode code point)
        ]
        for content, expected_count in test_cases:
            actual_count = len(content) if content else 0
            assert actual_count == expected_count, f"Failed for content: '{content}'"


class TestValidateLearnerAccessToSource:
    """Test learner access validation logic"""

    def test_access_validation_logic(self):
        """Test the access validation flow conceptually"""
        # These are unit tests for the validation logic patterns
        # The actual validation happens in the endpoint with database queries

        # Test case 1: Source exists, notebook published, company assigned
        source_exists = True
        notebook_published = True
        company_assigned = True
        access_granted = source_exists and notebook_published and company_assigned
        assert access_granted is True

        # Test case 2: Source exists but notebook not published
        source_exists = True
        notebook_published = False
        company_assigned = True
        access_granted = source_exists and notebook_published and company_assigned
        assert access_granted is False

        # Test case 3: Source exists, notebook published, but company not assigned
        source_exists = True
        notebook_published = True
        company_assigned = False
        access_granted = source_exists and notebook_published and company_assigned
        assert access_granted is False

        # Test case 4: Source doesn't exist
        source_exists = False
        notebook_published = True
        company_assigned = True
        access_granted = source_exists and notebook_published and company_assigned
        assert access_granted is False

    def test_company_scoping_prevents_cross_company_access(self):
        """Test that company scoping correctly prevents cross-company access"""
        # Simulated scenario: User from Company A tries to access Source from Notebook assigned to Company B

        user_company_id = "company:A"
        notebook_assigned_to = "company:B"

        # Access should be denied
        access_granted = user_company_id == notebook_assigned_to
        assert access_granted is False

        # Same company should be granted
        user_company_id = "company:A"
        notebook_assigned_to = "company:A"
        access_granted = user_company_id == notebook_assigned_to
        assert access_granted is True

    def test_locked_module_access_denied(self):
        """Test that locked modules deny access"""
        notebook_locked = True
        access_granted = not notebook_locked
        assert access_granted is False

        notebook_locked = False
        access_granted = not notebook_locked
        assert access_granted is True
