"""
Reporting Routes (Lane 5)
Dashboard & Reports

Provides dashboard data, GHG reports, and compliance
status for sustainability reporting.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_agent
from api.auth import get_current_user, require_any, require_l3_or_l4
from api.schemas import (
    DashboardDataResponse,
    GHGReportResponse,
    ComplianceStatusResponse
)
from models.user import User
from core.agent import (
    GHGAppAgent,
    ProjectNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow/reporting", tags=["Lane 5: Reporting"])


@router.get("/{project_id}/dashboard", response_model=DashboardDataResponse)
async def generate_dashboard_data(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_any)
):
    """
    Generate dashboard data for a project.

    **Persona**: All roles

    Returns:
    - Project overview
    - Scope breakdown with categories
    - Emission totals
    - Dashboard URL
    """
    try:
        result = agent.generate_dashboard_data(project_id)
        return DashboardDataResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error generating dashboard for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{project_id}/ghg-report", response_model=GHGReportResponse)
async def create_ghg_report(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l3_or_l4)
):
    """
    Create comprehensive GHG inventory report.

    **Persona**: QA Reviewer (L3), Sustainability Manager (L4)

    Generates a report including:
    - Report ID and metadata
    - Organization and reporting period
    - Scope 1, 2, 3 emissions
    - Total emissions
    - Verification status
    - Protocols applied (GHG Protocol, ISO 14064-1)
    """
    try:
        result = agent.create_ghg_report(project_id)

        logger.info(
            f"GHG report generated: project={project_id}, "
            f"by user={current_user.username}"
        )

        return GHGReportResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error generating GHG report for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{project_id}/compliance-status", response_model=ComplianceStatusResponse)
async def get_reporting_compliance_status(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_any)
):
    """
    Get compliance status for reporting requirements.

    **Persona**: All roles

    Checks:
    - Scope 1 reported
    - Scope 2 reported
    - Scope 3 reported
    - Verified status
    - Locked status
    """
    try:
        result = agent.get_reporting_compliance_status(project_id)
        return ComplianceStatusResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error getting compliance status for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
