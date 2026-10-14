import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Campus Energy Consumption Analytics System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "smart_energy_db"
    ENERGY_COLLECTION: str = "energy_records"
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",      # Streamlit default
        "http://127.0.0.1:8501",
        "http://localhost:3000",      # React/Next.js default
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Energy Analytics Parameters (Standard Defensible Benchmarks)
    # CEA (Central Electricity Authority, India) CO2 Baseline database ~0.716 kg CO2/kWh for Indian grid
    GRID_EMISSION_FACTOR_KG_CO2_PER_KWH: float = 0.72
    # Typical Commercial/Educational High Tension (HT) Tariff in INR (₹) per kWh
    DEFAULT_TARIFF_INR_PER_KWH: float = 8.50
    
    # Data path default
    DEFAULT_DATASET_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "preprocessed_energy.csv"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
