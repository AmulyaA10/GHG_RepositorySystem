"""
Test Workflow State Machine
"""
import pytest
from core.workflow import WorkflowManager
from models import Project, AuditLog

def test_draft_to_submitted_transition(db_session, test_project, test_user):
    """Test transitioning from DRAFT to SUBMITTED"""
    # Should be allowed for L1 users
    can_transition, message = WorkflowManager.can_transition("DRAFT", "SUBMITTED", "L1")
    assert can_transition is True

    # Perform transition
    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="SUBMITTED",
        user_id=test_user.id,
        user_role="L1"
    )

    db_session.refresh(test_project)
    assert test_project.status == "SUBMITTED"
    assert test_project.submitted_at is not None

    # Check audit log
    log = db_session.query(AuditLog).filter(
        AuditLog.project_id == test_project.id,
        AuditLog.action == "SUBMITTED"
    ).first()

    assert log is not None
    assert log.from_status == "DRAFT"
    assert log.to_status == "SUBMITTED"
    assert log.user_id == test_user.id

def test_invalid_transition(test_project):
    """Test that invalid transitions are rejected"""
    # Cannot go directly from DRAFT to LOCKED
    can_transition, message = WorkflowManager.can_transition("DRAFT", "LOCKED", "L1")
    assert can_transition is False
    assert "Invalid transition" in message

def test_unauthorized_role(test_project):
    """Test that unauthorized roles cannot perform transitions"""
    # L1 cannot transition from PENDING_REVIEW to APPROVED
    can_transition, message = WorkflowManager.can_transition("PENDING_REVIEW", "APPROVED", "L1")
    assert can_transition is False
    assert "does not have permission" in message

def test_submitted_to_under_calculation(db_session, test_project, test_user):
    """Test L2 can move SUBMITTED to UNDER_CALCULATION"""
    # First transition to SUBMITTED
    test_project.status = "SUBMITTED"
    db_session.commit()

    # L2 should be able to transition
    can_transition, message = WorkflowManager.can_transition("SUBMITTED", "UNDER_CALCULATION", "L2")
    assert can_transition is True

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="UNDER_CALCULATION",
        user_id=test_user.id,
        user_role="L2"
    )

    db_session.refresh(test_project)
    assert test_project.status == "UNDER_CALCULATION"

def test_under_calculation_to_pending_review(db_session, test_project, test_user):
    """Test L2 can move UNDER_CALCULATION to PENDING_REVIEW"""
    test_project.status = "UNDER_CALCULATION"
    db_session.commit()

    can_transition, message = WorkflowManager.can_transition("UNDER_CALCULATION", "PENDING_REVIEW", "L2")
    assert can_transition is True

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="PENDING_REVIEW",
        user_id=test_user.id,
        user_role="L2"
    )

    db_session.refresh(test_project)
    assert test_project.status == "PENDING_REVIEW"
    assert test_project.calculated_at is not None

def test_pending_review_to_approved(db_session, test_project, test_user):
    """Test L3 can approve projects"""
    test_project.status = "PENDING_REVIEW"
    db_session.commit()

    can_transition, message = WorkflowManager.can_transition("PENDING_REVIEW", "APPROVED", "L3")
    assert can_transition is True

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="APPROVED",
        user_id=test_user.id,
        user_role="L3",
        comments="Project approved"
    )

    db_session.refresh(test_project)
    assert test_project.status == "APPROVED"
    assert test_project.reviewed_at is not None

def test_pending_review_to_rejected(db_session, test_project, test_user):
    """Test L3 can reject projects"""
    test_project.status = "PENDING_REVIEW"
    db_session.commit()

    can_transition, message = WorkflowManager.can_transition("PENDING_REVIEW", "REJECTED", "L3")
    assert can_transition is True

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="REJECTED",
        user_id=test_user.id,
        user_role="L3",
        comments="Incomplete data",
        reason_code="DQ001"
    )

    db_session.refresh(test_project)
    assert test_project.status == "REJECTED"

    # Check audit log includes reason code
    log = db_session.query(AuditLog).filter(
        AuditLog.project_id == test_project.id,
        AuditLog.action == "REJECTED"
    ).first()

    assert log.reason_code == "DQ001"
    assert log.comments == "Incomplete data"

def test_rejected_to_submitted(db_session, test_project, test_user):
    """Test L1 can resubmit rejected projects"""
    test_project.status = "REJECTED"
    db_session.commit()

    can_transition, message = WorkflowManager.can_transition("REJECTED", "SUBMITTED", "L1")
    assert can_transition is True

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="SUBMITTED",
        user_id=test_user.id,
        user_role="L1"
    )

    db_session.refresh(test_project)
    assert test_project.status == "SUBMITTED"

def test_approved_to_locked(db_session, test_project, test_user):
    """Test L4 can lock approved projects"""
    test_project.status = "APPROVED"
    db_session.commit()

    can_transition, message = WorkflowManager.can_transition("APPROVED", "LOCKED", "L4")
    assert can_transition is True

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="LOCKED",
        user_id=test_user.id,
        user_role="L4"
    )

    db_session.refresh(test_project)
    assert test_project.status == "LOCKED"
    assert test_project.locked_at is not None
    assert test_project.approved_at is not None

def test_locked_is_final(test_project):
    """Test that LOCKED status cannot be transitioned"""
    # LOCKED state should have no valid transitions
    can_transition, message = WorkflowManager.can_transition("LOCKED", "DRAFT", "L4")
    assert can_transition is False

def test_audit_log_creation(db_session, test_project, test_user):
    """Test that all transitions create audit logs"""
    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="SUBMITTED",
        user_id=test_user.id,
        user_role="L1"
    )

    logs = db_session.query(AuditLog).filter(
        AuditLog.project_id == test_project.id
    ).all()

    assert len(logs) > 0
    log = logs[0]
    assert log.user_id == test_user.id
    assert log.user_role == "L1"
    assert log.action == "SUBMITTED"
    assert log.created_at is not None

def test_timestamp_updates(db_session, test_project, test_user):
    """Test that appropriate timestamps are updated"""
    # Transition to SUBMITTED
    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="SUBMITTED",
        user_id=test_user.id,
        user_role="L1"
    )

    db_session.refresh(test_project)
    assert test_project.submitted_at is not None

    # Transition to APPROVED
    test_project.status = "PENDING_REVIEW"
    db_session.commit()

    WorkflowManager.transition(
        db=db_session,
        project=test_project,
        new_status="APPROVED",
        user_id=test_user.id,
        user_role="L3"
    )

    db_session.refresh(test_project)
    assert test_project.reviewed_at is not None
    assert test_project.approved_at is not None
