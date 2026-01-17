"""
Data Verification Routes (Lane 3)
Persona: QA Reviewer (L3)

Handles verification, compliance checking, and QA review
of GHG emission calculations per GHG Protocol and ISO 14064-1.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_agent
from api.auth import get_current_user, require_l3
from api.schemas import (
    VerifyDataResponse,
    ComplianceCheckResponse,
    ApproveVerificationRequest,
    ApproveVerificationResponse,
    RejectVerificationRequest,
    RejectVerificationResponse,
    VerificationReportResponse
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

router = APIRouter(prefix="/workflow/verification", tags=["Lane 3: Data Verification"])


@router.get("/{project_id}/verify", response_model=VerifyDataResponse)
async def verify_transformed_data(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l3)
):
    """
    Verify accuracy and integrity of transformed data.

    **Persona**: QA Reviewer (L3)

    Performs deeper checks:
    - All data records have calculations
    - Valid emission factors
    - Cross-reference validation
    """
    try:
        result = agent.verify_transformed_data(project_id)
        return VerifyDataResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in verify_transformed_data for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.get("/{project_id}/compliance", response_model=ComplianceCheckResponse)
async def ghg_protocol_compliance_check(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l3)
):
    """
    Check compliance with GHG Protocol standards.

    **Persona**: QA Reviewer (L3)

    Checks against:
    - GHG Protocol Corporate Standard
    - ISO 14064-1

    Validates:
    - Scope coverage (at least Scope 1 or 2 required)
    - Emission factor documentation
    """
    try:
        result = agent.ghg_protocol_compliance_check(project_id)
        return ComplianceCheckResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in compliance_check for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.post("/{project_id}/approve", response_model=ApproveVerificationResponse)
async def approve_verification(
    project_id: int,
    data: ApproveVerificationRequest,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l3)
):
    """
    Approve verification and transition to APPROVED status.

    **Persona**: QA Reviewer (L3)

    - Creates review record
    - Transitions project to APPROVED status
    """
    try:
        # Run verification checks first
        verification = agent.verify_transformed_data(project_id)
        if not verification.get("verification_passed"):
            logger.warning(
                f"Verification approval denied for project {project_id}: "
                f"verification failed (by user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Verification failed. Issues: {verification.get('issues', [])}"
            )

        # Run compliance check
        compliance = agent.ghg_protocol_compliance_check(project_id)
        if not compliance.get("compliant"):
            logger.warning(
                f"Verification approval denied for project {project_id}: "
                f"compliance failed (by user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Compliance check failed. Issues: {compliance.get('issues', [])}"
            )

        result = agent.approve_verification(
            project_id=project_id,
            verifier_id=current_user.id,
            verifier_role=current_user.role,
            comments=data.comments.strip() if data.comments else None
        )

        logger.info(
            f"Verification approved: project={project_id}, "
            f"by verifier={current_user.username}"
        )

        return ApproveVerificationResponse(**result)

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
        logger.error(f"Database error in approve_verification for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/reject", response_model=RejectVerificationResponse)
async def reject_verification(
    project_id: int,
    data: RejectVerificationRequest,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l3)
):
    """
    Reject verification and transition to REJECTED status.

    **Persona**: QA Reviewer (L3)

    Requires:
    - reason_code: Reason code for rejection
    - comments: Detailed explanation

    Sends project back to L1 for corrections.
    """
    try:
        result = agent.reject_verification(
            project_id=project_id,
            verifier_id=current_user.id,
            verifier_role=current_user.role,
            reason_code=data.reason_code.strip(),
            comments=data.comments.strip()
        )

        logger.info(
            f"Verification rejected: project={project_id}, reason={data.reason_code}, "
            f"by verifier={current_user.username}"
        )

        return RejectVerificationResponse(**result)

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
        logger.error(f"Database error in reject_verification for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/report", response_model=VerificationReportResponse)
async def generate_verification_report(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_l3)
):
    """
    Generate verification report for the project.

    **Persona**: QA Reviewer (L3)

    Creates a comprehensive verification report including:
    - Project details
    - Review history
    - Verification status
    """
    try:
        result = agent.generate_verification_report(project_id)

        logger.info(
            f"Verification report generated: project={project_id}, "
            f"by user={current_user.username}"
        )

        return VerificationReportResponse(**result)

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error generating verification report for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
