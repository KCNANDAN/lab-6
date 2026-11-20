import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics


# ==============================================================================
# LAB 6 - STEP 5: CODE COVERAGE TEST SUITE
# Focus: Statement / Line Coverage (Target: >= 90% line coverage)
# Executes all primary execution lines through positive and typical execution paths.
# ==============================================================================

def test_single_economy_rental():
    """Starter test: Single confirmed economy rental."""
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 30,
            "days": 2,
            "trip_segments": [100]
        }
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["total_revenue"] == 110.0
    assert result["status"] == "STANDARD"


def test_invalid_fleet_inputs():
    """Hits input validation lines raising ValueError."""
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet("invalid_type", 10.0)

    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet([], -1.0)


def test_unconfirmed_and_invalid_days_rental():
    """Hits unconfirmed continue and non-positive days lines."""
    rentals = [
        {"is_confirmed": False},
        {"is_confirmed": True, "days": 0}
    ]
    result = process_rental_fleet(rentals, 5.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "EMPTY_BATCH"


def test_luxury_and_suv_pricing_with_young_drivers():
    """Executes luxury and SUV branches along with underage fee calculations."""
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "luxury",
            "driver_age": 22,
            "days": 2,
            "trip_segments": [150]
        },
        {
            "is_confirmed": True,
            "vehicle_type": "suv",
            "driver_age": 23,
            "days": 1,
            "trip_segments": [80]
        }
    ]
    result = process_rental_fleet(rentals, 20.0)
    assert result["status"] == "STANDARD"
    # Luxury: (120*2) + 20 + (150*0.2) + (50*2) = 240 + 20 + 30 + 100 = 390
    # SUV: (70*1) + 20 + (80*0.2) + (20*1) = 70 + 20 + 16 + 20 = 126
    # Total = 516.0
    assert result["total_revenue"] == 516.0


def test_mileage_segments_and_speed_penalties():
    """Hits negative miles continue, >300 under 21 break, and adult >300 miles."""
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 19,
            "days": 1,
            "trip_segments": [-15, 320]
        },
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 35,
            "days": 1,
            "trip_segments": [350]
        }
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["status"] == "STANDARD"


def test_high_risk_fleet_audit():
    """Hits HIGH_RISK_AUDIT return line when risk flags exceed 4."""
    rentals = [
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1}
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["status"] == "HIGH_RISK_AUDIT"


def test_fleet_telematics_scenarios():
    """Hits NO_DATA, GROUND_VEHICLE, and SAFE return lines in telematics."""
    assert check_fleet_telematics([]) == "NO_DATA"
    assert check_fleet_telematics([[120, 115]]) == "GROUND_VEHICLE"
    assert check_fleet_telematics([[90, 85]]) == "SAFE"
