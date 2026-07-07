@phase_02h
Feature: Phase 2H — Enriched race live sync (ADR-0028)
  Five-minute RaceLiveSnapshot with fleet performance rollups and tactical insights.

  Scenario: FR-238 race-live-sync service and export module exist
    Given the file "race-live-sync/race_live_sync/export.py" exists in the system repo
    And the file "fleet-performance-tracker/fleet_performance_tracker/rollup.py" exists in the system repo
    And the file "live-results/live_results/standings.py" exists in the system repo

  Scenario: FR-241 docker compose includes race-live-sync with influx env
    Given the file "docker-compose.sla-2.yml" exists in the system repo
    Then the file "docker-compose.sla-2.yml" contains "race-live-sync"
    And the file "docker-compose.sla-2.yml" contains "INFLUX_READ_TOKEN"

  Scenario: FR-162 fleet-performance-tracker service in SLA-2 compose
    Given the file "docker-compose.sla-2.yml" exists in the system repo
    Then the file "docker-compose.sla-2.yml" contains "fleet-performance-tracker"
    And the file "fleet-performance-tracker/fleet_performance_tracker/collector.py" exists in the system repo

  Scenario: FR-16 ais-collector service in SLA-2 compose
    Given the file "docker-compose.sla-2.yml" exists in the system repo
    Then the file "docker-compose.sla-2.yml" contains "ais-collector"
    And the file "ais-collector/ais_collector/collector.py" exists in the system repo

  Scenario: FR-221 race-live-sync finalize module exists
    Given the file "race-live-sync/race_live_sync/finalize.py" exists in the system repo
    And the file "race-live-sync/race_live_sync/__main__.py" exists in the system repo

  Scenario: FR-239 data repo documents enriched RaceLiveSnapshot
    Given the AI-sailing-data repository is available
    Then file "docs/RACE_LIVE_SYNC.md" exists in the data repo
    And file "schema/neo4j-mapping.yaml" exists in the data repo
