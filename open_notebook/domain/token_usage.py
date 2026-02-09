"""
Token Usage Domain Model

Tracks token consumption per LLM operation for future cost attribution
and spending visibility per company/notebook.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import Field

from open_notebook.domain.base import ObjectModel
from open_notebook.database.repository import repo_query


class TokenUsage(ObjectModel):
    """
    Token usage record for LLM operations.

    Tracks input/output tokens per operation for future cost attribution
    and spending visibility per company/notebook.
    """

    table_name = "token_usage"

    user_id: Optional[str] = Field(
        None, description="User who initiated operation (None for system ops)"
    )
    company_id: Optional[str] = Field(
        None, description="Company context for learner operations"
    )
    notebook_id: Optional[str] = Field(
        None, description="Module context if applicable"
    )
    model_provider: str = Field(
        ..., description="AI provider: openai, anthropic, google, groq, etc."
    )
    model_name: str = Field(
        ...,
        description="Model identifier: gpt-4, claude-3-5-sonnet, gemini-flash-3, etc.",
    )
    input_tokens: int = Field(..., description="Prompt/input token count")
    output_tokens: int = Field(..., description="Completion/output token count")
    operation_type: str = Field(
        ...,
        description="Operation: chat, quiz_generation, embedding, transformation, search, navigation, objectives_generation",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When operation completed",
    )
    cost_estimate: Optional[float] = Field(
        None, description="Estimated cost in USD (future enhancement)"
    )

    @classmethod
    async def get_usage_by_company(
        cls,
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        operation_type: Optional[str] = None,
    ) -> List["TokenUsage"]:
        """
        Query token usage records for a company within date range.

        Args:
            company_id: Company record ID
            start_date: Start of time window (inclusive)
            end_date: End of time window (inclusive)
            operation_type: Optional filter by operation type

        Returns:
            List of TokenUsage records
        """
        query = """
            SELECT * FROM token_usage
            WHERE company_id = $company_id
            AND timestamp >= $start_date
            AND timestamp <= $end_date
        """
        params = {
            "company_id": company_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        if operation_type:
            query += " AND operation_type = $operation_type"
            params["operation_type"] = operation_type

        results = await repo_query(query, params)
        return [cls.model_validate(record) for record in results]

    @classmethod
    async def get_usage_by_notebook(
        cls, notebook_id: str, start_date: datetime, end_date: datetime
    ) -> List["TokenUsage"]:
        """Query token usage records for a specific notebook/module."""
        query = """
            SELECT * FROM token_usage
            WHERE notebook_id = $notebook_id
            AND timestamp >= $start_date
            AND timestamp <= $end_date
        """
        params = {
            "notebook_id": notebook_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        results = await repo_query(query, params)
        return [cls.model_validate(record) for record in results]

    @classmethod
    async def aggregate_by_company(
        cls, company_id: str, start_date: datetime, end_date: datetime
    ) -> dict:
        """
        Aggregate token usage by operation type and model for a company.

        Returns:
            {
                "total_input_tokens": int,
                "total_output_tokens": int,
                "total_operations": int,
                "by_operation": {"chat": {"input": X, "output": Y, "count": Z}, ...},
                "by_model": {"gpt-4": {"input": X, "output": Y, "count": Z}, ...}
            }
        """
        query = """
            SELECT
                operation_type,
                model_name,
                math::sum(input_tokens) AS total_input,
                math::sum(output_tokens) AS total_output,
                count() AS operation_count
            FROM token_usage
            WHERE company_id = $company_id
            AND timestamp >= $start_date
            AND timestamp <= $end_date
            GROUP BY operation_type, model_name
        """
        params = {
            "company_id": company_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        results = await repo_query(query, params)

        # Aggregate results
        total_input = 0
        total_output = 0
        by_operation = {}
        by_model = {}

        for record in results:
            op_type = record["operation_type"]
            model = record["model_name"]
            inp = record["total_input"]
            out = record["total_output"]
            count = record["operation_count"]

            total_input += inp
            total_output += out

            if op_type not in by_operation:
                by_operation[op_type] = {"input": 0, "output": 0, "count": 0}
            by_operation[op_type]["input"] += inp
            by_operation[op_type]["output"] += out
            by_operation[op_type]["count"] += count

            if model not in by_model:
                by_model[model] = {"input": 0, "output": 0, "count": 0}
            by_model[model]["input"] += inp
            by_model[model]["output"] += out
            by_model[model]["count"] += count

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_operations": sum(op["count"] for op in by_operation.values()),
            "by_operation": by_operation,
            "by_model": by_model,
        }
