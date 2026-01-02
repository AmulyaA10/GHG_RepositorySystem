"""
Project Model - Main submission entity
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Index
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

    # Timestamps (indexed for sorting and filtering)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    submitted_at = Column(DateTime, index=True)
    calculated_at = Column(DateTime, index=True)
    reviewed_at = Column(DateTime, index=True)
    approved_at = Column(DateTime, index=True)
    locked_at = Column(DateTime, index=True)

    # Calculated totals (populated by L2)
    total_scope1 = Column(Float, default=0.0)
    total_scope2 = Column(Float, default=0.0)
    total_scope3 = Column(Float, default=0.0)
    total_emissions = Column(Float, default=0.0)

    # Relationships - using lazy loading to prevent N+1 queries
    created_by_user = relationship("User", back_populates="projects", foreign_keys=[created_by], lazy='select')
    project_data = relationship("ProjectData", back_populates="project", cascade="all, delete-orphan", lazy='select')
    calculations = relationship("Calculation", back_populates="project", cascade="all, delete-orphan", lazy='select')
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan", lazy='select')
    approvals = relationship("Approval", back_populates="project", cascade="all, delete-orphan", lazy='select')
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan", lazy='select')
    evidence = relationship("Evidence", back_populates="project", cascade="all, delete-orphan", lazy='select')

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_project_status_year', 'status', 'reporting_year'),
        Index('idx_project_created_by_status', 'created_by', 'status'),
        Index('idx_project_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', status='{self.status}')>"
