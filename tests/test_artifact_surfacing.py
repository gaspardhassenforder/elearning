"""Tests for artifact surfacing tools (Story 4.6)."""

import pytest
from open_notebook.domain.quiz import Quiz, QuizQuestion
from open_notebook.domain.podcast import Podcast
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.user import User
from open_notebook.domain.company import Company
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.graphs.tools import surface_quiz, surface_podcast


@pytest.mark.asyncio
class TestSurfaceQuizTool:
    """Tests for surface_quiz tool."""

    async def test_surface_quiz_valid(self):
        """Test surface_quiz returns quiz preview with questions."""
        # Create test notebook
        notebook = Notebook(name="Test Notebook", description="Test")
        await notebook.save()

        # Create quiz with questions
        questions = [
            QuizQuestion(
                question="What is supervised learning?",
                options=["Uses labeled datasets", "Uses unlabeled datasets", "No training data"],
                correct_answer=0,
                explanation="Correct! Supervised learning uses labeled data."
            ),
            QuizQuestion(
                question="What is a neural network?",
                options=["A graph structure", "A decision tree", "A clustering algorithm"],
                correct_answer=0,
                explanation="Neural networks are graph structures."
            ),
        ]

        quiz = Quiz(
            notebook_id=notebook.id,
            title="ML Basics Quiz",
            description="Test your knowledge",
            questions=questions,
            created_by="admin"
        )
        await quiz.save()

        # Invoke tool without user context (admin use case)
        result = await surface_quiz.ainvoke({"quiz_id": quiz.id})

        # Assertions
        assert result["artifact_type"] == "quiz"
        assert result["quiz_id"] == quiz.id
        assert result["title"] == "ML Basics Quiz"
        assert result["description"] == "Test your knowledge"
        assert len(result["questions"]) == 1  # Only first question
        assert result["total_questions"] == 2  # But total count is 2
        assert result["quiz_url"] == f"/quizzes/{quiz.id}"

        # Verify correct_answer is NOT included (security)
        assert "correct_answer" not in result["questions"][0]
        assert result["questions"][0]["text"] == "What is supervised learning?"
        assert len(result["questions"][0]["options"]) == 3

    async def test_surface_quiz_company_scoping(self):
        """Test surface_quiz with valid company assignment."""
        # Note: Full company scoping validation is enforced at API layer
        # This test verifies the tool works with valid company context

        # Create company
        company = Company(name="Company A", slug="company-a")
        await company.save()

        # Create notebook assigned to company
        notebook = Notebook(name="Notebook A", description="For Company A", published=True)
        await notebook.save()

        assignment = ModuleAssignment(
            notebook_id=notebook.id,
            company_id=company.id,
            is_locked=False
        )
        await assignment.save()

        # Create quiz for notebook
        quiz = Quiz(
            notebook_id=notebook.id,
            title="Quiz A",
            questions=[
                QuizQuestion(
                    question="Test question",
                    options=["A", "B"],
                    correct_answer=0
                )
            ]
        )
        await quiz.save()

        # Create learner from same company
        learner = User(
            username="learner_a",
            email="learner_a@company-a.com",
            password_hash="hashed_password",
            role="learner",
            company_id=company.id
        )
        await learner.save()

        # Surface quiz with valid learner context
        config = {"configurable": {"user_id": learner.id}}
        result = await surface_quiz.ainvoke({"quiz_id": quiz.id, "config": config})

        # Should successfully return quiz data (company scoping passes)
        assert result["artifact_type"] == "quiz"
        assert result["quiz_id"] == quiz.id
        assert result["title"] == "Quiz A"

    async def test_surface_quiz_not_found(self):
        """Test surface_quiz handles invalid quiz_id gracefully."""
        # Invoke tool with non-existent quiz_id
        result = await surface_quiz.ainvoke({"quiz_id": "quiz:nonexistent"})

        # Should return error
        assert "error" in result
        assert result["error"] == "Quiz not found"
        assert result["quiz_id"] == "quiz:nonexistent"


@pytest.mark.asyncio
class TestSurfacePodcastTool:
    """Tests for surface_podcast tool."""

    async def test_surface_podcast_valid(self):
        """Test surface_podcast returns podcast metadata with audio URL."""
        # Create test notebook
        notebook = Notebook(name="Test Notebook", description="Test")
        await notebook.save()

        # Create completed podcast
        podcast = Podcast(
            notebook_id=notebook.id,
            title="ML Fundamentals",
            topic="Introduction to ML",
            length="medium",
            speaker_format="multi",
            audio_file_path="/data/podcasts/test.mp3",
            transcript="This is the transcript...",
            status="completed",
            created_by="admin"
        )
        await podcast.save()

        # Invoke tool
        result = await surface_podcast.ainvoke({"podcast_id": podcast.id})

        # Assertions
        assert result["artifact_type"] == "podcast"
        assert result["podcast_id"] == podcast.id
        assert result["title"] == "ML Fundamentals"
        assert result["audio_url"] == f"/api/podcasts/{podcast.id}/audio"
        assert result["duration_minutes"] == 7  # medium = 7 minutes
        assert result["transcript_url"] == f"/api/podcasts/{podcast.id}/transcript"
        assert result["status"] == "completed"

    async def test_surface_podcast_not_ready(self):
        """Test surface_podcast handles generating podcast gracefully."""
        # Create test notebook
        notebook = Notebook(name="Test Notebook", description="Test")
        await notebook.save()

        # Create podcast still generating
        podcast = Podcast(
            notebook_id=notebook.id,
            title="Generating Podcast",
            status="generating",  # Not completed
            audio_file_path=None,  # No audio yet
        )
        await podcast.save()

        # Invoke tool
        result = await surface_podcast.ainvoke({"podcast_id": podcast.id})

        # Should return status with error
        assert result["artifact_type"] == "podcast"
        assert result["status"] == "generating"
        assert "error" in result
        assert result["error"] == "Podcast not ready"

    async def test_surface_podcast_company_scoping(self):
        """Test surface_podcast with valid company assignment."""
        # Note: Full company scoping validation is enforced at API layer
        # This test verifies the tool works with valid company context

        # Create company
        company = Company(name="Company A", slug="company-a")
        await company.save()

        # Create notebook assigned to company
        notebook = Notebook(name="Notebook A", description="For Company A", published=True)
        await notebook.save()

        assignment = ModuleAssignment(
            notebook_id=notebook.id,
            company_id=company.id,
            is_locked=False
        )
        await assignment.save()

        # Create podcast for notebook
        podcast = Podcast(
            notebook_id=notebook.id,
            title="Podcast A",
            audio_file_path="/data/test.mp3",
            status="completed"
        )
        await podcast.save()

        # Create learner from same company
        learner = User(
            username="learner_a",
            email="learner_a@company-a.com",
            password_hash="hashed_password",
            role="learner",
            company_id=company.id
        )
        await learner.save()

        # Surface podcast with valid learner context
        config = {"configurable": {"user_id": learner.id}}
        result = await surface_podcast.ainvoke({"podcast_id": podcast.id, "config": config})

        # Should successfully return podcast data (company scoping passes)
        assert result["artifact_type"] == "podcast"
        assert result["podcast_id"] == podcast.id
        assert result["title"] == "Podcast A"

    async def test_surface_podcast_not_found(self):
        """Test surface_podcast handles invalid podcast_id gracefully."""
        # Invoke tool with non-existent podcast_id
        result = await surface_podcast.ainvoke({"podcast_id": "podcast:nonexistent"})

        # Should return error
        assert "error" in result
        assert result["error"] == "Podcast not found"
