"""
Project Model - Main submission entity
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=False, index=True)
    reporting_year = Column(Integer, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="DRAFT", index=True)
    description = Column(Text)

    # User tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_email = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime)
    calculated_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    approved_at = Column(DateTime)
    locked_at = Column(DateTime)

    # Calculated totals (populated by L2)
    total_scope1 = Column(Float, default=0.0)
    total_scope2 = Column(Float, default=0.0)
    total_scope3 = Column(Float, default=0.0)
    total_emissions = Column(Float, default=0.0)

    # Relationships
    created_by_user = relationship("User", back_populates="projects", foreign_keys=[created_by])
    project_data = relationship("ProjectData", back_populates="project", cascade="all, delete-orphan")
    calculations = relationship("Calculation", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', status='{self.status}')>"
