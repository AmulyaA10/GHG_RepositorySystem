"""
GHG Calculation Formula Engine
"""
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)

class FormulaEngine:
    """GHG Calculation Formula Engine"""

    @staticmethod
    def calculate_emissions(
        activity_data: float,
        emission_factor: float,
        gwp: float = 1.0,
        unit_conversion: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate GHG emissions using standard formula:
        Emissions (tCO2e) = Activity Data × Emission Factor × GWP × Unit Conversion

        Args:
            activity_data: Amount of activity (e.g., fuel consumed, distance traveled)
            emission_factor: Emission factor (kgCO2e per unit activity)
            gwp: Global Warming Potential (default 1.0 for CO2)
            unit_conversion: Unit conversion factor (default 1.0)

        Returns:
            Dict containing calculation breakdown
        """
        try:
            # Convert to Decimal for precise calculation
            ad = Decimal(str(activity_data))
            ef = Decimal(str(emission_factor))
            g = Decimal(str(gwp))
            uc = Decimal(str(unit_conversion))

            # Calculate emissions in kg
            emissions_kg = ad * ef * g * uc

            # Convert to tonnes (tCO2e)
            emissions_tonnes = emissions_kg / Decimal('1000')

            # Round to 4 decimal places
            emissions_tonnes = emissions_tonnes.quantize(
                Decimal('0.0001'),
                rounding=ROUND_HALF_UP
            )

            result = {
                "activity_data": float(ad),
                "emission_factor": float(ef),
                "gwp": float(g),
                "unit_conversion": float(uc),
                "emissions_kg": float(emissions_kg),
                "emissions_tco2e": float(emissions_tonnes),
                "formula": "Activity Data × Emission Factor × GWP × Unit Conversion ÷ 1000",
                "calculation": f"{float(ad)} × {float(ef)} × {float(g)} × {float(uc)} ÷ 1000 = {float(emissions_tonnes)} tCO2e"
            }

            logger.debug(f"Emission calculated: {result}")
            return result

        except Exception as e:
            logger.error(f"Error calculating emissions: {e}")
            raise ValueError(f"Calculation error: {e}")

    @staticmethod
    def calculate_scope1_stationary_combustion(
        fuel_quantity: float,
        fuel_type: str,
        emission_factor: float,
        ncv: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate Scope 1 emissions from stationary combustion

        Args:
            fuel_quantity: Quantity of fuel consumed
            fuel_type: Type of fuel (coal, natural gas, LPG, etc.)
            emission_factor: Emission factor for the fuel
            ncv: Net Calorific Value (optional, for energy content calculation)

        Returns:
            Dict containing calculation results
        """
        # Base calculation
        result = FormulaEngine.calculate_emissions(
            activity_data=fuel_quantity,
            emission_factor=emission_factor
        )

        result["fuel_type"] = fuel_type
        result["scope"] = "Scope 1"
        result["category"] = "Stationary Combustion"

        if ncv:
            energy_content = Decimal(str(fuel_quantity)) * Decimal(str(ncv))
            result["energy_content_gj"] = float(energy_content)

        return result

    @staticmethod
    def calculate_scope2_electricity(
        electricity_kwh: float,
        grid_emission_factor: float,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate Scope 2 emissions from purchased electricity

        Args:
            electricity_kwh: Electricity consumption in kWh
            grid_emission_factor: Grid emission factor (kgCO2e/kWh)
            location: Location/grid region (optional)

        Returns:
            Dict containing calculation results
        """
        result = FormulaEngine.calculate_emissions(
            activity_data=electricity_kwh,
            emission_factor=grid_emission_factor
        )

        result["scope"] = "Scope 2"
        result["category"] = "Purchased Electricity"
        result["location"] = location or "Not specified"

        return result

    @staticmethod
    def calculate_scope3_transport(
        distance_km: float,
        transport_mode: str,
        emission_factor: float,
        weight_tonnes: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate Scope 3 emissions from transportation

        Args:
            distance_km: Distance traveled in kilometers
            transport_mode: Mode of transport (road, rail, air, sea)
            emission_factor: Emission factor (kgCO2e per km or per tonne-km)
            weight_tonnes: Weight transported in tonnes (for freight)

        Returns:
            Dict containing calculation results
        """
        # If freight, calculate tonne-km
        if weight_tonnes:
            activity_data = distance_km * weight_tonnes
        else:
            activity_data = distance_km

        result = FormulaEngine.calculate_emissions(
            activity_data=activity_data,
            emission_factor=emission_factor
        )

        result["scope"] = "Scope 3"
        result["category"] = "Transportation"
        result["transport_mode"] = transport_mode
        result["distance_km"] = distance_km

        if weight_tonnes:
            result["weight_tonnes"] = weight_tonnes
            result["tonne_km"] = distance_km * weight_tonnes

        return result

    @staticmethod
    def calculate_scope3_waste(
        waste_quantity_tonnes: float,
        waste_type: str,
        disposal_method: str,
        emission_factor: float
    ) -> Dict[str, Any]:
        """
        Calculate Scope 3 emissions from waste disposal

        Args:
            waste_quantity_tonnes: Quantity of waste in tonnes
            waste_type: Type of waste (hazardous, non-hazardous, etc.)
            disposal_method: Disposal method (landfill, incineration, recycling)
            emission_factor: Emission factor for disposal method

        Returns:
            Dict containing calculation results
        """
        result = FormulaEngine.calculate_emissions(
            activity_data=waste_quantity_tonnes,
            emission_factor=emission_factor
        )

        result["scope"] = "Scope 3"
        result["category"] = "Waste Disposal"
        result["waste_type"] = waste_type
        result["disposal_method"] = disposal_method

        return result

    @staticmethod
    def aggregate_emissions(calculations: list) -> Dict[str, Any]:
        """
        Aggregate multiple emission calculations

        Args:
            calculations: List of calculation result dictionaries

        Returns:
            Dict containing aggregated results by scope
        """
        totals = {
            "Scope 1": Decimal('0'),
            "Scope 2": Decimal('0'),
            "Scope 3": Decimal('0'),
            "Total": Decimal('0')
        }

        for calc in calculations:
            scope = calc.get("scope", "Unknown")
            emissions = Decimal(str(calc.get("emissions_tco2e", 0)))

            if scope in totals:
                totals[scope] += emissions
            totals["Total"] += emissions

        # Convert to float and round
        result = {
            scope: float(value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
            for scope, value in totals.items()
        }

        result["breakdown_count"] = len(calculations)

        return result
