"""
Data Collection Routes (Lane 1)
Persona: Data Collector (L1)

Handles raw data collection, aggregation, and submission
for GHG emissions calculations.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_agent
from api.auth import get_current_user, require_l1, require_l1_or_l2
from api.schemas import (
    RawDataCollect,
    RawDataCollectResponse,
    AggregateDataResponse,
    QualityCheckResponse,
    SubmitForCalculationResponse,
    SuccessResponse
)
from models.user import User
from core.agent import (
    GHGAppAgent,
    GHGAgentError,
    ProjectNotFoundError,
    InvalidStateError,
    ValidationError,
    DatabaseError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow/collection", tags=["Lane 1: Data Collection"])


@router.post("/{project_id}/collect", response_model=RawDataCollectResponse)
async def collect_raw_data(
    project_id: int,
    data: RawDataCollect,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l1)
):
    """
    Collect raw activity data for a project.

    **Persona**: Data Collector (L1)

    Creates a ProjectData record with:
    - criteria_id: Reference to emission criteria
    - activity_data: Activity amount (e.g., kWh, liters, km)
    - unit: Unit of measurement
    - notes: Optional notes
    """
    try:
        result = agent.collect_raw_data(
            project_id=project_id,
            criteria_id=data.criteria_id,
            activity_data=data.activity_data,
            unit=data.unit.strip(),
            notes=data.notes.strip() if data.notes else None,
            user_id=current_user.id
        )

        logger.info(
            f"Raw data collected: project={project_id}, criteria={data.criteria_id}, "
            f"by user={current_user.username}"
        )

        return RawDataCollectResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateError as e:
        logger.warning(f"Invalid state for data collection on project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in collect_raw_data for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/aggregate", response_model=AggregateDataResponse)
async def aggregate_data(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l1_or_l2)
):
    """
    Aggregate all collected data for a project.

    **Persona**: Data Collector (L1), Calculation Specialist (L2)

    Returns summary statistics of collected data.
    """
    try:
        result = agent.aggregate_data(project_id)
        return AggregateDataResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in aggregate_data for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{project_id}/quality-check", response_model=QualityCheckResponse)
async def initial_quality_check(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l1_or_l2)
):
    """
    Run initial quality checks on collected data.

    **Persona**: Data Collector (L1), Calculation Specialist (L2)

    Checks for:
    - Negative values
    - Missing units
    - Missing evidence
    """
    try:
        result = agent.initial_quality_check(project_id)
        return QualityCheckResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in quality_check for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.post("/{project_id}/submit", response_model=SubmitForCalculationResponse)
async def submit_for_calculation(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l1)
):
    """
    Submit project for calculation (L1 -> L2 handoff).

    **Persona**: Data Collector (L1)

    Transitions project from DRAFT to SUBMITTED status.
    Requires passing initial quality checks.
    """
    try:
        # Run quality check first
        qc_result = agent.initial_quality_check(project_id)
        if not agent.quality_check_pass(qc_result):
            logger.warning(
                f"Submit rejected for project {project_id}: quality check failed "
                f"(by user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quality check failed. Issues: {qc_result.get('issues', [])}"
            )

        result = agent.submit_for_calculation(
            project_id=project_id,
            user_id=current_user.id,
            user_role=current_user.role
        )

        logger.info(
            f"Project submitted for calculation: project={project_id}, "
            f"by user={current_user.username}"
        )

        return SubmitForCalculationResponse(**result)

    except HTTPException:
        raise
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in submit_for_calculation for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
