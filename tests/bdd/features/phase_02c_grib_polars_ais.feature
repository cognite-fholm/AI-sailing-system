@phase_02c
Feature: Phase 2C — GRIB, polars, AIS (scaffold)
  polar-manager stub and polar interpolation per spec §7.12.
  Full GRIB/AIS scenarios: phase_02c_grib_polars_ais_live.feature (@wip).
  See FR-15–26, ADR-0004, ADR-0021.

  Background:
    Given the AI Sailing System repository is checked out

  Scenario: polar-manager stub is wired in SLA-2 compose
    Then file "docker-compose.sla-2.yml" contains service "polar-manager"
    And file "polar-manager/polar_manager/api.py" exists

  Scenario: polar-manager exposes target speed API
    Then polar-manager api exposes route "/health"
    And polar-manager api exposes route "/polars/{vessel_id}/target"

  Scenario: FR-23 polar-manager interpolates target BSP for any TWS and TWA
    Given the AI-sailing-data repository is available
    When polar-manager loads the active certificate target-speeds file
    Then polar target BSP at TWS 10 and TWA 52 is approximately 7.26 knots
