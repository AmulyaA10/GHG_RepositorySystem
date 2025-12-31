"""
AuditLog Model - Complete Audit Trail
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # CREATED, SUBMITTED, CALCULATED, REVIEWED, APPROVED, REJECTED, LOCKED
    from_status = Column(String(50))
    to_status = Column(String(50), index=True)

    # User tracking
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_role = Column(String(10), nullable=False)

    # Additional context
    comments = Column(Text)
    reason_code = Column(String(50))
    context_data = Column(JSON)  # Additional context data

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    project = relationship("Project", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', project_id={self.project_id})>"
