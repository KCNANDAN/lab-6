import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics


# ==============================================================================
# LAB 6: COMPREHENSIVE TEST SUITE (LINE & BRANCH COVERAGE)
# Achieves 100% Line Coverage and 100% Branch Coverage on car_rental_rate.py
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Base / Standard Tests
# ------------------------------------------------------------------------------
def test_single_economy_rental():
    """Initial starter test: standard confirmed economy rental."""
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


# ------------------------------------------------------------------------------
# 2. Input Validation & Error Handling
# ------------------------------------------------------------------------------
def test_invalid_input_parameters():
    """Validates type checks and negative base fees."""
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet("invalid_type", 10.0)
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet(None, 10.0)
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet(100, 10.0)
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet([], -1.0)
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet([], -0.01)


def test_empty_fleet_and_unconfirmed():
    """Tests empty rental batches and unconfirmed rentals."""
    # Empty list
    assert process_rental_fleet([], 0.0) == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}

    # Unconfirmed rentals (explicit and default)
    rentals = [
        {"is_confirmed": False, "days": 3},
        {"days": 2}  # default is_confirmed is False
    ]
    assert process_rental_fleet(rentals, 10.0) == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}


def test_invalid_days_skipping():
    """Tests rentals with zero or negative days."""
    rentals = [
        {"is_confirmed": True, "days": 0},
        {"is_confirmed": True, "days": -5}
    ]
    res = process_rental_fleet(rentals, 20.0)
    assert res["total_revenue"] == 0.0
    assert res["status"] == "EMPTY_BATCH"


# ------------------------------------------------------------------------------
# 3. Vehicle Rates and Driver Age Surcharges
# ------------------------------------------------------------------------------
def test_vehicle_rates_and_age_surcharges():
    """Tests luxury ($120/day), SUV ($70/day), default ($40/day) and age surcharges."""
    # Luxury with underage driver (<25): +$50/day surcharge
    res_lux_young = process_rental_fleet(
        [{"is_confirmed": True, "vehicle_type": "luxury", "driver_age": 24, "days": 2}],
        10.0
    )
    # (120 * 2) + 10 + (50 * 2) = 240 + 10 + 100 = 350.0
    assert res_lux_young["total_revenue"] == 350.0
    assert res_lux_young["status"] == "STANDARD"

    # SUV with underage driver (<25): +$20/day surcharge
    res_suv_young = process_rental_fleet(
        [{"is_confirmed": True, "vehicle_type": "suv", "driver_age": 21, "days": 2}],
        10.0
    )
    # (70 * 2) + 10 + (20 * 2) = 140 + 10 + 40 = 190.0
    assert res_suv_young["total_revenue"] == 190.0

    # Default vehicle type (missing vehicle_type defaults to economy $40/day, age defaults to 25)
    res_default = process_rental_fleet(
        [{"is_confirmed": True, "days": 2}],
        0.0
    )
    assert res_default["total_revenue"] == 80.0

    # Explicit other vehicle type (e.g. compact) with adult driver (>=25)
    res_other = process_rental_fleet(
        [{"is_confirmed": True, "vehicle_type": "compact", "driver_age": 25, "days": 1}],
        0.0
    )
    assert res_other["total_revenue"] == 40.0


# ------------------------------------------------------------------------------
# 4. Mileage Segments & Speeding Penalties
# ------------------------------------------------------------------------------
def test_trip_segments_and_penalties():
    """Tests mileage segments: negative miles, standard miles, >300 miles under 21, >300 adult."""
    rentals = [
        # Segment negative miles (continue) and segment <= 300
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 26,
            "days": 1,
            "trip_segments": [-25, 0, 300]
        },
        # Segment > 300 with driver < 21 (+250 and break)
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 19,
            "days": 1,
            "trip_segments": [350, 100]  # 100 skipped due to break
        },
        # Segment > 300 with adult driver (miles * 0.40)
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 30,
            "days": 1,
            "trip_segments": [400]
        }
    ]
    res = process_rental_fleet(rentals, 0.0)
    # Rental 1: 40*1 + 0 + (0*0.2) + (300*0.2) = 100.0
    # Rental 2: 40*1 + 0 + 250 + (20*1 underage) = 310.0
    # Rental 3: 40*1 + 0 + (400*0.4) = 200.0
    # Total: 610.0
    assert res["total_revenue"] == 610.0
    assert res["status"] == "STANDARD"


# ------------------------------------------------------------------------------
# 5. Risk Flags and Audit Status
# ------------------------------------------------------------------------------
def test_risk_audit_thresholds():
    """Tests risk_flags boundary (==4 is STANDARD, >4 is HIGH_RISK_AUDIT)."""
    # 4 risk flags -> STANDARD
    rentals_4 = [
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "vehicle_type": "economy", "days": 1}
    ]
    assert process_rental_fleet(rentals_4, 10.0)["status"] == "STANDARD"

    # 5 risk flags -> HIGH_RISK_AUDIT
    rentals_5 = [
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "days": -1},
        {"is_confirmed": True, "vehicle_type": "economy", "days": 1}
    ]
    assert process_rental_fleet(rentals_5, 10.0)["status"] == "HIGH_RISK_AUDIT"


# ------------------------------------------------------------------------------
# 6. Fleet Telematics
# ------------------------------------------------------------------------------
def test_fleet_telematics():
    """Tests all telematics scenarios: NO_DATA, SAFE, streak resets, and GROUND_VEHICLE."""
    # NO_DATA
    assert check_fleet_telematics([]) == "NO_DATA"
    assert check_fleet_telematics(None) == "NO_DATA"

    # SAFE
    assert check_fleet_telematics([[]]) == "SAFE"
    assert check_fleet_telematics([[100, 95, 90]]) == "SAFE"
    assert check_fleet_telematics([[110, 80, 115, 85]]) == "SAFE"

    # GROUND_VEHICLE
    assert check_fleet_telematics([[101, 105]]) == "GROUND_VEHICLE"
    assert check_fleet_telematics([[80, 90], [105, 110, 70]]) == "GROUND_VEHICLE"
