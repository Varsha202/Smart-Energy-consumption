import sys
from pathlib import Path
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pydantic import ValidationError
from backend.app.models.schemas import (
    EnergyRecordCreate,
    parse_and_normalize_date
)


class TestValidation(unittest.TestCase):
    def test_date_parsing_variations(self):
        # ISO format
        self.assertEqual(parse_and_normalize_date("2026-07-31"), "2026-07-31")
        # DD.MM.YYYY format
        self.assertEqual(parse_and_normalize_date("31.07.2026"), "2026-07-31")
        # DD-MM-YYYY format
        self.assertEqual(parse_and_normalize_date("15-07-2026"), "2026-07-15")

    def test_invalid_date_format_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_normalize_date("invalid-date-string")

    def test_energy_record_auto_computes_total(self):
        data = {
            "date": "2026-07-01",
            "tneb_campus": 20120.0,
            "tneb_new_stp": 806.0,
            "solar": 3497.0,
            "diesel": 0.0,
            "biogas": 575.0,
            "staff_quarters": 1927.0,
            "academic_blocks": 16384.0,
            "hostels": 769.0,
            "chiller": 4537.0,
            "stp": 1381.0
        }
        record = EnergyRecordCreate(**data)
        expected_total = 1927.0 + 16384.0 + 769.0 + 4537.0 + 1381.0
        self.assertEqual(record.total, expected_total)
        self.assertEqual(record.date, "2026-07-01")

    def test_energy_record_negative_value_rejected(self):
        data = {
            "date": "2026-07-01",
            "tneb_campus": -50.0,  # Negative value
            "tneb_new_stp": 806.0,
            "solar": 3497.0,
            "diesel": 0.0,
            "biogas": 575.0,
            "staff_quarters": 1927.0,
            "academic_blocks": 16384.0,
            "hostels": 769.0,
            "chiller": 4537.0,
            "stp": 1381.0
        }
        with self.assertRaises(ValidationError):
            EnergyRecordCreate(**data)

    def test_energy_record_missing_required_field_rejected(self):
        data = {
            "date": "2026-07-01",
            # missing staff_quarters
            "academic_blocks": 16384.0,
            "hostels": 769.0,
            "chiller": 4537.0,
            "stp": 1381.0
        }
        with self.assertRaises(ValidationError):
            EnergyRecordCreate(**data)


if __name__ == "__main__":
    unittest.main()
