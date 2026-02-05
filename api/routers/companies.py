from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import require_admin
from api.models import CompanyCreate, CompanyResponse, CompanyUpdate
from api import company_service
from open_notebook.domain.user import User

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/companies", response_model=List[CompanyResponse])
async def list_companies():
    """Get all companies with user and assignment counts."""
    try:
        # Use optimized batch query to avoid N+1 problem
        companies_with_counts = await company_service.list_companies_with_counts()
        return [
            CompanyResponse(
                id=company.id or "",
                name=company.name,
                slug=company.slug,
                description=company.description,
                user_count=user_count,
                assignment_count=assignment_count,
                created=str(company.created),
                updated=str(company.updated),
            )
            for company, user_count, assignment_count in companies_with_counts
        ]
    except Exception as e:
        logger.error(f"Error listing companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing companies: {str(e)}")


@router.post("/companies", response_model=CompanyResponse)
async def create_company(company_data: CompanyCreate, admin: User = Depends(require_admin)):
    """Create a new company."""
    try:
        company = await company_service.create_company(
            name=company_data.name,
            slug=company_data.slug,
            description=company_data.description,
        )
        return CompanyResponse(
            id=company.id or "",
            name=company.name,
            slug=company.slug,
            description=company.description,
            user_count=0,
            assignment_count=0,
            created=str(company.created),
            updated=str(company.updated),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str):
    """Get a specific company by ID."""
    try:
        company = await company_service.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        user_count = await company_service.get_company_user_count(company_id)
        assignment_count = await company_service.get_company_assignment_count(company_id)
        return CompanyResponse(
            id=company.id or "",
            name=company.name,
            slug=company.slug,
            description=company.description,
            user_count=user_count,
            assignment_count=assignment_count,
            created=str(company.created),
            updated=str(company.updated),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


@router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str, company_update: CompanyUpdate, admin: User = Depends(require_admin)
):
    """Update a company."""
    try:
        company = await company_service.update_company(
            company_id=company_id,
            name=company_update.name,
            slug=company_update.slug,
            description=company_update.description,
        )
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        user_count = await company_service.get_company_user_count(company_id)
        assignment_count = await company_service.get_company_assignment_count(company_id)
        return CompanyResponse(
            id=company.id or "",
            name=company.name,
            slug=company.slug,
            description=company.description,
            user_count=user_count,
            assignment_count=assignment_count,
            created=str(company.created),
            updated=str(company.updated),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, admin: User = Depends(require_admin)):
    """Delete a company."""
    try:
        deleted = await company_service.delete_company(company_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Company deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
