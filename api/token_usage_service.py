"""
Token Usage Service Layer

Business logic for token usage aggregation and querying.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger

from open_notebook.domain.token_usage import TokenUsage
from open_notebook.domain.company import Company
from open_notebook.domain.notebook import Notebook
from open_notebook.database.repository import repo_query
from api.models.token_usage_models import (
    CompanyTokenUsageSummary,
    NotebookTokenUsageSummary,
    PlatformTokenUsageSummary,
)


async def get_company_token_usage(
    company_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> CompanyTokenUsageSummary:
    """
    Get aggregated token usage for a company.

    Args:
        company_id: Company record ID
        start_date: Start of time window (defaults to 30 days ago)
        end_date: End of time window (defaults to now)

    Returns:
        CompanyTokenUsageSummary with aggregated data

    Raises:
        ValueError: If company not found
    """
    # Apply default date range if not specified
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Validate company exists
    try:
        company = await Company.get(company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")
    except Exception as e:
        logger.error(f"Error loading company {company_id}: {e}")
        raise ValueError(f"Company {company_id} not found")

    # Get aggregated usage
    aggregation = await TokenUsage.aggregate_by_company(
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    return CompanyTokenUsageSummary(
        company_id=company_id,
        company_name=company.name,
        start_date=start_date,
        end_date=end_date,
        total_input_tokens=aggregation["total_input_tokens"],
        total_output_tokens=aggregation["total_output_tokens"],
        total_operations=aggregation["total_operations"],
        breakdown_by_operation_type=aggregation["by_operation"],
        breakdown_by_model=aggregation["by_model"],
    )


async def get_notebook_token_usage(
    notebook_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> NotebookTokenUsageSummary:
    """
    Get aggregated token usage for a notebook/module.

    Args:
        notebook_id: Notebook record ID
        start_date: Start of time window (defaults to 30 days ago)
        end_date: End of time window (defaults to now)

    Returns:
        NotebookTokenUsageSummary with aggregated data

    Raises:
        ValueError: If notebook not found
    """
    # Apply default date range if not specified
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Validate notebook exists
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise ValueError(f"Notebook {notebook_id} not found")
    except Exception as e:
        logger.error(f"Error loading notebook {notebook_id}: {e}")
        raise ValueError(f"Notebook {notebook_id} not found")

    # Get aggregated usage from domain model
    aggregation = await TokenUsage.aggregate_by_notebook(
        notebook_id=notebook_id,
        start_date=start_date,
        end_date=end_date,
    )

    return NotebookTokenUsageSummary(
        notebook_id=notebook_id,
        notebook_title=notebook.title,
        start_date=start_date,
        end_date=end_date,
        total_input_tokens=aggregation["total_input_tokens"],
        total_output_tokens=aggregation["total_output_tokens"],
        total_operations=aggregation["total_operations"],
        breakdown_by_operation_type=aggregation["by_operation"],
        breakdown_by_model=aggregation["by_model"],
    )


async def get_platform_token_usage(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> PlatformTokenUsageSummary:
    """
    Get platform-wide token usage summary.

    Aggregates usage across all companies.

    Args:
        start_date: Start of time window (defaults to 30 days ago)
        end_date: End of time window (defaults to now)

    Returns:
        PlatformTokenUsageSummary with platform-wide and per-company data
    """
    # Apply default date range if not specified
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Single query to aggregate all companies at once (fixes N+1 problem)
    query = """
        SELECT
            company_id,
            operation_type,
            model_name,
            math::sum(input_tokens) AS total_input,
            math::sum(output_tokens) AS total_output,
            count() AS operation_count
        FROM token_usage
        WHERE timestamp >= $start_date
        AND timestamp <= $end_date
        AND company_id IS NOT NONE
        GROUP BY company_id, operation_type, model_name
    """
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    results = await repo_query(query, params)

    # Build per-company aggregations and platform totals in single pass
    company_data = {}  # company_id -> {total_input, total_output, by_operation, by_model}
    platform_by_operation = {}
    platform_by_model = {}
    total_input = 0
    total_output = 0

    for record in results:
        company_id = record["company_id"]
        op_type = record["operation_type"]
        model = record["model_name"]
        inp = record["total_input"]
        out = record["total_output"]
        count = record["operation_count"]

        # Initialize company data if first record for this company
        if company_id not in company_data:
            company_data[company_id] = {
                "total_input": 0,
                "total_output": 0,
                "by_operation": {},
                "by_model": {},
            }

        # Update company aggregations
        company_data[company_id]["total_input"] += inp
        company_data[company_id]["total_output"] += out

        if op_type not in company_data[company_id]["by_operation"]:
            company_data[company_id]["by_operation"][op_type] = {
                "input": 0,
                "output": 0,
                "count": 0,
            }
        company_data[company_id]["by_operation"][op_type]["input"] += inp
        company_data[company_id]["by_operation"][op_type]["output"] += out
        company_data[company_id]["by_operation"][op_type]["count"] += count

        if model not in company_data[company_id]["by_model"]:
            company_data[company_id]["by_model"][model] = {
                "input": 0,
                "output": 0,
                "count": 0,
            }
        company_data[company_id]["by_model"][model]["input"] += inp
        company_data[company_id]["by_model"][model]["output"] += out
        company_data[company_id]["by_model"][model]["count"] += count

        # Update platform-wide aggregations
        total_input += inp
        total_output += out

        if op_type not in platform_by_operation:
            platform_by_operation[op_type] = {"input": 0, "output": 0, "count": 0}
        platform_by_operation[op_type]["input"] += inp
        platform_by_operation[op_type]["output"] += out
        platform_by_operation[op_type]["count"] += count

        if model not in platform_by_model:
            platform_by_model[model] = {"input": 0, "output": 0, "count": 0}
        platform_by_model[model]["input"] += inp
        platform_by_model[model]["output"] += out
        platform_by_model[model]["count"] += count

    # Build company summaries with company names
    company_summaries = []
    for company_id, data in company_data.items():
        try:
            company = await Company.get(company_id)
            company_name = company.name if company else None
        except Exception as e:
            logger.warning(f"Could not load company {company_id}: {e}")
            company_name = None

        total_ops = sum(op["count"] for op in data["by_operation"].values())

        company_summaries.append(
            CompanyTokenUsageSummary(
                company_id=company_id,
                company_name=company_name,
                start_date=start_date,
                end_date=end_date,
                total_input_tokens=data["total_input"],
                total_output_tokens=data["total_output"],
                total_operations=total_ops,
                breakdown_by_operation_type=data["by_operation"],
                breakdown_by_model=data["by_model"],
            )
        )

    total_operations = sum(op["count"] for op in platform_by_operation.values())

    return PlatformTokenUsageSummary(
        start_date=start_date,
        end_date=end_date,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_operations=total_operations,
        breakdown_by_operation_type=platform_by_operation,
        breakdown_by_model=platform_by_model,
        company_summaries=company_summaries,
    )
