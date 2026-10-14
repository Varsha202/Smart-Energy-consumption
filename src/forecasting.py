from backend.app.services.forecast_service import forecast_service

def generate_forecast():
    """Wrapper calling backend forecast service."""
    return forecast_service.generate_three_month_forecast()
