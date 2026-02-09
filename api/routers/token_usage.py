"""
Token Usage API Router

Admin-only endpoints for querying aggregated token usage data.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import require_admin
from api.token_usage_service import (
    get_company_token_usage,
    get_notebook_token_usage,
    get_platform_token_usage,
)
from api.models.token_usage_models import (
    CompanyTokenUsageSummary,
    NotebookTokenUsageSummary,
    PlatformTokenUsageSummary,
)
from open_notebook.domain.user import User


router = APIRouter()


@router.get(
    "/admin/token-usage/company/{company_id}",
    response_model=CompanyTokenUsageSummary,
    summary="Get Company Token Usage",
    description="Retrieve aggregated token usage for a specific company within date range (admin-only).",
    tags=["Token Usage"],
)
async def get_company_usage(
    company_id: str,
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601). Defaults to 30 days ago."
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601). Defaults to now."
    ),
    admin: User = Depends(require_admin),
):
    """
    Get aggregated token usage for a company.

    **Returns:**
    - 200: CompanyTokenUsageSummary with total tokens and breakdowns
    - 404: Company not found
    - 403: Requires admin privileges
    """
    try:
        summary = await get_company_token_usage(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
        )
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/admin/token-usage/notebook/{notebook_id}",
    response_model=NotebookTokenUsageSummary,
    summary="Get Notebook Token Usage",
    description="Retrieve aggregated token usage for a specific notebook/module (admin-only).",
    tags=["Token Usage"],
)
async def get_notebook_usage(
    notebook_id: str,
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601). Defaults to 30 days ago."
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601). Defaults to now."
    ),
    admin: User = Depends(require_admin),
):
    """
    Get aggregated token usage for a notebook.

    **Returns:**
    - 200: NotebookTokenUsageSummary with total tokens and breakdowns
    - 404: Notebook not found
    - 403: Requires admin privileges
    """
    try:
        summary = await get_notebook_token_usage(
            notebook_id=notebook_id,
            start_date=start_date,
            end_date=end_date,
        )
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/admin/token-usage/summary",
    response_model=PlatformTokenUsageSummary,
    summary="Get Platform Token Usage Summary",
    description="Retrieve aggregated token usage across all companies (admin-only).",
    tags=["Token Usage"],
)
async def get_platform_usage_summary(
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601). Defaults to 30 days ago."
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601). Defaults to now."
    ),
    admin: User = Depends(require_admin),
):
    """
    Get platform-wide token usage summary.

    **Returns:**
    - 200: PlatformTokenUsageSummary with platform-wide and per-company data
    - 403: Requires admin privileges
    """
    summary = await get_platform_token_usage(
        start_date=start_date,
        end_date=end_date,
    )
    return summary
