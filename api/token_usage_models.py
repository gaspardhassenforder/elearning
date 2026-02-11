"""
Pydantic models for token usage API endpoints.

These models define the request/response schemas for token usage aggregation queries.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TokenUsageRecord(BaseModel):
    """
    Single token usage record.

    Matches the TokenUsage domain model fields for API responses.
    """

    id: str = Field(..., description="Record ID")
    user_id: Optional[str] = Field(None, description="User who initiated operation")
    company_id: Optional[str] = Field(None, description="Company context")
    notebook_id: Optional[str] = Field(None, description="Module context")
    model_provider: str = Field(..., description="AI provider (openai, anthropic, etc.)")
    model_name: str = Field(..., description="Model identifier")
    input_tokens: int = Field(..., description="Input token count")
    output_tokens: int = Field(..., description="Output token count")
    operation_type: str = Field(
        ..., description="Operation type (chat, quiz_generation, etc.)"
    )
    timestamp: datetime = Field(..., description="When operation completed")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost in USD")


class TokenUsageAggregation(BaseModel):
    """
    Aggregated token usage summary.

    Contains total tokens and breakdowns by operation type and model.
    """

    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")
    total_operations: int = Field(..., description="Total operation count")
    breakdown_by_operation_type: Dict[str, Dict[str, int]] = Field(
        ...,
        description="Breakdown by operation type: {operation: {input, output, count}}",
    )
    breakdown_by_model: Dict[str, Dict[str, int]] = Field(
        ..., description="Breakdown by model: {model: {input, output, count}}"
    )


class CompanyTokenUsageSummary(TokenUsageAggregation):
    """
    Token usage summary for a specific company.

    Extends TokenUsageAggregation with company context and date range.
    """

    company_id: str = Field(..., description="Company record ID")
    company_name: Optional[str] = Field(None, description="Company name")
    start_date: datetime = Field(..., description="Start of time window")
    end_date: datetime = Field(..., description="End of time window")


class NotebookTokenUsageSummary(TokenUsageAggregation):
    """
    Token usage summary for a specific notebook/module.

    Extends TokenUsageAggregation with notebook context.
    """

    notebook_id: str = Field(..., description="Notebook record ID")
    notebook_title: Optional[str] = Field(None, description="Module title")
    start_date: datetime = Field(..., description="Start of time window")
    end_date: datetime = Field(..., description="End of time window")


class PlatformTokenUsageSummary(TokenUsageAggregation):
    """
    Platform-wide token usage summary.

    Extends TokenUsageAggregation with per-company summaries.
    """

    start_date: datetime = Field(..., description="Start of time window")
    end_date: datetime = Field(..., description="End of time window")
    company_summaries: List[CompanyTokenUsageSummary] = Field(
        default_factory=list, description="Per-company usage summaries"
    )
