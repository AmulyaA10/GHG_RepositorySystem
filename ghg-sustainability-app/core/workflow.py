"""
Workflow State Machine for Project Lifecycle
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models.project import Project
from models.audit_log import AuditLog
from core.emailer import send_workflow_email
import logging

logger = logging.getLogger(__name__)

# Valid state transitions
STATE_TRANSITIONS = {
    "DRAFT": ["SUBMITTED"],
    "SUBMITTED": ["UNDER_CALCULATION", "DRAFT"],
    "UNDER_CALCULATION": ["PENDING_REVIEW", "SUBMITTED"],
    "PENDING_REVIEW": ["APPROVED", "REJECTED"],
    "REJECTED": ["SUBMITTED"],
    "APPROVED": ["LOCKED"],
    "LOCKED": []  # Final state
}

# Role permissions for state transitions
TRANSITION_PERMISSIONS = {
    ("DRAFT", "SUBMITTED"): ["L1"],
    ("SUBMITTED", "UNDER_CALCULATION"): ["L2"],
    ("SUBMITTED", "DRAFT"): ["L1", "L2"],
    ("UNDER_CALCULATION", "PENDING_REVIEW"): ["L2"],
    ("UNDER_CALCULATION", "SUBMITTED"): ["L2"],
    ("PENDING_REVIEW", "APPROVED"): ["L3"],
    ("PENDING_REVIEW", "REJECTED"): ["L3"],
    ("REJECTED", "SUBMITTED"): ["L1"],
    ("APPROVED", "LOCKED"): ["L4"],
}


class WorkflowManager:
    """Workflow state machine manager"""

    @staticmethod
    def can_transition(current_state: str, target_state: str, user_role: str) -> Tuple[bool, str]:
        """
        Check if a state transition is valid for the given role

        Args:
            current_state: Current project state
            target_state: Target state
            user_role: User's role code

        Returns:
            Tuple[bool, str]: (is_allowed, message)
        """
        # Check if transition is valid
        if target_state not in STATE_TRANSITIONS.get(current_state, []):
            return False, f"Invalid transition from {current_state} to {target_state}"

        # Check if user has permission
        allowed_roles = TRANSITION_PERMISSIONS.get((current_state, target_state), [])
        if user_role not in allowed_roles:
            return False, f"Role {user_role} does not have permission for this transition"

        return True, "Transition allowed"

    @staticmethod
    def transition(
        db: Session,
        project: Project,
        new_status: str,
        user_id: int,
        user_role: str,
        comments: Optional[str] = None,
        reason_code: Optional[str] = None
    ) -> None:
        """
        Transition a project to a new state

        Args:
            db: Database session
            project: Project object
            new_status: Target state
            user_id: User performing the transition
            user_role: User's role
            comments: Optional transition comments
            reason_code: Optional reason code (for rejections)

        Raises:
            ValueError: If transition is not allowed
        """
        current_state = project.status

        # Validate transition
        can_proceed, message = WorkflowManager.can_transition(current_state, new_status, user_role)
        if not can_proceed:
            raise ValueError(message)

        # Update project state
        old_state = project.status
        project.status = new_status
        project.updated_at = datetime.utcnow()

        # Update timestamps based on state
        if new_status == "SUBMITTED":
            project.submitted_at = datetime.utcnow()
        elif new_status == "PENDING_REVIEW":
            project.calculated_at = datetime.utcnow()
        elif new_status == "APPROVED":
            project.reviewed_at = datetime.utcnow()
            project.approved_at = datetime.utcnow()
        elif new_status == "LOCKED":
            project.locked_at = datetime.utcnow()

        # Create audit log
        WorkflowManager.log_transition(
            db=db,
            project=project,
            action=new_status,
            from_status=old_state,
            to_status=new_status,
            user_id=user_id,
            user_role=user_role,
            comments=comments,
            reason_code=reason_code
        )

        db.commit()

        logger.info(
            f"Project {project.id} transitioned from {old_state} to {new_status} by user {user_id}"
        )

        # Send email notification
        try:
            send_workflow_email(
                project=project,
                transition=f"{old_state}_to_{new_status}",
                comments=comments,
                reason_code=reason_code
            )
        except Exception as e:
            logger.warning(f"Email notification failed: {e}")

    @staticmethod
    def log_transition(
        db: Session,
        project: Project,
        action: str,
        from_status: Optional[str],
        to_status: str,
        user_id: int,
        user_role: str,
        comments: Optional[str] = None,
        reason_code: Optional[str] = None
    ) -> None:
        """
        Create an audit log entry for a state transition

        Args:
            db: Database session
            project: Project object
            action: Action performed
            from_status: Previous status
            to_status: New status
            user_id: User performing the action
            user_role: User's role
            comments: Optional comments
            reason_code: Optional reason code
        """
        audit_log = AuditLog(
            project_id=project.id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            user_id=user_id,
            user_role=user_role,
            comments=comments,
            reason_code=reason_code
        )
        db.add(audit_log)

    @staticmethod
    def get_available_transitions(project_status: str, user_role: str) -> List[str]:
        """
        Get list of available transitions for a project based on user role

        Args:
            project_status: Current project status
            user_role: User's role code

        Returns:
            List[str]: List of available target states
        """
        possible_states = STATE_TRANSITIONS.get(project_status, [])
        available = []

        for target_state in possible_states:
            can_proceed, _ = WorkflowManager.can_transition(project_status, target_state, user_role)
            if can_proceed:
                available.append(target_state)

        return available
