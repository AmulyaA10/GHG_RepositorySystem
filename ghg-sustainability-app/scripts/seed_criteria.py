"""
Seed GHG Criteria (23 Categories)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_db
from models import Criteria
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_criteria():
    """Create 23 GHG protocol criteria"""
    db = next(get_db())

    try:
        # Check if criteria already exist
        existing_count = db.query(Criteria).count()

        if existing_count > 0:
            logger.info(f"Criteria already exist ({existing_count} found). Skipping...")
            return

        # 23 GHG Protocol Categories (based on Excel file)
        criteria_data = [
            # Scope 1 - Direct Emissions
            {"number": 1, "scope": "Scope 1", "category": "Stationary Combustion", "subcategory": "Fuel consumption in boilers, furnaces", "unit": "liters/kg", "help_text": "Enter total fuel consumed in stationary equipment"},
            {"number": 2, "scope": "Scope 1", "category": "Mobile Combustion", "subcategory": "Company-owned vehicles", "unit": "liters", "help_text": "Enter fuel used by company vehicles"},
            {"number": 3, "scope": "Scope 1", "category": "Process Emissions", "subcategory": "Industrial processes", "unit": "kg", "help_text": "Emissions from chemical reactions, manufacturing processes"},
            {"number": 4, "scope": "Scope 1", "category": "Fugitive Emissions", "subcategory": "Refrigerants, AC systems", "unit": "kg", "help_text": "Leakage from refrigeration and AC systems"},
            {"number": 5, "scope": "Scope 1", "category": "Land Use, Land-Use Change, Forestry (LULUCF)", "subcategory": "Forestry activities", "unit": "hectares", "help_text": "Carbon sequestration or emissions from land use"},

            # Scope 2 - Indirect Emissions (Energy)
            {"number": 6, "scope": "Scope 2", "category": "Purchased Electricity", "subcategory": "Grid electricity consumption", "unit": "kWh", "help_text": "Enter total electricity consumed from grid"},
            {"number": 7, "scope": "Scope 2", "category": "Purchased Heat/Steam/Cooling", "subcategory": "District heating/cooling", "unit": "GJ", "help_text": "Energy purchased for heating or cooling"},

            # Scope 3 - Other Indirect Emissions
            {"number": 8, "scope": "Scope 3", "category": "Upstream Transportation", "subcategory": "Inbound logistics", "unit": "tonne-km", "help_text": "Transportation of purchased goods to facility"},
            {"number": 9, "scope": "Scope 3", "category": "Downstream Transportation", "subcategory": "Outbound logistics", "unit": "tonne-km", "help_text": "Transportation of products to customers"},
            {"number": 10, "scope": "Scope 3", "category": "Business Travel", "subcategory": "Employee travel", "unit": "km", "help_text": "Air, rail, and road travel by employees"},
            {"number": 11, "scope": "Scope 3", "category": "Employee Commuting", "subcategory": "Daily commute", "unit": "km", "help_text": "Employee transportation to/from work"},
            {"number": 12, "scope": "Scope 3", "category": "Purchased Goods and Services", "subcategory": "Raw materials, supplies", "unit": "USD", "help_text": "Emissions from production of purchased items"},
            {"number": 13, "scope": "Scope 3", "category": "Capital Goods", "subcategory": "Equipment, buildings", "unit": "USD", "help_text": "Emissions from production of capital equipment"},
            {"number": 14, "scope": "Scope 3", "category": "Waste Generated in Operations", "subcategory": "Solid waste disposal", "unit": "tonnes", "help_text": "Waste sent to landfill, incineration, recycling"},
            {"number": 15, "scope": "Scope 3", "category": "Upstream Leased Assets", "subcategory": "Leased facilities", "unit": "m2", "help_text": "Emissions from operation of leased assets"},
            {"number": 16, "scope": "Scope 3", "category": "Downstream Leased Assets", "subcategory": "Assets leased to others", "unit": "m2", "help_text": "Emissions from assets company leases to others"},
            {"number": 17, "scope": "Scope 3", "category": "Processing of Sold Products", "subcategory": "Intermediate products", "unit": "tonnes", "help_text": "Processing of intermediate products by third parties"},
            {"number": 18, "scope": "Scope 3", "category": "Use of Sold Products", "subcategory": "Product lifetime emissions", "unit": "units", "help_text": "Emissions during customer use of products"},
            {"number": 19, "scope": "Scope 3", "category": "End-of-Life Treatment", "subcategory": "Product disposal", "unit": "tonnes", "help_text": "Disposal and recycling of sold products"},
            {"number": 20, "scope": "Scope 3", "category": "Franchises", "subcategory": "Franchise operations", "unit": "locations", "help_text": "Emissions from franchised operations"},
            {"number": 21, "scope": "Scope 3", "category": "Investments", "subcategory": "Investment portfolio", "unit": "USD", "help_text": "Emissions from investments and financial assets"},
            {"number": 22, "scope": "Scope 3", "category": "Upstream Fuel and Energy", "subcategory": "Extraction, production", "unit": "kWh", "help_text": "Emissions from fuel/energy production"},
            {"number": 23, "scope": "Scope 3", "category": "Water Consumption", "subcategory": "Municipal water", "unit": "m3", "help_text": "Water supply and treatment emissions"}
        ]

        # Create criteria records
        for criteria in criteria_data:
            criterion = Criteria(
                criteria_number=criteria["number"],
                scope=criteria["scope"],
                category=criteria["category"],
                subcategory=criteria.get("subcategory"),
                description=f"{criteria['scope']} - {criteria['category']}",
                unit=criteria.get("unit"),
                help_text=criteria.get("help_text"),
                is_active=True
            )

            db.add(criterion)
            logger.info(f"Created criterion {criteria['number']}: {criteria['category']}")

        db.commit()
        logger.info(f"✅ Successfully created {len(criteria_data)} criteria")

    except Exception as e:
        logger.error(f"Error seeding criteria: {e}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_criteria()
