from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from api.auth import require_admin
from api.company_service import (
    create_company,
    get_company,
    list_companies,
    update_company,
)
from api.models import CompanyCreate, CompanyResponse, CompanyUpdate
from open_notebook.domain.company_deletion import (
    CompanyDeletionReport,
    CompanyDeletionSummary,
    delete_company_cascade,
    get_company_deletion_summary,
)
from open_notebook.domain.user import User

router = APIRouter()


@router.post("/companies", response_model=CompanyResponse, status_code=201)
async def create_company_endpoint(
    data: CompanyCreate, _admin: User = Depends(require_admin)
):
    """Create a new company."""
    try:
        company = await create_company(name=data.name, slug=data.slug)
        user_count = await company.get_member_count()
        return CompanyResponse(
            id=company.id,
            name=company.name,
            slug=company.slug,
            user_count=user_count,
            assignment_count=0,
            created=str(company.created),
            updated=str(company.updated),
        )
    except ValueError as e:
        logger.error(f"Company creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(_admin: User = Depends(require_admin)):
    """List all companies with member counts."""
    try:
        return await list_companies()
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company_endpoint(company_id: str, _admin: User = Depends(require_admin)):
    """Get company details."""
    try:
        company = await get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company_endpoint(
    company_id: str, data: CompanyUpdate, _admin: User = Depends(require_admin)
):
    """Update company."""
    try:
        company = await update_company(
            company_id=company_id, name=data.name, slug=data.slug
        )
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        user_count = await company.get_member_count()
        return CompanyResponse(
            id=company.id,
            name=company.name,
            slug=company.slug,
            user_count=user_count,
            assignment_count=0,
            created=str(company.created),
            updated=str(company.updated),
        )
    except ValueError as e:
        logger.error(f"Company update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/companies/{company_id}/deletion-summary",
    response_model=CompanyDeletionSummary,
)
async def preview_company_deletion(
    company_id: str, _admin: User = Depends(require_admin)
):
    """
    Preview what will be deleted if company is removed (no action taken).

    Returns:
    - 200: CompanyDeletionSummary with counts and affected resources
    - 404: Company not found
    - 403: Requires admin privileges
    """
    try:
        summary = await get_company_deletion_summary(company_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting deletion summary for {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/companies/{company_id}", response_model=CompanyDeletionReport)
async def delete_company_endpoint(
    company_id: str,
    confirm: bool = Query(
        False, description="Must be true to proceed with deletion"
    ),
    admin: User = Depends(require_admin),
):
    """
    Delete company and ALL associated data (users, assignments). Requires confirmation.

    **WARNING: This is a destructive operation!**

    **Deleted Data:**
    - All member users (via user cascade for each)
    - All module assignments
    - Company record

    **Query Parameters:**
    - confirm: Must be true to proceed (safety check)

    **Returns:**
    - 200: CompanyDeletionReport with aggregate counts
    - 400: Confirmation required
    - 404: Company not found
    - 403: Requires admin privileges
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm deletion with ?confirm=true query parameter",
        )

    try:
        report = await delete_company_cascade(company_id)

        logger.warning(
            f"Company deleted by admin",
            extra={
                "company_id": company_id,
                "admin_id": admin.id,
                "report": report.model_dump(),
            },
        )

        return report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
