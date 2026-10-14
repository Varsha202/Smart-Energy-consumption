from datetime import datetime
from backend.app.models.schemas import parse_and_normalize_date

def format_date_iso(date_str: str) -> str:
    """Utility to normalize date to ISO YYYY-MM-DD."""
    return parse_and_normalize_date(date_str)
