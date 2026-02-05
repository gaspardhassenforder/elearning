from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import require_admin
from api.company_service import (
    create_company,
    delete_company,
    get_company,
    list_companies,
    update_company,
)
from api.models import CompanyCreate, CompanyResponse, CompanyUpdate
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


@router.delete("/companies/{company_id}", status_code=204)
async def delete_company_endpoint(
    company_id: str, _admin: User = Depends(require_admin)
):
    """Delete company (only if no assigned users or modules)."""
    try:
        deleted = await delete_company(company_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Company not found")
        return None
    except ValueError as e:
        logger.error(f"Company deletion blocked: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
