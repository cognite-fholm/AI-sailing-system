@phase_01
Feature: Phase 1 — SLA-1 telemetry (scaffold)
  Signal K hub, ADR-0021 sidecars, and Influx persistence contracts.
  Live NMEA ingest scenarios: phase_01_sla1_telemetry_live.feature (@wip).
  See spec §7.1–7.2, §7.4, FR-1–6, ADR-0001, ADR-0011, ADR-0021.

  Background:
    Given the AI Sailing System repository is checked out

  Scenario: ADR-0021 documents SLA-1 Signal K plugin strategy
    Then file "adr/0021-sla1-signalk-plugin-strategy.md" exists
    And adr/README.md lists ADR "0021"

  Scenario: SLA-1 compose wires ADR-0021 services
    Then file "docker-compose.sla-1.yml" contains service "signalk-server"
    And file "docker-compose.sla-1.yml" contains service "course-sk-sync"
    And file "docker-compose.sla-1.yml" contains service "signalk-polar-performance"
    And file "docker-compose.sla-1.yml" contains service "signalk-influx-bridge"
    And file "signalk-server/Dockerfile" exists

  Scenario: Influx bridge persists course geometry and polar performance paths
    Then signalk-influx-bridge maps path "navigation.course.calcValues.vmg"
    And signalk-influx-bridge maps path "navigation.course.calcValues.xte"
    And signalk-influx-bridge maps path "performance.polarSpeed"
    And signalk-influx-bridge maps path "performance.polarSpeedRatio"

  Scenario: course-sk-sync loads resolved waypoints from data repo YAML
    Given the AI-sailing-data repository is available
    When course-sk-sync resolves the active route from config
    Then at least 2 resolved waypoints are available for sync

  Scenario: polar-manager stub interpolates ORC target speeds
    Given the AI-sailing-data repository is available
    When polar-manager loads the active certificate target-speeds file
    Then polar target BSP at TWS 10 and TWA 52 is approximately 7.26 knots
