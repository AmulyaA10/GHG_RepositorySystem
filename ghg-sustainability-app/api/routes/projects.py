"""
Project Management Routes

Provides CRUD operations for GHG projects with comprehensive
error handling, input validation, and audit logging.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from api.deps import get_db, get_agent
from api.auth import get_current_user, require_any
from api.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatusResponse,
    SuccessResponse
)
from models.project import Project
from models.user import User
from core.agent import GHGAppAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any)
):
    """
    Create a new GHG project.

    Only L1 users can typically create projects, but all roles can access this endpoint.
    """
    try:
        project = Project(
            project_name=project_data.project_name.strip(),
            organization_name=project_data.organization_name.strip(),
            reporting_year=project_data.reporting_year,
            description=project_data.description.strip() if project_data.description else None,
            created_by=current_user.id,
            created_by_email=current_user.email,
            status="DRAFT"
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        logger.info(
            f"Project created: ID={project.id}, name='{project.project_name}', "
            f"by user={current_user.username} (ID: {current_user.id})"
        )

        return project

    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Integrity error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with similar details already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        regex="^(DRAFT|SUBMITTED|UNDER_CALCULATION|PENDING_REVIEW|REJECTED|APPROVED|LOCKED)$",
        description="Filter by project status"
    ),
    organization: Optional[str] = Query(None, max_length=255, description="Filter by organization name"),
    reporting_year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by reporting year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any)
):
    """
    List all projects with optional filtering.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by project status
    - **organization**: Filter by organization name
    - **reporting_year**: Filter by reporting year
    """
    try:
        query = db.query(Project)

        # Apply filters with parameterized queries (safe from SQL injection)
        if status_filter:
            query = query.filter(Project.status == status_filter)
        if organization:
            # Sanitize and use parameterized ILIKE
            safe_org = organization.strip().replace("%", "\\%").replace("_", "\\_")
            query = query.filter(Project.organization_name.ilike(f"%{safe_org}%"))
        if reporting_year:
            query = query.filter(Project.reporting_year == reporting_year)

        # Get total count
        total = query.count()

        # Apply pagination
        projects = query.order_by(Project.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        logger.debug(
            f"Listed {len(projects)} projects (page {page}) by user={current_user.username}"
        )

        return ProjectListResponse(
            projects=projects,
            total=total,
            page=page,
            page_size=page_size
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error listing projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any)
):
    """
    Get project by ID.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            logger.debug(f"Project {project_id} not found (requested by {current_user.username})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        return project

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any)
):
    """
    Update project details.

    Only DRAFT projects can be updated.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        if project.status != "DRAFT":
            logger.warning(
                f"Update denied for project {project_id}: status={project.status} "
                f"(by user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only DRAFT projects can be updated"
            )

        # Update fields with sanitization
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(project, field, value)

        db.commit()
        db.refresh(project)

        logger.info(
            f"Project updated: ID={project_id}, fields={list(update_data.keys())}, "
            f"by user={current_user.username}"
        )

        return project

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Integrity error updating project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update conflicts with existing data"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any)
):
    """
    Delete a project.

    Only DRAFT projects can be deleted.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        if project.status != "DRAFT":
            logger.warning(
                f"Delete denied for project {project_id}: status={project.status} "
                f"(by user={current_user.username})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only DRAFT projects can be deleted"
            )

        project_name = project.project_name
        db.delete(project)
        db.commit()

        logger.info(
            f"Project deleted: ID={project_id}, name='{project_name}', "
            f"by user={current_user.username}"
        )

        return SuccessResponse(message=f"Project {project_id} deleted successfully")

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(
    project_id: int,
    db: Session = Depends(get_db),
    agent: GHGAppAgent = Depends(get_agent),
    current_user: User = Depends(require_any)
):
    """
    Get comprehensive project status including workflow position.
    """
    from core.agent import ProjectNotFoundError, DatabaseError

    try:
        status_data = agent.get_project_status(project_id)
        return ProjectStatusResponse(**status_data)

    except ProjectNotFoundError as e:
        logger.debug(f"Project {project_id} not found (requested by {current_user.username})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error getting project status {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Please try again."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
