"""
Integration tests for note creation and notebook association.

This test suite verifies the complete flow of:
1. Creating a note
2. Saving it to the database
3. Adding it to a notebook via the Artifact tracking system
4. Retrieving notes from a notebook
"""

import os
import pytest
from unittest.mock import patch, AsyncMock

from open_notebook.domain.notebook import Note, Notebook
from open_notebook.domain.artifact import Artifact
from open_notebook.exceptions import InvalidInputError


# Set up test environment variables
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestNoteCreationFlow:
    """Test suite for the complete note creation and association flow."""

    @pytest.mark.asyncio
    async def test_note_validation(self):
        """Test note validation before database operations."""
        # Valid note should create without errors
        note = Note(title="Test Note", content="Test content", note_type="human")
        assert note.title == "Test Note"
        assert note.content == "Test content"
        assert note.note_type == "human"

        # Empty content should fail
        with pytest.raises(InvalidInputError, match="Note content cannot be empty"):
            Note(title="Test", content="")

        # Whitespace content should fail
        with pytest.raises(InvalidInputError, match="Note content cannot be empty"):
            Note(title="Test", content="   ")

    @pytest.mark.asyncio
    async def test_note_save_mock(self):
        """Test note save with mocked database."""
        note = Note(title="Test Note", content="Test content", note_type="human")
        
        # Mock the repo_create function to return a proper dict response
        with patch("open_notebook.domain.base.repo_create") as mock_create:
            mock_create.return_value = {
                "id": "note:test123",
                "title": "Test Note",
                "content": "Test content",
                "note_type": "human",
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z",
            }
            
            await note.save()
            
            # Verify the note got an ID
            assert note.id == "note:test123"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_note_add_to_notebook_validation(self):
        """Test validation when adding note to notebook."""
        note = Note(title="Test Note", content="Test content")
        
        # Should fail without notebook_id
        with pytest.raises(InvalidInputError, match="Notebook ID must be provided"):
            await note.add_to_notebook("")

        # Should fail if note not saved (no ID)
        with pytest.raises(InvalidInputError, match="Note must be saved before adding to notebook"):
            await note.add_to_notebook("notebook:123")

    @pytest.mark.asyncio
    async def test_artifact_creation_flow(self):
        """Test the complete artifact creation flow."""
        # Create a note with an ID (simulating it was saved)
        note = Note(
            id="note:test123",
            title="Test Note",
            content="Test content",
            note_type="human"
        )
        
        # Mock the Artifact.create_for_artifact method
        with patch("open_notebook.domain.artifact.Artifact.create_for_artifact") as mock_create:
            mock_artifact = Artifact(
                id="artifact:art123",
                notebook_id="notebook:nb123",
                artifact_type="note",
                artifact_id="note:test123",
                title="Test Note"
            )
            mock_create.return_value = mock_artifact
            
            # Add note to notebook
            result = await note.add_to_notebook("notebook:nb123")
            
            # Verify Artifact.create_for_artifact was called correctly
            mock_create.assert_called_once_with(
                notebook_id="notebook:nb123",
                artifact_type="note",
                artifact_id="note:test123",
                title="Test Note",
            )
            assert result == mock_artifact

    @pytest.mark.asyncio
    async def test_artifact_save_data_structure(self):
        """Test that Artifact prepares correct data for saving."""
        artifact = Artifact(
            notebook_id="notebook:nb123",
            artifact_type="note",
            artifact_id="note:test123",
            title="Test Note"
        )
        
        # Get the data that would be saved
        save_data = artifact._prepare_save_data()
        
        # Verify all required fields are present
        # notebook_id is converted to RecordID by record_id_fields mechanism
        from surrealdb import RecordID
        assert isinstance(save_data["notebook_id"], RecordID)
        assert str(save_data["notebook_id"]) == "notebook:nb123"
        assert save_data["artifact_type"] == "note"
        assert save_data["artifact_id"] == "note:test123"
        assert save_data["title"] == "Test Note"
        
        # id should not be in save data (it's set by database)
        assert "id" not in save_data

    @pytest.mark.asyncio
    async def test_notebook_get_notes_query(self):
        """Test notebook.get_notes() query structure."""
        notebook = Notebook(
            id="notebook:nb123",
            name="Test Notebook",
            description="Test"
        )
        
        # Mock repo_query to return artifact records
        with patch("open_notebook.domain.notebook.repo_query") as mock_query, \
             patch("open_notebook.domain.notebook.Note.get") as mock_note_get:
            
            # Mock artifact query result
            mock_query.return_value = [
                {
                    "artifact_id": "note:note1",
                    "updated": "2024-01-01T00:00:00Z"
                },
                {
                    "artifact_id": "note:note2",
                    "updated": "2024-01-02T00:00:00Z"
                }
            ]
            
            # Mock Note.get to return notes
            mock_note1 = Note(id="note:note1", title="Note 1", content="Content 1")
            mock_note2 = Note(id="note:note2", title="Note 2", content="Content 2")
            mock_note_get.side_effect = [mock_note1, mock_note2]
            
            # Get notes
            notes = await notebook.get_notes()
            
            # Verify results
            assert len(notes) == 2
            assert notes[0].id == "note:note1"
            assert notes[1].id == "note:note2"
            
            # Verify query was called with correct parameters
            assert mock_query.called
            call_args = mock_query.call_args
            query = call_args[0][0]
            
            # Verify query structure
            assert "SELECT artifact_id, updated FROM artifact" in query
            assert "WHERE notebook_id = $notebook_id" in query
            assert "AND artifact_type = 'note'" in query
            assert "ORDER BY updated DESC" in query

    @pytest.mark.asyncio
    async def test_complete_note_creation_flow_mock(self):
        """Test the complete flow from API perspective (mocked)."""
        # Simulate API request data
        notebook_id = "notebook:nb123"
        note_title = "My Note"
        note_content = "This is my note content"
        note_type = "human"
        
        # Step 1: Create note
        note = Note(title=note_title, content=note_content, note_type=note_type)
        
        # Step 2: Mock save
        with patch("open_notebook.domain.base.repo_create") as mock_create:
            mock_create.return_value = {
                "id": "note:saved123",
                "title": note_title,
                "content": note_content,
                "note_type": note_type,
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z",
            }
            
            await note.save()
            assert note.id == "note:saved123"
        
        # Step 3: Mock notebook retrieval
        with patch("open_notebook.domain.notebook.Notebook.get") as mock_notebook_get:
            mock_notebook = Notebook(
                id=notebook_id,
                name="Test Notebook",
                description="Test"
            )
            mock_notebook_get.return_value = mock_notebook
            
            # Step 4: Mock artifact creation
            with patch("open_notebook.domain.artifact.Artifact.create_for_artifact") as mock_artifact:
                mock_artifact_result = Artifact(
                    id="artifact:art123",
                    notebook_id=notebook_id,
                    artifact_type="note",
                    artifact_id=note.id,
                    title=note.title
                )
                mock_artifact.return_value = mock_artifact_result
                
                # Add to notebook
                await note.add_to_notebook(notebook_id)
                
                # Verify artifact was created correctly
                mock_artifact.assert_called_once_with(
                    notebook_id=notebook_id,
                    artifact_type="note",
                    artifact_id="note:saved123",
                    title=note_title,
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
