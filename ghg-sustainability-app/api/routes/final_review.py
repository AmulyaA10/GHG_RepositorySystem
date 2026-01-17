"""
Final Review Routes (Lane 4)
Persona: Sustainability Manager / Approver (L4)

Handles final approval, project locking, and archival
of verified GHG emissions data.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_agent
from api.auth import get_current_user, require_l4
from api.schemas import (
    FinalReviewResponse,
    FinalApprovalRequest,
    FinalApprovalResponse,
    ApprovalDocsResponse,
    ArchiveDataResponse
)
from models.user import User
from core.agent import (
    GHGAppAgent,
    GHGAgentError,
    ProjectNotFoundError,
    InvalidStateError,
    DatabaseError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow/final-review", tags=["Lane 4: Final Review"])


@router.get("/{project_id}/review", response_model=FinalReviewResponse)
async def final_data_review(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l4)
):
    """
    Perform final data review before locking.

    **Persona**: Sustainability Manager (L4)

    Returns comprehensive project summary:
    - Project details
    - Emission totals by scope
    - Calculation count
    - Current status
    """
    try:
        result = agent.final_data_review(project_id)
        return FinalReviewResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in final_data_review for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{project_id}/approve", response_model=FinalApprovalResponse)
async def final_data_approval(
    project_id: int,
    data: FinalApprovalRequest,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l4)
):
    """
    Final approval and lock the project.

    **Persona**: Sustainability Manager (L4)

    - Creates approval record
    - Transitions project to LOCKED status
    - Project becomes read-only after locking

    This is the final step in the GHG reporting workflow.
    """
    try:
        result = agent.final_data_approval(
            project_id=project_id,
            manager_id=current_user.id,
            manager_role=current_user.role,
            comments=data.comments.strip() if data.comments else None
        )

        logger.info(
            f"Final approval granted: project={project_id}, "
            f"locked by manager={current_user.username}"
        )

        return FinalApprovalResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateError as e:
        logger.warning(
            f"Final approval denied for project {project_id}: {e} "
            f"(by user={current_user.username})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in final_data_approval for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/approval-docs", response_model=ApprovalDocsResponse)
async def generate_approval_docs(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l4)
):
    """
    Generate approval documentation.

    **Persona**: Sustainability Manager (L4)

    Creates formal approval documentation including:
    - Document ID
    - Approval history
    - Generation timestamp
    """
    try:
        result = agent.generate_approval_docs(project_id)

        logger.info(
            f"Approval docs generated: project={project_id}, "
            f"by user={current_user.username}"
        )

        return ApprovalDocsResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error generating approval docs for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{project_id}/archive", response_model=ArchiveDataResponse)
async def archive_approved_data(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l4)
):
    """
    Archive approved project data.

    **Persona**: Sustainability Manager (L4)

    Only LOCKED projects can be archived.
    Creates an archive record for long-term storage.
    """
    try:
        result = agent.archive_approved_data(project_id)

        logger.info(
            f"Project archived: project={project_id}, "
            f"by user={current_user.username}"
        )

        return ArchiveDataResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateError as e:
        logger.warning(
            f"Archive denied for project {project_id}: {e} "
            f"(by user={current_user.username})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error archiving project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
