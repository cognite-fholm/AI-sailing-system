@phase_01 @wip
Feature: Phase 1 — SLA-1 telemetry (live)
  On-boat Signal K hub, InfluxDB persistence, and Grafana telemetry dashboards.
  Requires Docker stacks — pass pytest --run-wip.

  Background:
    Given the SLA-1 docker compose stack is deployed
    And Signal K is reachable on the telemetry node

  Scenario: FR-1 NMEA 2000 ingest at 250 kbit/s
    When NMEA 2000 traffic is present on can0
    Then Signal K publishes corresponding deltas within 200 milliseconds

  Scenario: FR-2 NMEA 0183 serial ingest
    When NMEA 0183 sentences arrive on the configured serial port
    Then Signal K normalizes them into the v1 data model

  Scenario: FR-4 InfluxDB write latency
    When telemetry deltas are produced
    Then numeric fields are persisted to InfluxDB signalk bucket within 500 milliseconds p95

  Scenario: FR-6 SLA-1 survives SLA-2 and SLA-3 outage
    Given SLA-2 and SLA-3 stacks are stopped
    When instruments continue sending data
    Then Signal K stream and grafana-telemetry remain available

  Scenario: Grafana telemetry dashboard shows live instruments
    When I open grafana-telemetry on the boat LAN
    Then SOG COG TWS and TWD panels update within 1 second
