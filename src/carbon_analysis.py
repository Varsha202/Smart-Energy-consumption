GRID_EMISSION_FACTOR_KG_CO2_PER_KWH = 0.72  # Indian Central Electricity Authority Baseline

def calculate_carbon_emissions(kwh: float, factor: float = GRID_EMISSION_FACTOR_KG_CO2_PER_KWH) -> float:
    """Calculate carbon emissions in kg CO2 from electricity consumption in kWh."""
    return round(kwh * factor, 2)
