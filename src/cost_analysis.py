DEFAULT_TARIFF_INR_PER_KWH = 8.50  # Commercial / Educational HT tariff in INR

def calculate_energy_cost(kwh: float, tariff: float = DEFAULT_TARIFF_INR_PER_KWH) -> float:
    """Calculate estimated electrical utility cost in INR."""
    return round(kwh * tariff, 2)
