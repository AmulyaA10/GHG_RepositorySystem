"""
Seed Ecoinvent Emission Factors (Sample Data)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_db
from models import Ecoinvent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_ecoinvent():
    """Create sample ecoinvent emission factors"""
    db = next(get_db())

    try:
        # Check if ecoinvent data already exists
        existing_count = db.query(Ecoinvent).count()

        if existing_count > 0:
            logger.info(f"Ecoinvent data already exists ({existing_count} records found). Skipping...")
            return

        # Sample emission factors (representative data)
        ecoinvent_data = [
            # Scope 1 - Fuels
            {"name": "Diesel combustion, stationary", "category": "Fuel", "subcategory": "Diesel", "scope": "Scope 1", "factor": 2.68, "unit": "kgCO2e/liter", "region": "Global", "year": 2023},
            {"name": "Natural gas combustion, stationary", "category": "Fuel", "subcategory": "Natural Gas", "scope": "Scope 1", "factor": 2.02, "unit": "kgCO2e/m3", "region": "Global", "year": 2023},
            {"name": "LPG combustion, stationary", "category": "Fuel", "subcategory": "LPG", "scope": "Scope 1", "factor": 1.51, "unit": "kgCO2e/kg", "region": "Global", "year": 2023},
            {"name": "Coal combustion, stationary", "category": "Fuel", "subcategory": "Coal", "scope": "Scope 1", "factor": 2.42, "unit": "kgCO2e/kg", "region": "Global", "year": 2023},
            {"name": "Petrol/Gasoline combustion, mobile", "category": "Fuel", "subcategory": "Petrol", "scope": "Scope 1", "factor": 2.31, "unit": "kgCO2e/liter", "region": "Global", "year": 2023},
            {"name": "Diesel combustion, mobile", "category": "Fuel", "subcategory": "Diesel", "scope": "Scope 1", "factor": 2.68, "unit": "kgCO2e/liter", "region": "Global", "year": 2023},

            # Scope 1 - Refrigerants
            {"name": "R-134a refrigerant", "category": "Refrigerant", "subcategory": "HFC", "scope": "Scope 1", "factor": 1430, "unit": "kgCO2e/kg", "region": "Global", "year": 2023, "gwp": 1430},
            {"name": "R-410A refrigerant", "category": "Refrigerant", "subcategory": "HFC", "scope": "Scope 1", "factor": 2088, "unit": "kgCO2e/kg", "region": "Global", "year": 2023, "gwp": 2088},

            # Scope 2 - Electricity (various regions)
            {"name": "Electricity, grid mix, USA", "category": "Electricity", "subcategory": "Grid", "scope": "Scope 2", "factor": 0.417, "unit": "kgCO2e/kWh", "region": "USA", "year": 2023},
            {"name": "Electricity, grid mix, EU-27", "category": "Electricity", "subcategory": "Grid", "scope": "Scope 2", "factor": 0.295, "unit": "kgCO2e/kWh", "region": "EU-27", "year": 2023},
            {"name": "Electricity, grid mix, India", "category": "Electricity", "subcategory": "Grid", "scope": "Scope 2", "factor": 0.708, "unit": "kgCO2e/kWh", "region": "India", "year": 2023},
            {"name": "Electricity, grid mix, China", "category": "Electricity", "subcategory": "Grid", "scope": "Scope 2", "factor": 0.581, "unit": "kgCO2e/kWh", "region": "China", "year": 2023},
            {"name": "Electricity, grid mix, UK", "category": "Electricity", "subcategory": "Grid", "scope": "Scope 2", "factor": 0.233, "unit": "kgCO2e/kWh", "region": "UK", "year": 2023},
            {"name": "Electricity, renewable energy", "category": "Electricity", "subcategory": "Renewable", "scope": "Scope 2", "factor": 0.024, "unit": "kgCO2e/kWh", "region": "Global", "year": 2023},

            # Scope 3 - Transportation
            {"name": "Freight transport, truck, diesel, >32t", "category": "Transport", "subcategory": "Road Freight", "scope": "Scope 3", "factor": 0.062, "unit": "kgCO2e/tonne-km", "region": "Global", "year": 2023},
            {"name": "Freight transport, train, diesel", "category": "Transport", "subcategory": "Rail Freight", "scope": "Scope 3", "factor": 0.022, "unit": "kgCO2e/tonne-km", "region": "Global", "year": 2023},
            {"name": "Freight transport, ship, container", "category": "Transport", "subcategory": "Sea Freight", "scope": "Scope 3", "factor": 0.012, "unit": "kgCO2e/tonne-km", "region": "Global", "year": 2023},
            {"name": "Freight transport, aircraft", "category": "Transport", "subcategory": "Air Freight", "scope": "Scope 3", "factor": 0.602, "unit": "kgCO2e/tonne-km", "region": "Global", "year": 2023},
            {"name": "Passenger transport, car, average", "category": "Transport", "subcategory": "Passenger Car", "scope": "Scope 3", "factor": 0.171, "unit": "kgCO2e/km", "region": "Global", "year": 2023},
            {"name": "Passenger transport, bus", "category": "Transport", "subcategory": "Bus", "scope": "Scope 3", "factor": 0.089, "unit": "kgCO2e/passenger-km", "region": "Global", "year": 2023},
            {"name": "Passenger transport, train, diesel", "category": "Transport", "subcategory": "Rail", "scope": "Scope 3", "factor": 0.041, "unit": "kgCO2e/passenger-km", "region": "Global", "year": 2023},
            {"name": "Passenger transport, aircraft, short-haul", "category": "Transport", "subcategory": "Aviation", "scope": "Scope 3", "factor": 0.158, "unit": "kgCO2e/passenger-km", "region": "Global", "year": 2023},
            {"name": "Passenger transport, aircraft, long-haul", "category": "Transport", "subcategory": "Aviation", "scope": "Scope 3", "factor": 0.115, "unit": "kgCO2e/passenger-km", "region": "Global", "year": 2023},

            # Scope 3 - Waste
            {"name": "Waste treatment, municipal solid waste, landfill", "category": "Waste", "subcategory": "Landfill", "scope": "Scope 3", "factor": 467, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Waste treatment, municipal solid waste, incineration", "category": "Waste", "subcategory": "Incineration", "scope": "Scope 3", "factor": 421, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Waste treatment, recycling, average", "category": "Waste", "subcategory": "Recycling", "scope": "Scope 3", "factor": 21, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Waste treatment, composting", "category": "Waste", "subcategory": "Composting", "scope": "Scope 3", "factor": 50, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},

            # Scope 3 - Water
            {"name": "Water supply, municipal", "category": "Water", "subcategory": "Supply", "scope": "Scope 3", "factor": 0.344, "unit": "kgCO2e/m3", "region": "Global", "year": 2023},
            {"name": "Wastewater treatment, municipal", "category": "Water", "subcategory": "Treatment", "scope": "Scope 3", "factor": 0.708, "unit": "kgCO2e/m3", "region": "Global", "year": 2023},

            # Scope 3 - Materials (sample)
            {"name": "Steel, average", "category": "Material", "subcategory": "Metal", "scope": "Scope 3", "factor": 1850, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Aluminum, primary", "category": "Material", "subcategory": "Metal", "scope": "Scope 3", "factor": 8900, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Concrete, average", "category": "Material", "subcategory": "Construction", "scope": "Scope 3", "factor": 295, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Paper, recycled", "category": "Material", "subcategory": "Paper", "scope": "Scope 3", "factor": 850, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023},
            {"name": "Plastic, average", "category": "Material", "subcategory": "Plastic", "scope": "Scope 3", "factor": 2500, "unit": "kgCO2e/tonne", "region": "Global", "year": 2023}
        ]

        # Create ecoinvent records
        for data in ecoinvent_data:
            # Create searchable text
            search_text = f"{data['name']} {data['category']} {data['subcategory']} {data['scope']} {data['region']}"

            ecoinvent = Ecoinvent(
                factor_name=data["name"],
                category=data["category"],
                subcategory=data["subcategory"],
                scope=data["scope"],
                emission_factor=data["factor"],
                unit=data["unit"],
                gwp=data.get("gwp", 1.0),
                region=data["region"],
                source="Ecoinvent v3.9",
                year=data["year"],
                search_text=search_text.lower()
            )

            db.add(ecoinvent)
            logger.info(f"Created ecoinvent factor: {data['name']}")

        db.commit()
        logger.info(f"✅ Successfully created {len(ecoinvent_data)} ecoinvent factors")

    except Exception as e:
        logger.error(f"Error seeding ecoinvent: {e}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_ecoinvent()
