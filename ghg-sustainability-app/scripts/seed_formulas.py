"""
Seed Calculation Formulas
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_db
from models import Formula
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_formulas():
    """Create standard calculation formulas"""
    db = next(get_db())

    try:
        # Check if formulas already exist
        existing_count = db.query(Formula).count()

        if existing_count > 0:
            logger.info(f"Formulas already exist ({existing_count} found). Skipping...")
            return

        # Standard formulas
        formulas_data = [
            {
                "name": "Standard Emissions Calculation",
                "scope": "All",
                "category": "General",
                "formula_text": "Emissions (tCO2e) = Activity Data × Emission Factor × GWP × Unit Conversion ÷ 1000",
                "formula_expression": "AD × EF × GWP × UC ÷ 1000",
                "parameters": {
                    "AD": "Activity Data (quantity of activity)",
                    "EF": "Emission Factor (kgCO2e per unit)",
                    "GWP": "Global Warming Potential",
                    "UC": "Unit Conversion Factor"
                },
                "description": "Standard formula for calculating GHG emissions across all scopes",
                "example": "100 liters diesel × 2.68 kgCO2e/liter × 1.0 × 1.0 ÷ 1000 = 0.268 tCO2e"
            },
            {
                "name": "Scope 1 Stationary Combustion",
                "scope": "Scope 1",
                "category": "Stationary Combustion",
                "formula_text": "Emissions = Fuel Quantity × Fuel Emission Factor",
                "formula_expression": "FQ × FEF",
                "parameters": {
                    "FQ": "Fuel Quantity (liters, kg, m3)",
                    "FEF": "Fuel-specific Emission Factor"
                },
                "description": "Calculate emissions from burning fuels in stationary equipment",
                "example": "1000 liters diesel × 2.68 kgCO2e/liter = 2.68 tCO2e"
            },
            {
                "name": "Scope 2 Electricity",
                "scope": "Scope 2",
                "category": "Purchased Electricity",
                "formula_text": "Emissions = Electricity Consumption × Grid Emission Factor",
                "formula_expression": "EC × GEF",
                "parameters": {
                    "EC": "Electricity Consumption (kWh)",
                    "GEF": "Grid Emission Factor (kgCO2e/kWh)"
                },
                "description": "Calculate emissions from purchased electricity based on grid factors",
                "example": "10000 kWh × 0.5 kgCO2e/kWh = 5.0 tCO2e"
            },
            {
                "name": "Scope 3 Transportation",
                "scope": "Scope 3",
                "category": "Transportation",
                "formula_text": "Emissions = Distance × Weight × Transport Emission Factor",
                "formula_expression": "D × W × TEF",
                "parameters": {
                    "D": "Distance (km)",
                    "W": "Weight (tonnes)",
                    "TEF": "Transport Mode Emission Factor (kgCO2e/tonne-km)"
                },
                "description": "Calculate emissions from freight transportation",
                "example": "500 km × 10 tonnes × 0.062 kgCO2e/tonne-km = 0.31 tCO2e"
            },
            {
                "name": "Scope 3 Waste Disposal",
                "scope": "Scope 3",
                "category": "Waste Disposal",
                "formula_text": "Emissions = Waste Quantity × Disposal Method Factor",
                "formula_expression": "WQ × DMF",
                "parameters": {
                    "WQ": "Waste Quantity (tonnes)",
                    "DMF": "Disposal Method Factor (kgCO2e/tonne)"
                },
                "description": "Calculate emissions from waste disposal by method",
                "example": "50 tonnes × 500 kgCO2e/tonne (landfill) = 25 tCO2e"
            }
        ]

        # Create formulas
        for formula_data in formulas_data:
            formula = Formula(
                name=formula_data["name"],
                scope=formula_data["scope"],
                category=formula_data["category"],
                formula_text=formula_data["formula_text"],
                formula_expression=formula_data["formula_expression"],
                parameters=formula_data["parameters"],
                description=formula_data["description"],
                example=formula_data["example"],
                is_active=True
            )

            db.add(formula)
            logger.info(f"Created formula: {formula_data['name']}")

        db.commit()
        logger.info(f"✅ Successfully created {len(formulas_data)} formulas")

    except Exception as e:
        logger.error(f"Error seeding formulas: {e}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_formulas()
