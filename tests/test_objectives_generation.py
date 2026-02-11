"""
Tests for learning objectives generation workflow.

Covers the 3-node per-source/per-artifact architecture:
- Per-content analysis with cache hit/miss
- Artifact content extraction (quiz → text)
- Aggregation with provenance (source_refs populated)
- Save with source_refs
- record_id_fields save pattern
- ContentAnalysis domain model
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from open_notebook.graphs.learning_objectives_generation import (
    analyze_all_content,
    aggregate_objectives,
    save_objectives,
    _analyze_single_content,
    _extract_quiz_text,
    _strip_code_fences,
    ObjectiveGenerationState,
    ContentAnalysisOutput,
    AggregatedObjective,
    AggregatedObjectives,
)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


def _make_state(**overrides) -> ObjectiveGenerationState:
    """Build a default ObjectiveGenerationState with optional overrides."""
    defaults: ObjectiveGenerationState = {
        "notebook_id": "notebook:test1",
        "num_objectives": 4,
        "content_analyses": [],
        "generated_objectives": [],
        "objective_ids": [],
        "error": None,
        "status": "pending",
    }
    defaults.update(overrides)
    return defaults


class TestStripCodeFences:
    """Test the _strip_code_fences helper."""

    def test_no_fences(self):
        assert _strip_code_fences('{"key": "value"}') == '{"key": "value"}'

    def test_json_fences(self):
        assert _strip_code_fences('```json\n{"key": "value"}\n```') == '{"key": "value"}'

    def test_plain_fences(self):
        assert _strip_code_fences('```\n{"key": "value"}\n```') == '{"key": "value"}'


class TestExtractQuizText:
    """Test _extract_quiz_text helper."""

    def test_basic_extraction(self):
        mock_quiz = MagicMock()
        q1 = MagicMock()
        q1.question = "What is Python?"
        q1.options = ["Language", "Snake", "Framework"]
        q1.explanation = "Python is a programming language"
        mock_quiz.questions = [q1]

        result = _extract_quiz_text(mock_quiz)
        assert "What is Python?" in result
        assert "Language" in result
        assert "Python is a programming language" in result

    def test_multiple_questions(self):
        mock_quiz = MagicMock()
        q1 = MagicMock()
        q1.question = "Q1"
        q1.options = ["A", "B"]
        q1.explanation = "E1"
        q2 = MagicMock()
        q2.question = "Q2"
        q2.options = ["C", "D"]
        q2.explanation = None
        mock_quiz.questions = [q1, q2]

        result = _extract_quiz_text(mock_quiz)
        assert "Q1" in result
        assert "Q2" in result
        assert "E1" in result


class TestTemplateRendering:
    """Verify the Jinja2 templates render without errors."""

    def test_analyze_content_template(self):
        """The analyze_content template renders correctly."""
        from ai_prompter import Prompter
        from langchain_core.output_parsers.pydantic import PydanticOutputParser

        parser = PydanticOutputParser(pydantic_object=ContentAnalysisOutput)
        prompter = Prompter(
            prompt_template="learning_objectives/analyze_content.jinja",
            parser=parser,
        )

        rendered = prompter.render(data={
            "content_type": "source",
            "title": "Intro to ML",
            "content": "Machine learning is a subset of AI...",
        })

        assert "source" in rendered
        assert "Intro to ML" in rendered
        assert "Machine learning" in rendered

    def test_generate_aggregation_template(self):
        """The aggregation template renders with analyses data."""
        from ai_prompter import Prompter
        from langchain_core.output_parsers.pydantic import PydanticOutputParser

        parser = PydanticOutputParser(pydantic_object=AggregatedObjectives)
        prompter = Prompter(
            prompt_template="learning_objectives/generate.jinja",
            parser=parser,
        )

        rendered = prompter.render(data={
            "analyses": [
                {
                    "content_type": "source",
                    "title": "ML Basics",
                    "summary": "This covers ML fundamentals.",
                    "objectives": ["Explain supervised learning", "Compare classification vs regression"],
                },
            ],
            "num_objectives": 4,
        })

        assert "ML Basics" in rendered
        assert "supervised learning" in rendered
        assert "4" in rendered


class TestAnalyzeSingleContent:
    """Test the _analyze_single_content helper function."""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Returns cached analysis without calling LLM."""
        mock_cached = MagicMock()
        mock_cached.content_id = "source:abc"
        mock_cached.content_type = "source"
        mock_cached.summary = "Cached summary"
        mock_cached.objectives = ["Cached objective 1"]

        with patch(
            "open_notebook.graphs.learning_objectives_generation.ContentAnalysis.get_for_content",
            new_callable=AsyncMock,
            return_value=mock_cached,
        ):
            result = await _analyze_single_content(
                content_id="source:abc",
                content_type="source",
                title="Test Source",
                text="Some content",
            )

            assert result["summary"] == "Cached summary"
            assert result["objectives"] == ["Cached objective 1"]
            assert result["title"] == "Test Source"

    @pytest.mark.asyncio
    async def test_cache_miss_calls_llm(self):
        """Calls LLM and saves to cache on cache miss."""
        mock_response = MagicMock()
        mock_response.content = '{"summary": "AI summary", "objectives": ["Obj 1", "Obj 2"]}'

        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=mock_response)

        mock_analysis = MagicMock()
        mock_analysis.save = AsyncMock()

        with patch(
            "open_notebook.graphs.learning_objectives_generation.ContentAnalysis.get_for_content",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.provision_langchain_model",
            new_callable=AsyncMock,
            return_value=mock_model,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.Prompter"
        ) as mock_prompter_cls, patch(
            "open_notebook.graphs.learning_objectives_generation.ContentAnalysis"
        ) as mock_ca_cls:
            mock_prompter = MagicMock()
            mock_prompter.render.return_value = "Test prompt"
            mock_prompter_cls.return_value = mock_prompter

            mock_ca_cls.return_value = mock_analysis
            mock_ca_cls.get_for_content = AsyncMock(return_value=None)

            result = await _analyze_single_content(
                content_id="source:abc",
                content_type="source",
                title="Test Source",
                text="Some content about Python programming",
            )

            assert result["summary"] == "AI summary"
            assert result["objectives"] == ["Obj 1", "Obj 2"]
            assert mock_analysis.save.called


class TestAnalyzeAllContent:
    """Test the analyze_all_content node."""

    @pytest.mark.asyncio
    async def test_notebook_not_found(self):
        """Returns error when notebook doesn't exist."""
        state = _make_state(notebook_id="notebook:notfound")

        with patch(
            "open_notebook.graphs.learning_objectives_generation.Notebook.get"
        ) as mock_get:
            mock_get.side_effect = Exception("not found")

            result = await analyze_all_content(state)
            assert result["status"] == "failed"
            assert "Failed to analyze content" in result["error"]

    @pytest.mark.asyncio
    async def test_no_sources_no_artifacts(self):
        """Returns error when notebook has no analyzable content."""
        state = _make_state()

        mock_notebook = MagicMock()
        mock_notebook.get_sources = AsyncMock(return_value=[])

        with patch(
            "open_notebook.graphs.learning_objectives_generation.Notebook.get",
            new_callable=AsyncMock,
            return_value=mock_notebook,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.repo_query",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await analyze_all_content(state)
            assert result["status"] == "failed"
            assert "No analyzable content" in result["error"]

    @pytest.mark.asyncio
    async def test_success_with_sources(self):
        """Analyzes sources and returns content_analyses."""
        state = _make_state()

        mock_source = MagicMock()
        mock_source.id = "source:src1"
        mock_source.title = "ML Basics"
        mock_source.full_text = None  # omitted by get_sources

        mock_full_source = MagicMock()
        mock_full_source.full_text = "Machine learning content here"

        mock_notebook = MagicMock()
        mock_notebook.get_sources = AsyncMock(return_value=[mock_source])

        analysis_result = {
            "content_id": "source:src1",
            "content_type": "source",
            "title": "ML Basics",
            "summary": "Covers ML fundamentals",
            "objectives": ["Explain ML concepts"],
        }

        with patch(
            "open_notebook.graphs.learning_objectives_generation.Notebook.get",
            new_callable=AsyncMock,
            return_value=mock_notebook,
        ), patch(
            "open_notebook.domain.notebook.Source.get",
            new_callable=AsyncMock,
            return_value=mock_full_source,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation._analyze_single_content",
            new_callable=AsyncMock,
            return_value=analysis_result,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.repo_query",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await analyze_all_content(state)
            assert result["status"] == "generating"
            assert len(result["content_analyses"]) == 1
            assert result["content_analyses"][0]["content_id"] == "source:src1"


class TestAggregateObjectives:
    """Test the aggregate_objectives node."""

    @pytest.mark.asyncio
    async def test_skips_on_error(self):
        """Skips aggregation when prior error exists."""
        state = _make_state(error="Previous error")
        result = await aggregate_objectives(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_success(self):
        """Aggregates objectives with provenance from content analyses."""
        state = _make_state(
            content_analyses=[
                {
                    "content_id": "source:src1",
                    "content_type": "source",
                    "title": "ML Basics",
                    "summary": "Covers ML fundamentals",
                    "objectives": ["Explain ML concepts"],
                },
                {
                    "content_id": "quiz:q1",
                    "content_type": "quiz",
                    "title": "ML Quiz",
                    "summary": "Tests ML knowledge",
                    "objectives": ["Apply ML classification"],
                },
            ],
            status="generating",
        )

        mock_response = MagicMock()
        mock_response.content = '{"objectives": [{"text": "Explain core ML concepts and their applications", "source_refs": ["source:src1", "quiz:q1"]}, {"text": "Apply classification algorithms to real datasets", "source_refs": ["source:src1"]}, {"text": "Evaluate model performance using standard metrics", "source_refs": ["quiz:q1"]}, {"text": "Design a basic ML pipeline for structured data", "source_refs": ["source:src1", "quiz:q1"]}]}'

        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "open_notebook.graphs.learning_objectives_generation.provision_langchain_model",
            new_callable=AsyncMock,
            return_value=mock_model,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.Prompter"
        ) as mock_prompter_cls:
            mock_prompter = MagicMock()
            mock_prompter.render.return_value = "Test prompt"
            mock_prompter_cls.return_value = mock_prompter

            result = await aggregate_objectives(state)
            assert result["status"] == "saving"
            assert len(result["generated_objectives"]) == 4
            assert result["generated_objectives"][0]["source_refs"] == [
                "source:src1",
                "quiz:q1",
            ]
            assert result["generated_objectives"][0]["auto_generated"] is True
            assert result["generated_objectives"][0]["order"] == 0
            assert result["generated_objectives"][3]["order"] == 3


class TestSaveObjectives:
    """Test the save_objectives node."""

    @pytest.mark.asyncio
    async def test_skips_on_error(self):
        """Skips save when prior error exists."""
        state = _make_state(error="Previous error")
        result = await save_objectives(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_success_with_source_refs(self):
        """Saves objectives with source_refs to database."""
        state = _make_state(
            generated_objectives=[
                {
                    "text": "Objective 1",
                    "order": 0,
                    "auto_generated": True,
                    "source_refs": ["source:abc", "quiz:xyz"],
                },
                {
                    "text": "Objective 2",
                    "order": 1,
                    "auto_generated": True,
                    "source_refs": ["source:abc"],
                },
            ],
            status="saving",
        )

        mock_obj = MagicMock()
        mock_obj.id = "learning_objective:abc123"
        mock_obj.save = AsyncMock()

        with patch(
            "open_notebook.graphs.learning_objectives_generation.LearningObjective"
        ) as mock_cls:
            mock_cls.return_value = mock_obj

            result = await save_objectives(state)
            assert result["status"] == "completed"
            assert len(result["objective_ids"]) == 2
            assert mock_cls.call_count == 2
            assert mock_obj.save.call_count == 2

            # Verify source_refs was passed to constructor
            first_call_kwargs = mock_cls.call_args_list[0][1]
            assert first_call_kwargs["source_refs"] == ["source:abc", "quiz:xyz"]


class TestAggregateObjectivesContentFormats:
    """Test aggregate_objectives handles various LLM response formats."""

    _json_payload = '{"objectives": [{"text": "Obj 1", "source_refs": ["source:abc"]}, {"text": "Obj 2", "source_refs": ["source:def"]}, {"text": "Obj 3", "source_refs": ["source:abc", "source:def"]}, {"text": "Obj 4", "source_refs": ["source:abc"]}]}'

    def _make_mock_model(self, content):
        mock_response = MagicMock()
        mock_response.content = content
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=mock_response)
        return mock_model

    @pytest.mark.asyncio
    async def test_anthropic_content_blocks(self):
        """Handles Anthropic-style content block list."""
        state = _make_state(
            content_analyses=[{
                "content_id": "source:abc",
                "content_type": "source",
                "title": "Test",
                "summary": "Test summary",
                "objectives": ["Test obj"],
            }],
            status="generating",
        )

        content_blocks = [{"type": "text", "text": self._json_payload}]
        mock_model = self._make_mock_model(content_blocks)

        with patch(
            "open_notebook.graphs.learning_objectives_generation.provision_langchain_model",
            new_callable=AsyncMock,
            return_value=mock_model,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.Prompter"
        ) as mock_prompter_cls:
            mock_prompter = MagicMock()
            mock_prompter.render.return_value = "Test prompt"
            mock_prompter_cls.return_value = mock_prompter

            result = await aggregate_objectives(state)
            assert result["status"] == "saving"
            assert len(result["generated_objectives"]) == 4

    @pytest.mark.asyncio
    async def test_markdown_fenced_json(self):
        """Handles JSON wrapped in markdown code fences."""
        state = _make_state(
            content_analyses=[{
                "content_id": "source:abc",
                "content_type": "source",
                "title": "Test",
                "summary": "Test summary",
                "objectives": ["Test obj"],
            }],
            status="generating",
        )

        fenced = f"```json\n{self._json_payload}\n```"
        mock_model = self._make_mock_model(fenced)

        with patch(
            "open_notebook.graphs.learning_objectives_generation.provision_langchain_model",
            new_callable=AsyncMock,
            return_value=mock_model,
        ), patch(
            "open_notebook.graphs.learning_objectives_generation.Prompter"
        ) as mock_prompter_cls:
            mock_prompter = MagicMock()
            mock_prompter.render.return_value = "Test prompt"
            mock_prompter_cls.return_value = mock_prompter

            result = await aggregate_objectives(state)
            assert result["status"] == "saving"
            assert len(result["generated_objectives"]) == 4


class TestRecordIdFields:
    """Test the record_id_fields pattern on LearningObjective."""

    def test_learning_objective_has_record_id_fields(self):
        """LearningObjective declares notebook_id as a record_id_field."""
        from open_notebook.domain.learning_objective import LearningObjective

        assert "notebook_id" in LearningObjective.record_id_fields

    def test_learning_objective_has_source_refs(self):
        """LearningObjective has source_refs field defaulting to empty list."""
        from open_notebook.domain.learning_objective import LearningObjective

        obj = LearningObjective(
            notebook_id="notebook:test",
            text="Test objective",
            order=0,
        )
        assert obj.source_refs == []

    def test_learning_objective_with_source_refs(self):
        """LearningObjective accepts source_refs values."""
        from open_notebook.domain.learning_objective import LearningObjective

        obj = LearningObjective(
            notebook_id="notebook:test",
            text="Test objective",
            order=0,
            source_refs=["source:abc", "quiz:xyz"],
        )
        assert obj.source_refs == ["source:abc", "quiz:xyz"]

    def test_prepare_save_data_converts_record_ids(self):
        """_prepare_save_data converts record_id_fields to RecordID objects."""
        from open_notebook.domain.learning_objective import LearningObjective
        from surrealdb import RecordID

        obj = LearningObjective(
            notebook_id="notebook:test",
            text="Test objective",
            order=0,
            source_refs=["source:abc"],
        )
        data = obj._prepare_save_data()
        assert isinstance(data["notebook_id"], RecordID)

    def test_artifact_has_record_id_fields(self):
        """Artifact also uses record_id_fields for notebook_id."""
        from open_notebook.domain.artifact import Artifact

        assert "notebook_id" in Artifact.record_id_fields

    def test_quiz_has_record_id_fields(self):
        """Quiz also uses record_id_fields for notebook_id."""
        from open_notebook.domain.quiz import Quiz

        assert "notebook_id" in Quiz.record_id_fields


class TestContentAnalysisModel:
    """Test the ContentAnalysis domain model."""

    def test_create_instance(self):
        """Can create a ContentAnalysis instance."""
        from open_notebook.domain.content_analysis import ContentAnalysis

        ca = ContentAnalysis(
            content_id="source:abc",
            content_type="source",
            summary="Test summary",
            objectives=["Obj 1", "Obj 2"],
        )
        assert ca.content_id == "source:abc"
        assert ca.content_type == "source"
        assert ca.summary == "Test summary"
        assert ca.objectives == ["Obj 1", "Obj 2"]

    def test_default_objectives(self):
        """Objectives defaults to empty list."""
        from open_notebook.domain.content_analysis import ContentAnalysis

        ca = ContentAnalysis(
            content_id="source:abc",
            content_type="source",
            summary="Test summary",
        )
        assert ca.objectives == []

    def test_table_name(self):
        """Has correct table_name."""
        from open_notebook.domain.content_analysis import ContentAnalysis

        assert ContentAnalysis.table_name == "content_analysis"


class TestEnsureRecordIdUrlDecoding:
    """Test that ensure_record_id handles URL-encoded IDs."""

    def test_normal_record_id(self):
        from open_notebook.database.repository import ensure_record_id

        rid = ensure_record_id("notebook:abc123")
        assert str(rid) == "notebook:abc123"

    def test_url_encoded_colon(self):
        from open_notebook.database.repository import ensure_record_id

        rid = ensure_record_id("notebook%3Aabc123")
        assert str(rid) == "notebook:abc123"

    def test_already_record_id(self):
        from surrealdb import RecordID
        from open_notebook.database.repository import ensure_record_id

        original = RecordID.parse("notebook:abc123")
        result = ensure_record_id(original)
        assert result is original
