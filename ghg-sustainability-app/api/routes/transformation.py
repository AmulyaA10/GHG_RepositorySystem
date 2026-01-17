"""
Data Transformation Routes (Lane 2)
Persona: Data Mapper / Calculation Specialist (L2)

Handles emission factor mapping, calculations, and
transformation of activity data into GHG emissions.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_agent
from api.auth import get_current_user, require_l2
from api.schemas import (
    MapDataResponse,
    TransformDataRequest,
    TransformDataResponse,
    ValidateTransformationResponse,
    UpdateTotalsResponse,
    SubmitForReviewResponse
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

router = APIRouter(prefix="/workflow/transformation", tags=["Lane 2: Data Transformation"])


@router.post("/{project_id}/map", response_model=MapDataResponse)
async def map_data_model(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l2)
):
    """
    Map collected data to GHG emission schema.

    **Persona**: Calculation Specialist (L2)

    - Transitions project to UNDER_CALCULATION status
    - Prepares data for emission calculations
    """
    try:
        result = agent.map_data_model(
            project_id=project_id,
            user_id=current_user.id,
            user_role=current_user.role
        )

        logger.info(
            f"Data mapped for project {project_id} by user={current_user.username}"
        )

        return MapDataResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateError as e:
        logger.warning(f"Invalid state for data mapping on project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in map_data_model for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/transform", response_model=TransformDataResponse)
async def transform_data(
    project_id: int,
    data: TransformDataRequest,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l2)
):
    """
    Transform activity data into emission calculations.

    **Persona**: Calculation Specialist (L2)

    Creates a Calculation record with:
    - emission_factor: Emission factor value
    - emission_factor_source: Source reference (e.g., Ecoinvent ID)
    - scope: Scope 1, 2, or 3
    - category: Emission category
    - gwp: Global Warming Potential (default: 1.0)
    - unit_conversion: Unit conversion factor (default: 1.0)

    Formula: emissions_kg = activity_data × emission_factor × GWP × unit_conversion
    """
    try:
        result = agent.transform_data(
            project_id=project_id,
            project_data_id=data.project_data_id,
            emission_factor=data.emission_factor,
            emission_factor_source=data.emission_factor_source.strip(),
            scope=data.scope.value,
            category=data.category.strip(),
            user_id=current_user.id,
            gwp=data.gwp,
            unit_conversion=data.unit_conversion,
            notes=data.notes.strip() if data.notes else None
        )

        logger.info(
            f"Data transformed: project={project_id}, data_id={data.project_data_id}, "
            f"scope={data.scope.value}, by user={current_user.username}"
        )

        return TransformDataResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in transform_data for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/validate", response_model=ValidateTransformationResponse)
async def validate_data_transformation(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l2)
):
    """
    Validate transformed data for internal consistency.

    **Persona**: Calculation Specialist (L2)

    Checks:
    - Calculation accuracy
    - Valid scope values
    """
    try:
        result = agent.validate_data_transformation(project_id)
        return ValidateTransformationResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in validate_transformation for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.post("/{project_id}/update-totals", response_model=UpdateTotalsResponse)
async def update_project_totals(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l2)
):
    """
    Update project emission totals from calculations.

    **Persona**: Calculation Specialist (L2)

    Aggregates all calculations and updates project totals for:
    - Scope 1 emissions
    - Scope 2 emissions
    - Scope 3 emissions
    - Total emissions
    """
    try:
        result = agent.update_project_totals(project_id)

        logger.info(
            f"Project totals updated: project={project_id}, "
            f"by user={current_user.username}"
        )

        return UpdateTotalsResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in update_totals for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{project_id}/submit-review", response_model=SubmitForReviewResponse)
async def submit_for_review(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l2)
):
    """
    Submit calculated project for review (L2 -> L3 handoff).

    **Persona**: Calculation Specialist (L2)

    - Validates data transformation
    - Updates project totals
    - Transitions to PENDING_REVIEW status
    """
    try:
        # Validate first
        validation = agent.validate_data_transformation(project_id)
        if not validation.get("data_accuracy_compliant"):
            logger.warning(
                f"Submit for review rejected for project {project_id}: validation failed "
                f"(by user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed. Issues: {validation.get('issues', [])}"
            )

        result = agent.submit_for_review(
            project_id=project_id,
            user_id=current_user.id,
            user_role=current_user.role
        )

        logger.info(
            f"Project submitted for review: project={project_id}, "
            f"by user={current_user.username}"
        )

        return SubmitForReviewResponse(**result)

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
        logger.error(f"Database error in submit_for_review for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
