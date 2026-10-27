import json
import logging
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any

from ..config import settings
from ..database import db_manager, DatabaseUnavailableException
from ..models.schemas import (
    TariffSlab,
    TariffConfig,
    SlabCalculationDetail,
    TariffCalculationResult,
)

logger = logging.getLogger("energy_backend.tariff_service")

# Quantization constants
CENT = Decimal("0.01")
RATE_PRECISION = Decimal("0.0001")


def _to_decimal(val: Any) -> Decimal:
    """Helper to convert float, int, or string to Decimal safely."""
    return Decimal(str(val))


class TariffService:
    """
    Centralized service for progressive slab-based electricity tariff calculation,
    rate configuration, persistence, and profile management.
    """

    def __init__(self):
        self._cached_config: Optional[TariffConfig] = None
        self._load_or_init_config()

    @staticmethod
    def get_initial_slabs() -> List[TariffSlab]:
        """
        User-provided initial progressive slab structure:
        - 0–100 units: ₹0/unit (free units enabled)
        - 101–200 units: ₹4.70/unit
        - 201–400 units: ₹6.30/unit (within supplied 4.70-8.40 range)
        - 401–500 units: ₹8.00/unit (within supplied 6.30-8.40 range)
        - Above 500 units: ₹8.40/unit
        """
        return [
            TariffSlab(start_units=0.0, end_units=100.0, rate_per_unit=0.0, label="0 - 100 units (Free Tier)"),
            TariffSlab(start_units=100.0, end_units=200.0, rate_per_unit=4.70, label="101 - 200 units"),
            TariffSlab(start_units=200.0, end_units=400.0, rate_per_unit=6.30, label="201 - 400 units"),
            TariffSlab(start_units=400.0, end_units=500.0, rate_per_unit=8.00, label="401 - 500 units"),
            TariffSlab(start_units=500.0, end_units=None, rate_per_unit=8.40, label="Above 500 units"),
        ]

    def get_default_config(self, profile: str = "commercial") -> TariffConfig:
        """Construct standard default configuration for a given profile."""
        profile_lower = profile.lower()
        if profile_lower == "domestic":
            return TariffConfig(
                profile="domestic",
                billing_mode="progressive",
                free_units_enabled=True,
                free_units_limit=100.0,
                single_tier_rate=8.50,
                slabs=self.get_initial_slabs(),
                notes=(
                    "Domestic Profile: Progressive slab configuration with 100 free units. "
                    "Initial configuration parameters for modeling and analysis (not officially verified)."
                ),
            )
        elif profile_lower == "commercial":
            return TariffConfig(
                profile="commercial",
                billing_mode="progressive",
                free_units_enabled=True,
                free_units_limit=100.0,
                single_tier_rate=8.50,
                slabs=self.get_initial_slabs(),
                notes=(
                    "Commercial / Institutional Profile: Progressive slab configuration. "
                    "Initial configuration parameters for modeling and analysis (not officially verified)."
                ),
            )
        else:
            return TariffConfig(
                profile="custom",
                billing_mode="progressive",
                free_units_enabled=True,
                free_units_limit=100.0,
                single_tier_rate=8.50,
                slabs=self.get_initial_slabs(),
                notes="Custom Profile: User-defined progressive slabs and rate boundaries.",
            )

    def _load_or_init_config(self) -> None:
        """Load configuration from MongoDB or fallback JSON file, or initialize defaults."""
        # 1. Attempt MongoDB Atlas retrieval
        try:
            db = db_manager.get_database()
            col = db[settings.TARIFF_COLLECTION]
            doc = col.find_one({"_id": "active_tariff_config"})
            if doc and "config" in doc:
                self._cached_config = TariffConfig(**doc["config"])
                logger.info("Loaded active tariff configuration from MongoDB Atlas.")
                return
        except Exception as e:
            logger.info("MongoDB unavailable for tariff loading (%s); checking local fallback file.", str(e))

        # 2. Attempt Local Fallback JSON file retrieval
        if os.path.exists(settings.TARIFF_FALLBACK_FILE):
            try:
                with open(settings.TARIFF_FALLBACK_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cached_config = TariffConfig(**data)
                    logger.info("Loaded tariff configuration from local fallback file.")
                    return
            except Exception as e:
                logger.warning("Error reading local tariff fallback file: %s", str(e))

        # 3. Initialize default commercial progressive configuration
        self._cached_config = self.get_default_config("commercial")

    def _persist_config(self, config: TariffConfig) -> None:
        """Safely persist configuration to MongoDB Atlas and local fallback file."""
        config_dict = config.model_dump()

        # 1. Save to local fallback file
        try:
            os.makedirs(os.path.dirname(settings.TARIFF_FALLBACK_FILE), exist_ok=True)
            with open(settings.TARIFF_FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)
            logger.info("Saved tariff configuration to local fallback file.")
        except Exception as e:
            logger.warning("Could not write tariff fallback file: %s", str(e))

        # 2. Save to MongoDB if available
        try:
            db = db_manager.get_database()
            col = db[settings.TARIFF_COLLECTION]
            col.replace_one(
                {"_id": "active_tariff_config"},
                {"_id": "active_tariff_config", "config": config_dict},
                upsert=True,
            )
            logger.info("Successfully persisted active tariff configuration into MongoDB.")
        except Exception as e:
            logger.info("MongoDB unavailable for tariff persistence: %s (persisted to file cache).", str(e))

    def get_active_config(self) -> TariffConfig:
        """Return the current active tariff configuration."""
        if self._cached_config is None:
            self._load_or_init_config()
        return self._cached_config

    def update_config(self, new_config: TariffConfig) -> TariffConfig:
        """Validate and apply a new tariff configuration."""
        self._cached_config = new_config
        self._persist_config(new_config)
        return self._cached_config

    def reset_to_defaults(self, profile: str = "commercial") -> TariffConfig:
        """Reset configuration to initial defaults for specified profile."""
        default_cfg = self.get_default_config(profile)
        return self.update_config(default_cfg)

    def calculate_bill(
        self,
        consumption_kwh: float,
        config: Optional[TariffConfig] = None
    ) -> TariffCalculationResult:
        """
        Progressive decimal-safe electricity tariff calculation.
        Supports both progressive slab billing and single-tier flat rate billing.
        """
        if consumption_kwh < 0:
            raise ValueError("Consumption cannot be negative.")

        active_cfg = config or self.get_active_config()
        consumption_dec = _to_decimal(consumption_kwh)
        baseline_rate_dec = _to_decimal(settings.DEFAULT_TARIFF_INR_PER_KWH)
        baseline_cost_dec = (consumption_dec * baseline_rate_dec).quantize(CENT, rounding=ROUND_HALF_UP)

        # Handle 0 consumption boundary
        if consumption_dec == Decimal("0"):
            return TariffCalculationResult(
                total_consumption_kwh=0.0,
                total_bill_inr=0.0,
                effective_rate_per_kwh=0.0,
                billing_mode=active_cfg.billing_mode,
                profile=active_cfg.profile,
                free_units_applied=0.0,
                slab_breakdown=[],
                baseline_flat_cost_inr=0.0,
                cost_difference_inr=0.0,
                percentage_difference=0.0,
                notes=active_cfg.notes or "Zero consumption evaluated.",
            )

        # ---------------- SINGLE-TIER BILLING MODE ----------------
        if active_cfg.billing_mode == "single_tier":
            rate_dec = _to_decimal(active_cfg.single_tier_rate)
            total_bill_dec = (consumption_dec * rate_dec).quantize(CENT, rounding=ROUND_HALF_UP)
            effective_rate_dec = rate_dec.quantize(RATE_PRECISION, rounding=ROUND_HALF_UP)

            diff_dec = (total_bill_dec - baseline_cost_dec).quantize(CENT, rounding=ROUND_HALF_UP)
            pct_diff = float(((diff_dec / baseline_cost_dec) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)) if baseline_cost_dec > 0 else 0.0

            detail = SlabCalculationDetail(
                slab_index=1,
                start_units=0.0,
                end_units=None,
                rate_per_unit=float(rate_dec),
                units_in_slab=float(consumption_dec),
                slab_cost=float(total_bill_dec),
                label=f"Flat Rate (₹{active_cfg.single_tier_rate:.2f}/kWh)",
            )

            return TariffCalculationResult(
                total_consumption_kwh=round(float(consumption_dec), 2),
                total_bill_inr=float(total_bill_dec),
                effective_rate_per_kwh=float(effective_rate_dec),
                billing_mode="single_tier",
                profile=active_cfg.profile,
                free_units_applied=0.0,
                slab_breakdown=[detail],
                baseline_flat_cost_inr=float(baseline_cost_dec),
                cost_difference_inr=float(diff_dec),
                percentage_difference=pct_diff,
                notes=active_cfg.notes or "Single-tier flat rate calculation.",
            )

        # ---------------- PROGRESSIVE SLAB BILLING MODE ----------------
        total_bill_dec = Decimal("0.00")
        slab_breakdown: List[SlabCalculationDetail] = []
        free_units_applied = Decimal("0.0")

        for idx, slab in enumerate(active_cfg.slabs, start=1):
            start_dec = _to_decimal(slab.start_units)
            end_dec = _to_decimal(slab.end_units) if slab.end_units is not None else None

            # Check if consumption reaches this slab
            if consumption_dec <= start_dec:
                units_in_slab = Decimal("0.0")
            elif end_dec is None:
                # Unlimited upper slab
                units_in_slab = consumption_dec - start_dec
            else:
                units_in_slab = min(consumption_dec, end_dec) - start_dec

            # Effective slab rate (considering free units on first slab)
            if idx == 1 and active_cfg.free_units_enabled:
                free_limit = _to_decimal(active_cfg.free_units_limit)
                free_units_applied = min(units_in_slab, free_limit)
                # First slab charged at zero
                rate_dec = Decimal("0.00")
            else:
                rate_dec = _to_decimal(slab.rate_per_unit)

            slab_cost_dec = (units_in_slab * rate_dec).quantize(CENT, rounding=ROUND_HALF_UP)
            total_bill_dec += slab_cost_dec

            slab_breakdown.append(
                SlabCalculationDetail(
                    slab_index=idx,
                    start_units=float(start_dec),
                    end_units=float(end_dec) if end_dec is not None else None,
                    rate_per_unit=float(rate_dec),
                    units_in_slab=round(float(units_in_slab), 2),
                    slab_cost=float(slab_cost_dec),
                    label=slab.label or (
                        f"{slab.start_units:.0f} - {slab.end_units:.0f} kWh"
                        if slab.end_units is not None
                        else f"Above {slab.start_units:.0f} kWh"
                    ),
                )
            )

        total_bill_dec = total_bill_dec.quantize(CENT, rounding=ROUND_HALF_UP)
        effective_rate_dec = (
            (total_bill_dec / consumption_dec).quantize(RATE_PRECISION, rounding=ROUND_HALF_UP)
            if consumption_dec > 0
            else Decimal("0.00")
        )

        diff_dec = (total_bill_dec - baseline_cost_dec).quantize(CENT, rounding=ROUND_HALF_UP)
        pct_diff = float(((diff_dec / baseline_cost_dec) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)) if baseline_cost_dec > 0 else 0.0

        return TariffCalculationResult(
            total_consumption_kwh=round(float(consumption_dec), 2),
            total_bill_inr=float(total_bill_dec),
            effective_rate_per_kwh=float(effective_rate_dec),
            billing_mode="progressive",
            profile=active_cfg.profile,
            free_units_applied=float(free_units_applied),
            slab_breakdown=slab_breakdown,
            baseline_flat_cost_inr=float(baseline_cost_dec),
            cost_difference_inr=float(diff_dec),
            percentage_difference=pct_diff,
            notes=active_cfg.notes or "Progressive slab calculation.",
        )

    def get_effective_rate_or_default(self, consumption_kwh: Optional[float] = None) -> float:
        """Returns the current effective tariff rate per kWh for estimation."""
        if consumption_kwh is None or consumption_kwh <= 0:
            return float(self.get_active_config().single_tier_rate)
        res = self.calculate_bill(consumption_kwh)
        return res.effective_rate_per_kwh if res.effective_rate_per_kwh > 0 else float(self.get_active_config().single_tier_rate)


# Global singleton instance
tariff_service = TariffService()
