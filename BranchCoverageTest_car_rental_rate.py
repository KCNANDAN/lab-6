import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics


# ==============================================================================
# LAB 6 - STEP 7 & 8: BRANCH COVERAGE TEST SUITE
# Target: 100% Branch Coverage and 100% Statement Coverage
# Exhaustively tests every decision branch (True/False) and boundary condition.
# ==============================================================================

class TestBranchCoverageProcessRentalFleet:
    """Branch coverage tests for process_rental_fleet function."""

    def test_invalid_rentals_parameter(self):
        """Branch: not isinstance(rentals, list) is True."""
        with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
            process_rental_fleet("not-a-list", 10.0)
        with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
            process_rental_fleet(None, 10.0)
        with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
            process_rental_fleet(12345, 10.0)

    def test_negative_base_admin_fee(self):
        """Branch: base_admin_fee < 0 is True."""
        with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
            process_rental_fleet([], -0.01)
        with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
            process_rental_fleet([], -10.0)

    def test_empty_rentals_list_empty_batch(self):
        """Branch: loop not entered, total_revenue == 0.0 -> EMPTY_BATCH."""
        result = process_rental_fleet([], 0.0)
        assert result == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}

    def test_unconfirmed_rentals_default_and_explicit(self):
        """Branch: rental.get('is_confirmed', False) is False."""
        rentals = [
            {"driver_age": 30, "days": 2},            # default is_confirmed is False
            {"is_confirmed": False, "days": 5}        # explicit False
        ]
        result = process_rental_fleet(rentals, 10.0)
        assert result == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}

    def test_non_positive_days_boundary(self):
        """Branch: days <= 0 is True (days == 0 and days < 0)."""
        rentals = [
            {"is_confirmed": True, "days": 0},   # boundary days == 0
            {"is_confirmed": True, "days": -3}   # days < 0
        ]
        result = process_rental_fleet(rentals, 10.0)
        assert result == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}

    def test_vehicle_types_and_defaults(self):
        """Branches: luxury, suv, and default/other vehicle types."""
        # 1. Luxury vehicle with driver >= 25
        res_lux = process_rental_fleet(
            [{"is_confirmed": True, "vehicle_type": "luxury", "driver_age": 30, "days": 2}],
            0.0
        )
        assert res_lux["total_revenue"] == 240.0  # 120 * 2
        assert res_lux["status"] == "STANDARD"

        # 2. SUV vehicle with driver >= 25
        res_suv = process_rental_fleet(
            [{"is_confirmed": True, "vehicle_type": "suv", "driver_age": 30, "days": 2}],
            0.0
        )
        assert res_suv["total_revenue"] == 140.0  # 70 * 2
        assert res_suv["status"] == "STANDARD"

        # 3. Default vehicle type (missing key -> economy rate 40.0)
        res_def = process_rental_fleet(
            [{"is_confirmed": True, "days": 2}],
            0.0
        )
        assert res_def["total_revenue"] == 80.0  # 40 * 2
        assert res_def["status"] == "STANDARD"

        # 4. Explicit other vehicle type (e.g. sedan -> economy rate 40.0)
        res_other = process_rental_fleet(
            [{"is_confirmed": True, "vehicle_type": "sedan", "driver_age": 30, "days": 1}],
            0.0
        )
        assert res_other["total_revenue"] == 40.0

    def test_underage_driver_surcharges(self):
        """Branches: driver_age < 25 (luxury vs non-luxury) and driver_age >= 25."""
        # Luxury underage (<25): +50.0 * days
        res_lux_young = process_rental_fleet(
            [{"is_confirmed": True, "vehicle_type": "luxury", "driver_age": 24, "days": 2}],
            10.0
        )
        # (120 * 2) + 10 + (50 * 2) = 240 + 10 + 100 = 350.0
        assert res_lux_young["total_revenue"] == 350.0

        # Non-luxury underage (<25): +20.0 * days
        res_suv_young = process_rental_fleet(
            [{"is_confirmed": True, "vehicle_type": "suv", "driver_age": 21, "days": 2}],
            10.0
        )
        # (70 * 2) + 10 + (20 * 2) = 140 + 10 + 40 = 190.0
        assert res_suv_young["total_revenue"] == 190.0

        # Boundary: driver_age == 25 (not < 25, no surcharge)
        res_age_25 = process_rental_fleet(
            [{"is_confirmed": True, "vehicle_type": "luxury", "driver_age": 25, "days": 1}],
            0.0
        )
        assert res_age_25["total_revenue"] == 120.0

    def test_trip_segments_branches(self):
        """Branches: miles < 0, miles <= 300, miles > 300 (age < 21 break vs age >= 21)."""
        # Segment miles < 0: risk_flags += 1, continue
        # Segment miles <= 300 boundary (miles == 300): miles * 0.20
        # Segment miles == 0 boundary
        rentals = [
            {
                "is_confirmed": True,
                "vehicle_type": "economy",
                "driver_age": 25,
                "days": 1,
                "trip_segments": [-50, 0, 300]
            }
        ]
        res = process_rental_fleet(rentals, 0.0)
        # 40*1 + 0 + (0 * 0.20) + (300 * 0.20) = 40 + 60 = 100.0
        assert res["total_revenue"] == 100.0
        assert res["status"] == "STANDARD"

        # Segment miles > 300 with driver_age < 21: +250.0 and BREAK
        rentals_break = [
            {
                "is_confirmed": True,
                "vehicle_type": "economy",
                "driver_age": 20,
                "days": 1,
                "trip_segments": [350, 100]  # 100 must be skipped due to break!
            }
        ]
        # 40*1 + 0 + 250 (break) + 20 (underage) = 310.0
        res_break = process_rental_fleet(rentals_break, 0.0)
        assert res_break["total_revenue"] == 310.0

        # Segment miles > 300 with driver_age >= 21: + miles * 0.40
        rentals_adult_long = [
            {
                "is_confirmed": True,
                "vehicle_type": "economy",
                "driver_age": 21,  # boundary for < 21
                "days": 1,
                "trip_segments": [400]
            }
        ]
        # 40*1 + 0 + (400 * 0.40) + 20 (under 25) = 40 + 160 + 20 = 220.0
        res_adult_long = process_rental_fleet(rentals_adult_long, 0.0)
        assert res_adult_long["total_revenue"] == 220.0

    def test_high_risk_audit_boundary(self):
        """Branch: risk_flags > 4 vs risk_flags == 4."""
        # 1. Exactly 4 risk flags (boundary: 4 > 4 is False -> STANDARD)
        rentals_4_flags = [
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "vehicle_type": "economy", "days": 1}  # valid
        ]
        res_4 = process_rental_fleet(rentals_4_flags, 10.0)
        assert res_4["status"] == "STANDARD"

        # 2. Exactly 5 risk flags (5 > 4 is True -> HIGH_RISK_AUDIT)
        rentals_5_flags = [
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "days": -1},  # +1 risk
            {"is_confirmed": True, "vehicle_type": "economy", "days": 1}
        ]
        res_5 = process_rental_fleet(rentals_5_flags, 10.0)
        assert res_5["status"] == "HIGH_RISK_AUDIT"


class TestBranchCoverageTelematics:
    """Branch coverage tests for check_fleet_telematics function."""

    def test_no_data_conditions(self):
        """Branch: not telematics_matrix is True."""
        assert check_fleet_telematics([]) == "NO_DATA"
        assert check_fleet_telematics(None) == "NO_DATA"

    def test_safe_scenarios_and_speed_resets(self):
        """Branch: speed <= 100 resets speeding_streak."""
        # Matrix with empty vehicle logs
        assert check_fleet_telematics([[]]) == "SAFE"

        # Matrix with boundary speed == 100 (100 is not > 100)
        assert check_fleet_telematics([[100, 100, 95]]) == "SAFE"

        # Streak resets: single speeding event followed by safe speed
        # speed > 100 evaluated True once, but streak reset by <= 100
        matrix_reset = [
            [110, 80, 120, 75, 115, 90],
            [90, 95, 99]
        ]
        assert check_fleet_telematics(matrix_reset) == "SAFE"

    def test_ground_vehicle_consecutive_speeding(self):
        """Branch: speeding_streak >= 2 is True."""
        # Consecutive speeding in first vehicle
        matrix_first = [
            [85, 101, 102, 90]
        ]
        assert check_fleet_telematics(matrix_first) == "GROUND_VEHICLE"

        # Consecutive speeding in subsequent vehicle
        matrix_second = [
            [80, 90, 100],
            [110, 130]
        ]
        assert check_fleet_telematics(matrix_second) == "GROUND_VEHICLE"
