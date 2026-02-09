"""Company cascade deletion service for GDPR-compliant data removal."""

from typing import List

from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import repo_query
from open_notebook.domain.company import Company
from open_notebook.domain.user_deletion import UserDeletionReport, delete_user_cascade


class CompanyDeletionSummary(BaseModel):
    """Preview of what will be deleted."""

    company_id: str
    company_name: str
    user_count: int
    assignment_count: int
    affected_notebooks: List[str]


class CompanyDeletionReport(BaseModel):
    """Report of deleted records during company cascade deletion."""

    company_id: str
    deleted_users: int = 0
    deleted_user_data_records: int = 0  # Aggregate from user cascades
    deleted_assignments: int = 0
    total_deleted: int = 0
    user_deletion_reports: List[UserDeletionReport] = []


async def get_company_deletion_summary(company_id: str) -> CompanyDeletionSummary:
    """
    Get preview of what will be deleted if company is removed.

    Args:
        company_id: Company record ID

    Returns:
        CompanyDeletionSummary with counts and affected resources

    Raises:
        ValueError: If company not found
    """
    company = await Company.get(company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    # Count member users
    user_count = await company.get_member_count()

    # Count module assignments
    assignments = await repo_query(
        "SELECT notebook_id FROM module_assignment WHERE company_id = $cid",
        {"cid": company_id},
    )
    assignment_count = len(assignments) if assignments else 0
    affected_notebooks = (
        [a.get("notebook_id") for a in assignments] if assignments else []
    )

    return CompanyDeletionSummary(
        company_id=company_id,
        company_name=company.name,
        user_count=user_count,
        assignment_count=assignment_count,
        affected_notebooks=affected_notebooks,
    )


async def delete_company_cascade(company_id: str) -> CompanyDeletionReport:
    """
    Delete company and all associated data (GDPR-compliant cascade).

    Cascades to:
    - All member users (via delete_user_cascade for each)
    - module_assignment records
    - company record

    Args:
        company_id: Company record ID

    Returns:
        CompanyDeletionReport with aggregate counts

    Raises:
        ValueError: If company not found
    """
    company = await Company.get(company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    report = CompanyDeletionReport(company_id=company_id)

    # Get all member users
    users = await repo_query(
        "SELECT id FROM user WHERE company_id = $cid",
        {"cid": company_id},
    )

    # Delete each user (triggers user cascade)
    if users:
        for user_record in users:
            user_id = user_record.get("id")
            try:
                user_report = await delete_user_cascade(user_id)
                report.user_deletion_reports.append(user_report)
                report.deleted_users += 1
                report.deleted_user_data_records += user_report.total_deleted
            except Exception as e:
                logger.error(
                    f"Failed to delete user {user_id} during company cascade: {e}"
                )
                # Continue with other users

    # Delete module assignments
    assignment_result = await repo_query(
        "DELETE module_assignment WHERE company_id = $cid RETURN BEFORE",
        {"cid": company_id},
    )
    report.deleted_assignments = len(assignment_result) if assignment_result else 0

    # Delete company record
    await company.delete()

    # Calculate total
    report.total_deleted = (
        report.deleted_user_data_records + report.deleted_assignments + 1  # Company record itself
    )

    logger.error(
        f"Company deletion cascade completed",
        extra={"company_id": company_id, "report": report.model_dump()},
    )

    return report
