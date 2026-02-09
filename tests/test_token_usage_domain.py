"""
Unit tests for TokenUsage domain model.

Tests token usage tracking functionality including CRUD operations,
querying by company/notebook, and aggregation methods.
"""

import pytest
from datetime import datetime, timedelta
from open_notebook.domain.token_usage import TokenUsage


class TestTokenUsageDomainModel:
    """Test suite for TokenUsage domain model."""

    @pytest.mark.asyncio
    async def test_token_usage_create_and_save(self):
        """TokenUsage record can be created and saved."""
        # Arrange
        usage = TokenUsage(
            user_id="user:test123",
            company_id="company:xyz",
            notebook_id="notebook:abc",
            model_provider="openai",
            model_name="gpt-4-turbo",
            input_tokens=150,
            output_tokens=75,
            operation_type="chat",
        )

        # Act
        await usage.save()

        # Assert
        assert usage.id is not None
        assert usage.user_id == "user:test123"
        assert usage.company_id == "company:xyz"
        assert usage.notebook_id == "notebook:abc"
        assert usage.model_provider == "openai"
        assert usage.model_name == "gpt-4-turbo"
        assert usage.input_tokens == 150
        assert usage.output_tokens == 75
        assert usage.operation_type == "chat"
        assert isinstance(usage.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_token_usage_handles_missing_optional_fields(self):
        """TokenUsage allows None for user_id, company_id, notebook_id."""
        # Arrange - system operation without user context
        usage = TokenUsage(
            user_id=None,
            company_id=None,
            notebook_id=None,
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            input_tokens=200,
            output_tokens=100,
            operation_type="embedding",
        )

        # Act
        await usage.save()

        # Assert
        assert usage.id is not None
        assert usage.user_id is None
        assert usage.company_id is None
        assert usage.notebook_id is None
        assert usage.model_provider == "anthropic"

    @pytest.mark.asyncio
    async def test_get_usage_by_company_filters_correctly(self):
        """get_usage_by_company returns only company's records."""
        # Arrange - Create records for two companies
        now = datetime.utcnow()
        start = now - timedelta(days=7)
        end = now + timedelta(days=1)

        # Company ABC records
        for i in range(3):
            usage = TokenUsage(
                user_id=f"user:abc{i}",
                company_id="company:abc",
                notebook_id="notebook:test",
                model_provider="openai",
                model_name="gpt-4",
                input_tokens=100 + i,
                output_tokens=50 + i,
                operation_type="chat",
            )
            await usage.save()

        # Company XYZ records (should not appear)
        usage_xyz = TokenUsage(
            user_id="user:xyz1",
            company_id="company:xyz",
            notebook_id="notebook:test",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=500,
            output_tokens=250,
            operation_type="chat",
        )
        await usage_xyz.save()

        # Act
        results = await TokenUsage.get_usage_by_company(
            company_id="company:abc",
            start_date=start,
            end_date=end
        )

        # Assert
        assert len(results) == 3
        assert all(r.company_id == "company:abc" for r in results)
        assert not any(r.company_id == "company:xyz" for r in results)

    @pytest.mark.asyncio
    async def test_get_usage_by_notebook_filters_correctly(self):
        """get_usage_by_notebook returns only notebook's records."""
        # Arrange
        now = datetime.utcnow()
        start = now - timedelta(days=7)
        end = now + timedelta(days=1)

        # Notebook AAA records
        for i in range(2):
            usage = TokenUsage(
                user_id=f"user:test{i}",
                company_id="company:test",
                notebook_id="notebook:aaa",
                model_provider="openai",
                model_name="gpt-4",
                input_tokens=100 + i,
                output_tokens=50 + i,
                operation_type="chat",
            )
            await usage.save()

        # Notebook BBB records (should not appear)
        usage_bbb = TokenUsage(
            user_id="user:test3",
            company_id="company:test",
            notebook_id="notebook:bbb",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=300,
            output_tokens=150,
            operation_type="quiz_generation",
        )
        await usage_bbb.save()

        # Act
        results = await TokenUsage.get_usage_by_notebook(
            notebook_id="notebook:aaa",
            start_date=start,
            end_date=end
        )

        # Assert
        assert len(results) == 2
        assert all(r.notebook_id == "notebook:aaa" for r in results)
        assert not any(r.notebook_id == "notebook:bbb" for r in results)

    @pytest.mark.asyncio
    async def test_aggregate_by_company_sums_correctly(self):
        """aggregate_by_company returns accurate totals."""
        # Arrange
        now = datetime.utcnow()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

        # Create test records with known totals
        records = [
            ("chat", "gpt-4", 100, 50),
            ("chat", "gpt-4", 150, 75),
            ("quiz_generation", "gpt-4-turbo", 200, 100),
            ("embedding", "text-embedding-3-small", 50, 0),
        ]

        for operation_type, model_name, input_tok, output_tok in records:
            usage = TokenUsage(
                user_id="user:test",
                company_id="company:aggregate_test",
                notebook_id="notebook:test",
                model_provider="openai",
                model_name=model_name,
                input_tokens=input_tok,
                output_tokens=output_tok,
                operation_type=operation_type,
            )
            await usage.save()

        # Act
        aggregation = await TokenUsage.aggregate_by_company(
            company_id="company:aggregate_test",
            start_date=start,
            end_date=end
        )

        # Assert
        assert aggregation["total_input_tokens"] == 500  # 100+150+200+50
        assert aggregation["total_output_tokens"] == 225  # 50+75+100+0
        assert aggregation["total_operations"] == 4

        # Check operation breakdown
        assert "chat" in aggregation["by_operation"]
        assert aggregation["by_operation"]["chat"]["input"] == 250  # 100+150
        assert aggregation["by_operation"]["chat"]["output"] == 125  # 50+75
        assert aggregation["by_operation"]["chat"]["count"] == 2

        assert "quiz_generation" in aggregation["by_operation"]
        assert aggregation["by_operation"]["quiz_generation"]["input"] == 200
        assert aggregation["by_operation"]["quiz_generation"]["output"] == 100
        assert aggregation["by_operation"]["quiz_generation"]["count"] == 1

        # Check model breakdown
        assert "gpt-4" in aggregation["by_model"]
        assert aggregation["by_model"]["gpt-4"]["input"] == 250
        assert aggregation["by_model"]["gpt-4"]["output"] == 125

    @pytest.mark.asyncio
    async def test_get_usage_by_company_with_operation_filter(self):
        """get_usage_by_company filters by operation_type when provided."""
        # Arrange
        now = datetime.utcnow()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

        # Create different operation types
        for op_type in ["chat", "chat", "quiz_generation", "embedding"]:
            usage = TokenUsage(
                user_id="user:test",
                company_id="company:filter_test",
                notebook_id="notebook:test",
                model_provider="openai",
                model_name="gpt-4",
                input_tokens=100,
                output_tokens=50,
                operation_type=op_type,
            )
            await usage.save()

        # Act - Filter for "chat" only
        results = await TokenUsage.get_usage_by_company(
            company_id="company:filter_test",
            start_date=start,
            end_date=end,
            operation_type="chat"
        )

        # Assert
        assert len(results) == 2
        assert all(r.operation_type == "chat" for r in results)

    @pytest.mark.asyncio
    async def test_get_usage_by_company_respects_date_range(self):
        """get_usage_by_company only returns records within date range."""
        # Arrange
        now = datetime.utcnow()

        # Old record (outside range)
        old_usage = TokenUsage(
            user_id="user:test",
            company_id="company:date_test",
            notebook_id="notebook:test",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=100,
            output_tokens=50,
            operation_type="chat",
            timestamp=now - timedelta(days=10)
        )
        await old_usage.save()

        # Recent record (inside range)
        recent_usage = TokenUsage(
            user_id="user:test",
            company_id="company:date_test",
            notebook_id="notebook:test",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=200,
            output_tokens=100,
            operation_type="chat",
            timestamp=now - timedelta(days=1)
        )
        await recent_usage.save()

        # Act - Query last 3 days
        start = now - timedelta(days=3)
        end = now + timedelta(days=1)
        results = await TokenUsage.get_usage_by_company(
            company_id="company:date_test",
            start_date=start,
            end_date=end
        )

        # Assert - Should only find recent record
        assert len(results) == 1
        assert results[0].input_tokens == 200
