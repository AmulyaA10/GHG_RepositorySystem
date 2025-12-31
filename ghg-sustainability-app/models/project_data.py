"""
ProjectData Model - L1 Data Entry Records
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class ProjectData(Base):
    __tablename__ = "project_data"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    criteria_id = Column(Integer, ForeignKey("criteria.id"), nullable=False, index=True)

    # Activity data entered by L1
    activity_data = Column(Float, nullable=False)
    unit = Column(String(50))
    notes = Column(Text)

    # Evidence tracking
    has_evidence = Column(Integer, default=0)  # Count of evidence files

    # Metadata
    entered_by = Column(Integer, ForeignKey("users.id"))
    entered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="project_data")
    criteria = relationship("Criteria", back_populates="project_data")
    calculations = relationship("Calculation", back_populates="project_data", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProjectData(id={self.id}, project_id={self.project_id}, criteria_id={self.criteria_id})>"
