import re
from typing import Dict, Any, List, Tuple
import pandas as pd
from datetime import datetime


def parse_date(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD."""
    clean = str(date_str).strip()
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", clean):
        parts = clean.split(".")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return clean


def load_and_clean_data(file_path: str) -> pd.DataFrame:
    """Load energy CSV dataset, format dates, and sort chronologically."""
    df = pd.read_csv(file_path)
    df["Date"] = df["Date"].apply(parse_date)
    df["date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df
