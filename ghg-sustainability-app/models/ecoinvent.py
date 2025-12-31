"""
Ecoinvent Model - Emission Factors Database
"""
from sqlalchemy import Column, Integer, String, Text, Float, Index
from sqlalchemy.orm import relationship
from core.db import Base

class Ecoinvent(Base):
    __tablename__ = "ecoinvent"

    id = Column(Integer, primary_key=True, index=True)

    # Factor identification
    factor_name = Column(String(500), nullable=False)
    category = Column(String(255), nullable=False, index=True)
    subcategory = Column(String(255), index=True)
    scope = Column(String(20), nullable=False, index=True)

    # Emission factor value
    emission_factor = Column(Float, nullable=False)  # kgCO2e per unit
    unit = Column(String(100), nullable=False)  # per kWh, per kg, per km, etc.

    # Additional details
    gwp = Column(Float, default=1.0)
    region = Column(String(100), index=True)  # Geographic region
    source = Column(String(255))  # Data source reference
    description = Column(Text)
    year = Column(Integer, index=True)  # Reference year

    # Search optimization
    search_text = Column(Text)  # Concatenated searchable text

    def __repr__(self):
        return f"<Ecoinvent(id={self.id}, name='{self.factor_name}')>"

    # Create composite index for full-text search using pg_trgm
    __table_args__ = (
        Index('idx_ecoinvent_search', 'search_text', postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'}),
        Index('idx_ecoinvent_category_scope', 'category', 'scope'),
    )
