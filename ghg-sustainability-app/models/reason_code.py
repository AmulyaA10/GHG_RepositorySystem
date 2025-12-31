"""
ReasonCode Model - Review Rejection Reasons
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from core.db import Base

class ReasonCode(Base):
    __tablename__ = "reason_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), index=True)  # Data Quality, Calculation Error, Evidence Missing, etc.
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ReasonCode(id={self.id}, code='{self.code}')>"
