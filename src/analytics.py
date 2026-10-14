import pandas as pd
from typing import Dict, Any


def calculate_summary_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate summary KPIs for energy consumption dataset."""
    total_col = "Total" if "Total" in df.columns else "total"
    date_col = "Date" if "Date" in df.columns else "date"

    total = float(df[total_col].sum())
    mean_val = float(df[total_col].mean())
    peak_idx = df[total_col].idxmax()
    min_idx = df[total_col].idxmin()

    return {
        "total_kwh": total,
        "average_daily_kwh": mean_val,
        "peak_kwh": float(df.loc[peak_idx, total_col]),
        "peak_date": str(df.loc[peak_idx, date_col]),
        "min_kwh": float(df.loc[min_idx, total_col]),
        "min_date": str(df.loc[min_idx, date_col]),
        "records_count": len(df)
    }
