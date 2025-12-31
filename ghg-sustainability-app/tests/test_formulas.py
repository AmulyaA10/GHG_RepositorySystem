"""
Test Formula Engine
"""
import pytest
from core.formulas import FormulaEngine

def test_basic_emissions_calculation():
    """Test basic emissions calculation formula"""
    result = FormulaEngine.calculate_emissions(
        activity_data=100.0,  # 100 liters
        emission_factor=2.68,  # kgCO2e per liter
        gwp=1.0,
        unit_conversion=1.0
    )

    # Expected: 100 × 2.68 × 1.0 × 1.0 ÷ 1000 = 0.268 tCO2e
    assert result['emissions_tco2e'] == 0.268
    assert result['emissions_kg'] == 268.0
    assert result['activity_data'] == 100.0
    assert result['emission_factor'] == 2.68
    assert 'formula' in result
    assert 'calculation' in result

def test_emissions_with_gwp():
    """Test emissions calculation with GWP factor"""
    result = FormulaEngine.calculate_emissions(
        activity_data=10.0,  # 10 kg refrigerant
        emission_factor=1.0,  # base factor
        gwp=1430.0,  # R-134a GWP
        unit_conversion=1.0
    )

    # Expected: 10 × 1.0 × 1430 × 1.0 ÷ 1000 = 14.3 tCO2e
    assert result['emissions_tco2e'] == 14.3
    assert result['gwp'] == 1430.0

def test_emissions_with_unit_conversion():
    """Test emissions with unit conversion"""
    result = FormulaEngine.calculate_emissions(
        activity_data=1000.0,  # 1000 units
        emission_factor=0.5,
        gwp=1.0,
        unit_conversion=0.001  # Convert to proper units
    )

    # Expected: 1000 × 0.5 × 1.0 × 0.001 ÷ 1000 = 0.0005 tCO2e
    assert result['emissions_tco2e'] == 0.0005

def test_scope1_stationary_combustion():
    """Test Scope 1 stationary combustion calculation"""
    result = FormulaEngine.calculate_scope1_stationary_combustion(
        fuel_quantity=1000.0,  # 1000 liters
        fuel_type="Diesel",
        emission_factor=2.68,  # kgCO2e/liter
        ncv=36.0  # Net Calorific Value
    )

    assert result['emissions_tco2e'] == 2.68
    assert result['scope'] == "Scope 1"
    assert result['category'] == "Stationary Combustion"
    assert result['fuel_type'] == "Diesel"
    assert 'energy_content_gj' in result

def test_scope2_electricity():
    """Test Scope 2 electricity calculation"""
    result = FormulaEngine.calculate_scope2_electricity(
        electricity_kwh=10000.0,
        grid_emission_factor=0.5,  # kgCO2e/kWh
        location="USA"
    )

    # Expected: 10000 × 0.5 ÷ 1000 = 5.0 tCO2e
    assert result['emissions_tco2e'] == 5.0
    assert result['scope'] == "Scope 2"
    assert result['category'] == "Purchased Electricity"
    assert result['location'] == "USA"

def test_scope3_transport_passenger():
    """Test Scope 3 passenger transport"""
    result = FormulaEngine.calculate_scope3_transport(
        distance_km=500.0,
        transport_mode="Car",
        emission_factor=0.171  # kgCO2e/km
    )

    # Expected: 500 × 0.171 ÷ 1000 = 0.0855 tCO2e
    assert result['emissions_tco2e'] == 0.0855
    assert result['scope'] == "Scope 3"
    assert result['distance_km'] == 500.0

def test_scope3_transport_freight():
    """Test Scope 3 freight transport with weight"""
    result = FormulaEngine.calculate_scope3_transport(
        distance_km=500.0,
        transport_mode="Truck",
        emission_factor=0.062,  # kgCO2e/tonne-km
        weight_tonnes=10.0
    )

    # Expected: 500 km × 10 tonnes × 0.062 ÷ 1000 = 0.31 tCO2e
    assert result['emissions_tco2e'] == 0.31
    assert result['tonne_km'] == 5000.0
    assert result['weight_tonnes'] == 10.0

def test_scope3_waste():
    """Test Scope 3 waste disposal"""
    result = FormulaEngine.calculate_scope3_waste(
        waste_quantity_tonnes=50.0,
        waste_type="Municipal Solid Waste",
        disposal_method="Landfill",
        emission_factor=467.0  # kgCO2e/tonne
    )

    # Expected: 50 × 467 ÷ 1000 = 23.35 tCO2e
    assert result['emissions_tco2e'] == 23.35
    assert result['scope'] == "Scope 3"
    assert result['waste_type'] == "Municipal Solid Waste"
    assert result['disposal_method'] == "Landfill"

def test_aggregate_emissions():
    """Test emissions aggregation"""
    calculations = [
        {'scope': 'Scope 1', 'emissions_tco2e': 10.5},
        {'scope': 'Scope 1', 'emissions_tco2e': 5.5},
        {'scope': 'Scope 2', 'emissions_tco2e': 20.0},
        {'scope': 'Scope 3', 'emissions_tco2e': 15.0},
        {'scope': 'Scope 3', 'emissions_tco2e': 8.5}
    ]

    result = FormulaEngine.aggregate_emissions(calculations)

    assert result['Scope 1'] == 16.0
    assert result['Scope 2'] == 20.0
    assert result['Scope 3'] == 23.5
    assert result['Total'] == 59.5
    assert result['breakdown_count'] == 5

def test_zero_emissions():
    """Test calculation with zero activity data"""
    result = FormulaEngine.calculate_emissions(
        activity_data=0.0,
        emission_factor=2.68,
        gwp=1.0,
        unit_conversion=1.0
    )

    assert result['emissions_tco2e'] == 0.0
    assert result['emissions_kg'] == 0.0

def test_precision():
    """Test calculation precision with Decimal"""
    result = FormulaEngine.calculate_emissions(
        activity_data=123.456,
        emission_factor=0.789,
        gwp=1.0,
        unit_conversion=1.0
    )

    # Should be rounded to 4 decimal places
    assert isinstance(result['emissions_tco2e'], float)
    # 123.456 × 0.789 ÷ 1000 = 0.0974 (rounded to 4 decimals)
    assert result['emissions_tco2e'] == 0.0974
