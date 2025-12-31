"""
Criteria Model - Master data for 23 GHG categories
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from core.db import Base

class Criteria(Base):
    __tablename__ = "criteria"

    id = Column(Integer, primary_key=True, index=True)
    criteria_number = Column(Integer, unique=True, nullable=False, index=True)
    scope = Column(String(20), nullable=False, index=True)  # Scope 1, Scope 2, Scope 3
    category = Column(String(255), nullable=False)
    subcategory = Column(String(255))
    description = Column(Text)
    unit = Column(String(50))  # kg, liters, kWh, km, tonnes, etc.
    is_active = Column(Boolean, default=True, nullable=False)

    # Help text for data entry
    help_text = Column(Text)
    example = Column(String(255))

    # Relationships
    project_data = relationship("ProjectData", back_populates="criteria")
    calculations = relationship("Calculation", back_populates="criteria")
    evidence = relationship("Evidence", back_populates="criteria")

    def __repr__(self):
        return f"<Criteria(id={self.id}, number={self.criteria_number}, category='{self.category}')>"
