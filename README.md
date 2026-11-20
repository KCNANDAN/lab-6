# Lab 6: Code and Branch Coverage Analysis

## Overview
This repository contains the complete implementation and test deliverables for **Lab 6: Code and Branch Coverage Analysis** on the `car_rental_rate` application.

## Application Under Test
- `car_rental_rate.py`: Evaluates fleet car rentals by vehicle class, driver age, and mileage segments, assesses underage risk surcharges, and monitors fleet telematics for speeding anomalies.

## Deliverables
1. **Code Coverage Test Cases**: `CodeCoverageTest_car_rental_rate.py` (Achieves **100% Statement Coverage**).
2. **Branch Coverage Test Cases**: `BranchCoverageTest_car_rental_rate.py` (Achieves **100% Branch Coverage**, covering all 36 branches).
3. **Comprehensive Test Suite**: `test_car_rental.py` (Full unified suite passing 100% on line and branch coverage).
4. **Terminal Screenshots**:
   - `screenshot_code_coverage.png`: Terminal output for code coverage analysis.
   - `screenshot_branch_coverage.png`: Terminal output for branch coverage analysis.
   - `screenshot_full_coverage.png`: Terminal output for full test suite coverage.
5. **PDF Analysis Report**: `Lab6_Coverage_Analysis_Report.pdf` (Multi-page deliverable report).

## Commands to Run Coverage
```bash
# Run tests and measure statement / line coverage
coverage run -m pytest CodeCoverageTest_car_rental_rate.py
coverage report -m

# Run tests and measure branch coverage
coverage run --branch -m pytest BranchCoverageTest_car_rental_rate.py
coverage report -m

# Run full unified test suite
coverage run --branch -m pytest test_car_rental.py
coverage report -m
```
