"""
User Model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, index=True)  # L1, L2, L3, L4
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships - using lazy loading to prevent N+1 queries
    projects = relationship("Project", back_populates="created_by_user", foreign_keys="Project.created_by", lazy='select')
    audit_logs = relationship("AuditLog", back_populates="user", lazy='select')
    reviews = relationship("Review", back_populates="reviewer", lazy='select')
    approvals = relationship("Approval", back_populates="approver", lazy='select')
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", lazy='select', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
