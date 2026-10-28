import os
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union, Any


def _resolve_data_path(filename: str, env_var: str) -> str:
    """Resolve data file path dynamically across repository root and backend directory."""
    env_override = os.getenv(env_var)
    if env_override and os.path.exists(env_override):
        return os.path.abspath(env_override)

    current_file_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app
    backend_root = os.path.dirname(current_file_dir)                # backend
    repo_root = os.path.dirname(backend_root)                      # repo root
    cwd = os.getcwd()

    candidates = [
        os.path.join(repo_root, "data", filename),
        os.path.join(backend_root, "data", filename),
        os.path.join(cwd, "data", filename),
        os.path.join(cwd, "backend", "data", filename),
        os.path.join(backend_root, filename),
    ]

    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)

    return os.path.join(repo_root, "data", filename)


def _resolve_env_file() -> str:
    """Resolve env file dynamically, prioritizing backend/.env then root .env."""
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_env = os.path.join(backend_root, ".env")
    if os.path.exists(backend_env):
        return os.path.abspath(backend_env)
    return ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Campus Energy Consumption Analytics System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "smart_energy_db"
    ENERGY_COLLECTION: str = "energy_records"
    TARIFF_COLLECTION: str = "tariff_settings"
    NOTIFICATION_COLLECTION: str = "notifications"
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS Configuration - defaults to local frontend; overridden in production by CORS_ORIGINS env var
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",      # React/Next.js default
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            origins = [i.strip() for i in v.split(",") if i.strip()]
            return origins if origins else ["http://localhost:3000"]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]
    
    # Energy Analytics Parameters (Standard Defensible Benchmarks)
    # CEA (Central Electricity Authority, India) CO2 Baseline database ~0.716 kg CO2/kWh for Indian grid
    GRID_EMISSION_FACTOR_KG_CO2_PER_KWH: float = 0.72
    # Typical Commercial/Educational High Tension (HT) Tariff in INR (₹) per kWh
    DEFAULT_TARIFF_INR_PER_KWH: float = 8.50
    
    # Dynamic Data path resolution (supports repo root and backend directory)
    DEFAULT_DATASET_PATH: str = _resolve_data_path("preprocessed_energy.csv", "DATASET_PATH")
    TARIFF_FALLBACK_FILE: str = _resolve_data_path("tariff_config.json", "TARIFF_CONFIG_PATH")

    class Config:
        env_file = _resolve_env_file()
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
