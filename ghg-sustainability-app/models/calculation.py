"""
Calculation Model - L2 Calculation Results
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    criteria_id = Column(Integer, ForeignKey("criteria.id"), nullable=False, index=True)
    project_data_id = Column(Integer, ForeignKey("project_data.id"), nullable=False, index=True)

    # Calculation inputs
    activity_data = Column(Float, nullable=False)
    emission_factor = Column(Float, nullable=False)
    emission_factor_source = Column(String(255))  # Ecoinvent ID or manual entry
    gwp = Column(Float, default=1.0)
    unit_conversion = Column(Float, default=1.0)

    # Calculation results
    emissions_kg = Column(Float, nullable=False)
    emissions_tco2e = Column(Float, nullable=False)

    # Scope and category
    scope = Column(String(20), nullable=False, index=True)
    category = Column(String(255), nullable=False)

    # Formula details
    formula_used = Column(String(255))
    calculation_breakdown = Column(JSON)  # Stores complete calculation details

    # Metadata
    calculated_by = Column(Integer, ForeignKey("users.id"))
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)

    # Relationships - using lazy loading to prevent N+1 queries
    project = relationship("Project", back_populates="calculations", lazy='select')
    criteria = relationship("Criteria", back_populates="calculations", lazy='select')
    project_data = relationship("ProjectData", back_populates="calculations", lazy='select')

    def __repr__(self):
        return f"<Calculation(id={self.id}, emissions={self.emissions_tco2e} tCO2e)>"
