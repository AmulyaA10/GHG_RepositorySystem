"""
Evidence Model - File Metadata
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    criteria_id = Column(Integer, ForeignKey("criteria.id"), nullable=False, index=True)

    # File details
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # Relative path from storage base
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_type = Column(String(50))  # Extension

    # Metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="evidence")
    criteria = relationship("Criteria", back_populates="evidence")

    def __repr__(self):
        return f"<Evidence(id={self.id}, filename='{self.filename}')>"
