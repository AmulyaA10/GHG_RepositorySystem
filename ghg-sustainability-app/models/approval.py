"""
Approval Model - L4 Approval Records
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # Approval details
    comments = Column(Text)
    snapshot = Column(JSON)  # Store complete project snapshot at approval time

    # Metadata
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")

    def __repr__(self):
        return f"<Approval(id={self.id}, project_id={self.project_id})>"
