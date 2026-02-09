"""
Token Usage Service Layer

Business logic for token usage aggregation and querying.
"""

from datetime import datetime, timedelta
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
    operation_type: Optional[str] = None,
) -> CompanyTokenUsageSummary:
    """
    Get aggregated token usage for a company.

    Args:
        company_id: Company record ID
        start_date: Start of time window (defaults to 30 days ago)
        end_date: End of time window (defaults to now)
        operation_type: Optional filter by operation type

    Returns:
        CompanyTokenUsageSummary with aggregated data

    Raises:
        ValueError: If company not found
    """
    # Apply default date range if not specified
    if end_date is None:
        end_date = datetime.utcnow()
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
        end_date = datetime.utcnow()
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

    # Query aggregated usage
    query = """
        SELECT
            operation_type,
            model_name,
            math::sum(input_tokens) AS total_input,
            math::sum(output_tokens) AS total_output,
            count() AS operation_count
        FROM token_usage
        WHERE notebook_id = $notebook_id
        AND timestamp >= $start_date
        AND timestamp <= $end_date
        GROUP BY operation_type, model_name
    """
    params = {
        "notebook_id": notebook_id,
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

    total_operations = sum(op["count"] for op in by_operation.values())

    return NotebookTokenUsageSummary(
        notebook_id=notebook_id,
        notebook_title=notebook.title,
        start_date=start_date,
        end_date=end_date,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_operations=total_operations,
        breakdown_by_operation_type=by_operation,
        breakdown_by_model=by_model,
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
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Query all companies with token usage in this period
    query = """
        SELECT DISTINCT company_id
        FROM token_usage
        WHERE timestamp >= $start_date
        AND timestamp <= $end_date
        AND company_id IS NOT NONE
    """
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    company_ids_result = await repo_query(query, params)
    company_ids = [r["company_id"] for r in company_ids_result]

    # Get summary for each company
    company_summaries = []
    total_input = 0
    total_output = 0
    platform_by_operation = {}
    platform_by_model = {}

    for company_id in company_ids:
        try:
            summary = await get_company_token_usage(
                company_id=company_id,
                start_date=start_date,
                end_date=end_date,
            )
            company_summaries.append(summary)

            # Aggregate platform-wide totals
            total_input += summary.total_input_tokens
            total_output += summary.total_output_tokens

            # Merge operation breakdowns
            for op_type, stats in summary.breakdown_by_operation_type.items():
                if op_type not in platform_by_operation:
                    platform_by_operation[op_type] = {"input": 0, "output": 0, "count": 0}
                platform_by_operation[op_type]["input"] += stats["input"]
                platform_by_operation[op_type]["output"] += stats["output"]
                platform_by_operation[op_type]["count"] += stats["count"]

            # Merge model breakdowns
            for model, stats in summary.breakdown_by_model.items():
                if model not in platform_by_model:
                    platform_by_model[model] = {"input": 0, "output": 0, "count": 0}
                platform_by_model[model]["input"] += stats["input"]
                platform_by_model[model]["output"] += stats["output"]
                platform_by_model[model]["count"] += stats["count"]

        except ValueError as e:
            logger.warning(f"Skipping company {company_id}: {e}")
            continue

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
