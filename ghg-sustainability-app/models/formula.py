"""
Formula Model - Calculation Formulas
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON
from core.db import Base

class Formula(Base):
    __tablename__ = "formulas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scope = Column(String(20), nullable=False, index=True)
    category = Column(String(255), nullable=False, index=True)

    # Formula definition
    formula_text = Column(Text, nullable=False)
    formula_expression = Column(String(500))  # e.g., "AD × EF × GWP ÷ 1000"
    parameters = Column(JSON)  # Parameter definitions

    # Usage instructions
    description = Column(Text)
    example = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Formula(id={self.id}, name='{self.name}')>"
