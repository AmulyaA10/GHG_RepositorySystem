"""
Review Model - L3 Review Records
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # Review decision
    is_approved = Column(Boolean, nullable=False)
    reason_code_id = Column(Integer, ForeignKey("reason_codes.id"))
    comments = Column(Text)
    suggestions = Column(Text)

    # Metadata
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
    reason_code = relationship("ReasonCode")

    def __repr__(self):
        status = "APPROVED" if self.is_approved else "REJECTED"
        return f"<Review(id={self.id}, project_id={self.project_id}, status={status})>"
